import os
import time
import json
import logging
import threading
import subprocess
from datetime import datetime

from camera import detect_camera_binary, check_disk_space, build_record_command
from cleanup import cleanup_old_files
from uploader import upload_file
from config import VIDEO_DIR, DEVICE_ID, CAMERA_FRAMERATE
from state_store import save_state, clear_state

log = logging.getLogger(__name__)


# =========================================================
# Camera Service
# =========================================================

class CameraService:

    def __init__(self):
        self._proc = None
        self._lock = threading.Lock()
        self._start_time = None

    def start(self, output_file):

        with self._lock:

            if self.is_running():
                log.warning("[CameraService] Camera already running")
                return False

            binary = detect_camera_binary()
            cmd = build_record_command(binary, output_file)

            try:
                self._proc = subprocess.Popen(cmd)
                self._start_time = time.time()

                log.info("[CameraService] Camera process started")
                return True

            except Exception as e:
                log.error(f"[CameraService] Failed to start camera: {e}")
                return False

    def stop(self):

        with self._lock:

            if not self._proc:
                return

            log.info("[CameraService] Stopping camera")

            self._proc.terminate()

            try:
                self._proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                log.warning("[CameraService] Force killing camera")
                self._proc.kill()

            self._proc = None

    def is_running(self):
        return self._proc and self._proc.poll() is None

    def start_time(self):
        return self._start_time


# =========================================================
# Mux Service
# =========================================================

class MuxService:

    def convert(self, h264_file, mp4_file):

        cmd = [
            "ffmpeg",
            "-fflags", "+genpts",
            "-r", str(CAMERA_FRAMERATE),
            "-i", h264_file,
            "-c:v", "copy",
            "-movflags", "+faststart",
            mp4_file
        ]

        log.info("[MuxService] Converting to mp4")

        result = subprocess.run(cmd)

        if result.returncode != 0:
            log.error("[MuxService] FFmpeg conversion failed")
            return False

        log.info("[MuxService] Conversion complete")

        return True


# =========================================================
# Recording Manager
# =========================================================

class RecordingManager:

    def __init__(self):

        self.camera = CameraService()
        self.mux = MuxService()

        self._recording_id = None
        self._temp_file = None
        self._final_file = None
        self._duration = None

        self._lock = threading.Lock()

    def is_recording(self):
        return self.camera.is_running()

    def get_status(self):
        return "RECORDING" if self.is_recording() else "STANDBY"

    def start(self, mqtt_client, recording_id, duration=3600):

        with self._lock:

            if self.is_recording():
                log.warning("[RecordingManager] Already recording")
                return False

            os.makedirs(VIDEO_DIR, exist_ok=True)

            cleanup_old_files()

            if not check_disk_space():
                log.error("[RecordingManager] Low disk space")
                self._publish_status(mqtt_client, recording_id, "failed")
                return False

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base = f"GM_{DEVICE_ID}_{recording_id}_{timestamp}"

            self._temp_file = os.path.join(VIDEO_DIR, base + ".h264")
            self._final_file = os.path.join(VIDEO_DIR, base + ".mp4")

            self._recording_id = recording_id
            self._duration = duration

            if not self.camera.start(self._temp_file):
                self._publish_status(mqtt_client, recording_id, "failed")
                return False

            log.info(f"[RecordingManager] Recording started → {self._temp_file}")

            self._publish_status(mqtt_client, recording_id, "recording")

            # auto stop thread
            threading.Thread(
                target=self._auto_stop,
                args=(mqtt_client,),
                daemon=True
            ).start()

            return True

    def _auto_stop(self, mqtt_client):

        time.sleep(self._duration)

        if self.is_recording():
            log.info("[RecordingManager] Auto stop triggered")
            self.stop(mqtt_client, manual_stop=False)

    def stop(self, mqtt_client, manual_stop=False):

        with self._lock:

            if not self.is_recording():
                log.warning("[RecordingManager] Stop called but not recording")
                return

            recording_id = self._recording_id
            temp_file = self._temp_file
            final_file = self._final_file

        self.camera.stop()

        wallclock = int(time.time() - self.camera.start_time())
        log.info(f"[RecordingManager] Duration: {wallclock}s")

        if manual_stop:
            self._publish_status(mqtt_client, recording_id, "stopped")
        else:
            self._publish_status(mqtt_client, recording_id, "processing")

        threading.Thread(
            target=self._post_process,
            args=(mqtt_client, recording_id, temp_file, final_file, manual_stop),
            daemon=True
        ).start()

    def _post_process(self, mqtt_client, recording_id, temp_file, final_file, manual_stop=False):

        if not os.path.exists(temp_file) or os.path.getsize(temp_file) == 0:
            log.error("[RecordingManager] Recording file missing")
            self._publish_status(mqtt_client, recording_id, "failed")
            return

        if manual_stop:
    	    log.info("[RecordingManager] Manual stop — processing file")
        success = self.mux.convert(temp_file, final_file)

        if not success:
            self._publish_status(mqtt_client, recording_id, "failed")
            return

        os.remove(temp_file)

        pts_file = temp_file.replace(".h264", ".pts")

        if os.path.exists(pts_file):
            os.remove(pts_file)

        log.info("[RecordingManager] Uploading file")

        save_state({
            "recordingId": recording_id,
            "finalFile": final_file
        })

        try:

            success = upload_file(final_file, mqtt_client, recording_id)

            if success:
                clear_state()

            else:
                log.error("[RecordingManager] Upload failed — state preserved")

        except Exception as e:
            log.error(f"[RecordingManager] Upload crashed: {e}")

    def _publish_status(self, mqtt_client, recording_id, status):

        if not mqtt_client or not recording_id:
            return

        mqtt_client.publish(
            f"pi/{DEVICE_ID}/film_status",
            json.dumps({
                "status": status,
                "recordingId": recording_id
            }),
            qos=1
        )

    def get_remaining_time(self):

        if not self.is_recording():
            return 0

        elapsed = int(time.time() - self.camera.start_time())

        return max(0, self._duration - elapsed)


# Singleton instance
_manager = RecordingManager()


def start_recording(mqtt_client, recording_id, duration=3600):
    return _manager.start(mqtt_client, recording_id, duration)


def stop_recording(mqtt_client, manual_stop=True):
    _manager.stop(mqtt_client, manual_stop)


def is_recording():
    return _manager.is_recording()


def get_status():
    return _manager.get_status()


def get_remaining_time():
    return _manager.get_remaining_time()
