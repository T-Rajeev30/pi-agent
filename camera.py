import os
import shutil
import subprocess
import logging
from config import VIDEO_DIR, CAMERA_WIDTH, CAMERA_HEIGHT, CAMERA_FRAMERATE, MIN_FREE_DISK_MB

log = logging.getLogger(__name__)

def detect_camera_binary():
    for binary in ("rpicam-vid", "libcamera-vid"):
        if shutil.which(binary):
            log.info(f"[Camera] Using binary: {binary}")
            return binary
    raise RuntimeError("Neither rpicam-vid nor libcamera-vid found. Run: sudo apt install rpicam-apps")

def check_disk_space():
    stat = os.statvfs(VIDEO_DIR)
    free_mb = (stat.f_bavail * stat.f_frsize) / (1024 * 1024)
    log.info(f"[Camera] Free disk: {free_mb:.0f} MB")
    if free_mb < MIN_FREE_DISK_MB:
        log.error(f"[Camera] Insufficient disk space: {free_mb:.0f} MB free")
        return False
    return True

def build_record_command(binary, output_path):
    cam_cmd = [binary, "--width", str(CAMERA_WIDTH), "--height", str(CAMERA_HEIGHT),
               "--framerate", str(CAMERA_FRAMERATE), "--codec", "h264",
               "-t", "0", "-o", "-", "--nopreview"]
    ffmpeg_cmd = ["ffmpeg", "-y", "-fflags", "+genpts", "-i", "pipe:0",
                  "-c:v", "copy", "-movflags", "+faststart", output_path]
    return cam_cmd, ffmpeg_cmd

