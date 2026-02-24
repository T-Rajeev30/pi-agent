import json
import logging
import os
import subprocess
import threading
import time
from datetime import datetime
from cleanup import cleanup_old_files
from camera import detect_camera_binary, check_disk_space, build_record_command
from config import VIDEO_DIR, DEVICE_ID, CAMERA_FRAMERATE
from uploader import upload_file

log = logging.getLogger(__name__)

_cam_proc = None
_current_file = None
_temp_file = None
_recording_id = None
_recording_start_time = None      # time of Popen() — fallback only
_first_frame_time = None          # time of actual first frame from pts detection
_uploading = False
_lock = threading.Lock()

MIN_RECORD_SECONDS = 3
FIRST_FRAME_TIMEOUT = 30.0


# ─────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────

def is_recording():
    with _lock:
        return _cam_proc is not None and _cam_proc.poll() is None


def get_status():
    with _lock:
        if _cam_proc is not None and _cam_proc.poll() is None:
            return "RECORDING"
        if _uploading:
            return "UPLOADING"
        return "STANDBY"


# ─────────────────────────────────────────────
# Internal helpers
# ─────────────────────────────────────────────

def _is_recording_unsafe():
    return _cam_proc is not None and _cam_proc.poll() is None


def _publish_status(mqtt_client, recording_id, status):
    if mqtt_client and recording_id:
        mqtt_client.publish(
            f"pi/{DEVICE_ID}/film_status",
            json.dumps({"status": status, "recordingId": recording_id}),
            qos=1,
        )


def _wait_for_first_frame(pts_file, popen_time):
    """
    Poll the .pts file until at least one data line appears.
    rpicam-vid creates the file immediately but buffers writes for ~15s.
    """
    global _first_frame_time

    t0 = time.time()
    while time.time() - t0 < FIRST_FRAME_TIMEOUT:
        try:
            if os.path.exists(pts_file):
                with open(pts_file, "r") as f:
                    for line in f:
                        stripped = line.strip()
                        if stripped and not stripped.startswith("#"):
                            first_frame_time = time.time()
                            init_overhead = first_frame_time - popen_time
                            log.info(
                                f"[Recorder] ✅ First frame detected — "
                                f"camera init overhead: {init_overhead:.3f}s"
                            )
                            with _lock:
                                _first_frame_time = first_frame_time
                            return
        except OSError:
            pass
        time.sleep(0.1)

    log.warning(
        f"[Recorder] ⚠️ First frame not detected within {FIRST_FRAME_TIMEOUT}s"
    )


def _build_ffmpeg_cmd(temp_file, pts_file, current_file):
    """
    Build the ffmpeg command that correctly preserves real timestamps.

    Strategy:
    - If pts file exists and has valid data → use it to assign real timestamps.
      This preserves gaps caused by frame drops, so the output duration
      reflects actual wall-clock time, not just frame count.
    - If pts file is missing/bad → fall back to forcing 60fps timestamps
      (fast but compresses any dropped-frame gaps into shorter duration).
    """
    pts_valid = False
    if os.path.exists(pts_file) and os.path.getsize(pts_file) > 0:
        try:
            with open(pts_file, "r") as f:
                lines = [
                    l.strip() for l in f
                    if l.strip() and not l.startswith("#")
                ]
            if len(lines) >= 2:
                first_ts = float(lines[0])
                last_ts  = float(lines[-1])
                # Sanity check: avg interval should be close to 1000/60 = 16.67ms
                avg_ms = (last_ts - first_ts) / max(len(lines) - 1, 1)
                if 5.0 < avg_ms < 100.0:   # valid ms range for 10–200fps
                    pts_valid = True
                    log.info(
                        f"[Recorder] pts valid — avg frame interval: {avg_ms:.2f}ms "
                        f"({1000/avg_ms:.1f}fps effective)"
                    )
                else:
                    log.warning(
                        f"[Recorder] pts avg interval {avg_ms:.2f}ms is implausible "
                        f"— ignoring pts for timestamp assignment"
                    )
        except Exception as e:
            log.warning(f"[Recorder] pts read error: {e}")

    if pts_valid:
        # Use pts timestamps → dropped frame gaps are preserved in output duration
        # Output duration ≈ actual wall-clock recording time
        log.info("[Recorder] Using pts file for real-time timestamp assignment")
        return [
            "ffmpeg",
            "-loglevel",  "warning",
            "-r",         str(CAMERA_FRAMERATE),   # input framerate hint
            "-i",         temp_file,
            "-c:v",       "copy",
            "-video_track_timescale", "90000",
            "-movflags",  "+faststart",
            current_file,
        ]
    else:
        # No valid pts → assign timestamps sequentially at CAMERA_FRAMERATE
        # Output duration = frame_count / fps (shorter than wall-clock if frames dropped)
        log.warning(
            "[Recorder] No valid pts — timestamps assigned sequentially at "
            f"{CAMERA_FRAMERATE}fps (dropped frames will compress duration)"
        )
        return [
            "ffmpeg",
            "-loglevel",  "warning",
            "-fflags",    "+genpts",
            "-r",         str(CAMERA_FRAMERATE),
            "-i",         temp_file,
            "-c:v",       "copy",
            "-video_track_timescale", "90000",
            "-movflags",  "+faststart",
            current_file,
        ]


