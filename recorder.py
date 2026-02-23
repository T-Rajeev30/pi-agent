import json, logging, os, subprocess, threading
from datetime import datetime
from camera import detect_camera_binary, check_disk_space, build_record_command
from config import VIDEO_DIR, DEVICE_ID
from uploader import upload_file

log = logging.getLogger(__name__)
_cam_proc = _ffmpeg_proc = _current_file = _recording_id = None
_lock = threading.Lock()

def is_recording():
    with _lock:
        return _cam_proc is not None and _cam_proc.poll() is None

def _publish_status(mqtt_client, recording_id, status):
    if mqtt_client and recording_id:
        mqtt_client.publish(f"pi/{DEVICE_ID}/film_status",
                            json.dumps({"status": status, "recordingId": recording_id}), qos=1)

def start_recording(mqtt_client, recording_id):
    global _cam_proc, _ffmpeg_proc, _current_file, _recording_id
    with _lock:
        if _cam_proc is not None and _cam_proc.poll() is None:
            log.warning("[Recorder] Already recording")
            return False
        os.makedirs(VIDEO_DIR, exist_ok=True)
        if not check_disk_space():
            _publish_status(mqtt_client, recording_id, "failed")
            return False
        try:
            binary = detect_camera_binary()
        except RuntimeError as e:
            log.error(str(e))
            _publish_status(mqtt_client, recording_id, "failed")
            return False
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(VIDEO_DIR, f"GM_{DEVICE_ID}_{timestamp}.mp4")
        _current_file = output_path
        _recording_id = recording_id
        cam_cmd, ffmpeg_cmd = build_record_command(binary, output_path)
        try:
            _cam_proc = subprocess.Popen(cam_cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
            _ffmpeg_proc = subprocess.Popen(ffmpeg_cmd, stdin=_cam_proc.stdout,
                                            stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
            _cam_proc.stdout.close()
        except FileNotFoundError as e:
            log.error(f"[Recorder] Binary not found: {e}")
            _publish_status(mqtt_client, recording_id, "failed")
            _cam_proc = _ffmpeg_proc = None
            return False
        log.info(f"[Recorder] Recording -> {output_path}")
        return True

def stop_recording(mqtt_client):
    global _cam_proc, _ffmpeg_proc, _current_file, _recording_id
    with _lock:
        if _cam_proc is None:
            log.warning("[Recorder] No active recording")
            return
        try:
            _cam_proc.terminate()
            _cam_proc.wait(timeout=10)
        except Exception as e:
            log.error(f"[Recorder] Error stopping camera: {e}")
            _cam_proc.kill()
        try:
            _ffmpeg_proc.wait(timeout=30)
        except subprocess.TimeoutExpired:
            _ffmpeg_proc.kill()
        file_to_upload = _current_file
        recording_id_val = _recording_id
        _cam_proc = _ffmpeg_proc = _current_file = _recording_id = None
    if file_to_upload and os.path.exists(file_to_upload):
        threading.Thread(target=upload_file,
                         args=(file_to_upload, mqtt_client, recording_id_val),
                         daemon=True).start()
        log.info("[Recorder] Upload thread started")
    else:
        log.error(f"[Recorder] File missing: {file_to_upload}")
        _publish_status(mqtt_client, recording_id_val, "failed")
