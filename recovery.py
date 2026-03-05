import os
import subprocess
import logging
from pathlib import Path

from uploader import upload_file
from config import VIDEO_DIR
from state_store import load_state, clear_state
from recorder import is_recording

log = logging.getLogger(__name__)

VIDEO_PATH = Path(VIDEO_DIR)


# --------------------------------------------------
# Helpers
# --------------------------------------------------
def extract_recording_id(file_path):
    name = file_path.stem
    parts = name.split("_")

    # GM_DEVICEID_RECORDINGID_TIMESTAMP
    if len(parts) >= 4:
        return parts[2]

    return name

def convert_to_mp4(h264_path: Path) -> Path | None:

    mp4_path = h264_path.with_suffix(".mp4")

    if mp4_path.exists():
        return mp4_path

    log.info(f"[Recovery] Converting {h264_path.name} → mp4")

    cmd = [
        "ffmpeg",
        "-y",
        "-fflags", "+genpts",
        "-r", "30",
        "-i", str(h264_path),
        "-c", "copy",
        str(mp4_path),
    ]

    result = subprocess.run(cmd, capture_output=True)

    if result.returncode != 0:
        log.error(f"[Recovery] FFmpeg failed for {h264_path.name}")
        return None

    return mp4_path


def cleanup_related_files(mp4_path: Path):

    base = mp4_path.stem

    h264 = VIDEO_PATH / f"{base}.h264"
    pts = VIDEO_PATH / f"{base}.pts"

    if h264.exists():
        h264.unlink()
        log.info(f"[Recovery] Deleted {h264.name}")

    if pts.exists():
        pts.unlink()
        log.info(f"[Recovery] Deleted {pts.name}")

    if mp4_path.exists():
        mp4_path.unlink()
        log.info(f"[Recovery] Deleted {mp4_path.name}")


# --------------------------------------------------
# Main Recovery
# --------------------------------------------------

def recover_pending_files(mqtt_client=None):

    log.info("[Recovery] Checking for crashed recording state...")

    # 1️⃣ Recover crashed active recording
    state = load_state()

    if state:

        final_file = state.get("finalFile")
        recording_id = state.get("recordingId")

        if final_file and os.path.exists(final_file):

            log.info("[Recovery] Re-uploading crashed file")

            success = upload_file(final_file, mqtt_client, recording_id)

            if success:
                try:
                    os.remove(final_file)
                except Exception:
                    pass

        else:

            log.warning("[Recovery] State exists but file missing")
            clear_state()

    else:

        log.info("[Recovery] No active state found")


    # 2️⃣ Scan filesystem for orphan files
    log.info("[Recovery] Scanning video directory...")


    # If currently recording, do not touch files
    if is_recording():

        log.info("[Recovery] Recording active — skipping filesystem recovery")
        return


    for file in VIDEO_PATH.iterdir():

        # 🔴 Skip broken partial files
        if file.stat().st_size == 0:
            continue


        # Handle orphan MP4
        if file.suffix == ".mp4":

            log.info(f"[Recovery] Found orphan mp4: {file.name}")

            recording_id = extract_recording_id(file)

            success = upload_file(str(file), mqtt_client, recording_id)

            if success:
                cleanup_related_files(file)


        # Handle orphan H264
        elif file.suffix == ".h264":

            log.info(f"[Recovery] Found raw file: {file.name}")

            mp4_path = convert_to_mp4(file)

            if not mp4_path:
                continue

            recording_id = extract_recording_id(mp4_path)

            success = upload_file(str(mp4_path), mqtt_client, recording_id)

            if success:
                cleanup_related_files(mp4_path)