def _get_duration_from_mp4(file_path, fallback):
    """Use ffprobe to read actual MP4 duration. Falls back on error."""
    try:
        result = subprocess.run(
            [
                "ffprobe", "-v", "error",
                "-select_streams", "v:0",
                "-show_entries", "stream=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                file_path,
            ],
            capture_output=True, text=True, timeout=15,
        )
        output = result.stdout.strip()

        if not output or output == "N/A":
            result2 = subprocess.run(
                [
                    "ffprobe", "-v", "error",
                    "-show_entries", "format=duration",
                    "-of", "default=noprint_wrappers=1:nokey=1",
                    file_path,
                ],
                capture_output=True, text=True, timeout=15,
            )
            output = result2.stdout.strip()

        if output and output != "N/A":
            duration = float(output)
            log.info(f"[Recorder] ✅ ffprobe duration: {duration:.3f}s → {int(duration)}s")
            return int(duration)

        log.warning(f"[Recorder] ffprobe no result — using fallback: {fallback}s")
        return fallback

    except Exception as e:
        log.warning(f"[Recorder] ffprobe failed ({e}) — using fallback: {fallback}s")
        return fallback


# ─────────────────────────────────────────────
# Recording control
# ─────────────────────────────────────────────

def start_recording(mqtt_client, recording_id):
    global _cam_proc, _current_file, _temp_file, _recording_id
    global _recording_start_time, _first_frame_time

    with _lock:
        if _is_recording_unsafe():
            log.warning("[Recorder] Already recording — ignoring start_recording()")
            return False

        os.makedirs(VIDEO_DIR, exist_ok=True)
        cleanup_old_files()

        if not check_disk_space():
            _publish_status(mqtt_client, recording_id, "failed")
            return False

        try:
            binary = detect_camera_binary()
        except RuntimeError as e:
            log.error(f"[Recorder] {e}")
            _publish_status(mqtt_client, recording_id, "failed")
            return False

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        _current_file = os.path.join(VIDEO_DIR, f"GM_{DEVICE_ID}_{timestamp}.mp4")
        _temp_file    = _current_file.replace(".mp4", ".h264")
        _recording_id = recording_id
        _first_frame_time = None

        cam_cmd = build_record_command(binary, _temp_file)
        log.info(f"[Recorder] Running command: {' '.join(cam_cmd)}")

        try:
            _cam_proc = subprocess.Popen(cam_cmd)
            _recording_start_time = time.time()
            log.info(
                f"[Recorder] Popen() at {_recording_start_time:.3f} — "
                f"waiting for first frame..."
            )
        except Exception as e:
            log.error(f"[Recorder] Failed to start camera process: {e}")
            _publish_status(mqtt_client, recording_id, "failed")
            return False

        pts_file   = _temp_file.replace(".h264", ".pts")
        popen_time = _recording_start_time
        threading.Thread(
            target=_wait_for_first_frame,
            args=(pts_file, popen_time),
            daemon=True,
            name="first-frame-detector",
        ).start()

        log.info(f"[Recorder] Recording → {_current_file}")
        _publish_status(mqtt_client, recording_id, "recording")
        return True


def stop_recording(mqtt_client):
    global _cam_proc, _current_file, _temp_file, _recording_id
    global _recording_start_time, _first_frame_time, _uploading

    with _lock:
        if _cam_proc is None:
            log.warning("[Recorder] stop_recording() called but nothing is recording")
            return

        start_ref = _first_frame_time or _recording_start_time or time.time()
        ref_label = "first-frame" if _first_frame_time else "Popen"
        elapsed   = time.time() - start_ref

        if elapsed < MIN_RECORD_SECONDS:
            wait = MIN_RECORD_SECONDS - elapsed
            log.warning(
                f"[Recorder] Too short ({elapsed:.1f}s), "
                f"waiting {wait:.1f}s..."
            )
            time.sleep(wait)

        proc         = _cam_proc
        current_file = _current_file
        temp_file    = _temp_file
        recording_id = _recording_id
        wallclock_duration = int(time.time() - start_ref)

        log.info(
            f"[Recorder] Stopping — "
            f"wall-clock from {ref_label}: {wallclock_duration}s"
        )

        _publish_status(mqtt_client, recording_id, "processing")
        proc.terminate()
        proc.wait()

        _cam_proc             = None
        _current_file         = None
        _temp_file            = None
        _recording_id         = None
        _recording_start_time = None
        _first_frame_time     = None

    # ── Post-stop processing ──────────────────────────────────────────────────
    time.sleep(1)

    if not os.path.exists(temp_file) or os.path.getsize(temp_file) == 0:
        log.error(f"[Recorder] h264 file missing or empty: {temp_file}")
        _publish_status(mqtt_client, recording_id, "failed")
        return

    pts_file = temp_file.replace(".h264", ".pts")

    # Build ffmpeg command — uses pts if valid, otherwise sequential timestamps
    ffmpeg_cmd = _build_ffmpeg_cmd(temp_file, pts_file, current_file)

    log.info("[Recorder] Running ffmpeg...")
    result = subprocess.run(ffmpeg_cmd)

    if result.returncode != 0:
        log.error(f"[Recorder] ffmpeg failed for {temp_file}")
        _publish_status(mqtt_client, recording_id, "failed")
        return

    # Cleanup temp files
    for f in [temp_file, pts_file]:
        if os.path.exists(f):
            os.remove(f)
            log.info(f"[Recorder] Removed temp file: {os.path.basename(f)}")

    if not os.path.exists(current_file) or os.path.getsize(current_file) == 0:
        log.error(f"[Recorder] Output file missing or empty: {current_file}")
        _publish_status(mqtt_client, recording_id, "failed")
        return

    # ffprobe gives us the true duration of the output file
    duration_sec = _get_duration_from_mp4(current_file, fallback=wallclock_duration)

    # Log frame drop analysis
    if wallclock_duration > 0:
        capture_pct = (duration_sec / wallclock_duration) * 100
        if capture_pct < 90:
            log.warning(
                f"[Recorder] ⚠️ Frame drop detected — captured {duration_sec}s "
                f"of {wallclock_duration}s wall-clock ({capture_pct:.1f}% efficiency)"
            )
        else:
            log.info(
                f"[Recorder] ✅ Capture efficiency: {capture_pct:.1f}% "
                f"({duration_sec}s of {wallclock_duration}s)"
            )

    size_mb = os.path.getsize(current_file) // (1024 * 1024)
    log.info(
        f"[Recorder] Conversion done — "
        f"{duration_sec}s recorded / {size_mb} MB, uploading..."
    )

    # ── Upload ────────────────────────────────────────────────────────────────
    with _lock:
        _uploading = True

    def _upload_and_clear():
        global _uploading
        try:
            upload_file(current_file, mqtt_client, recording_id)
        finally:
            with _lock:
                _uploading = False

    threading.Thread(target=_upload_and_clear, daemon=True).start()












