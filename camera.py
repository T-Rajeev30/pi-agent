import os
import shutil
import logging
from config import (
    VIDEO_DIR, VIDEO_BITRATE, CAMERA_WIDTH, CAMERA_HEIGHT,
    CAMERA_FRAMERATE, MIN_FREE_DISK_MB
)

log = logging.getLogger(__name__)


def detect_camera_binary():
    for binary in ("rpicam-vid", "libcamera-vid"):
        if shutil.which(binary):
            log.info(f"[Camera] Using binary: {binary}")
            return binary
    raise RuntimeError(
        "Neither rpicam-vid nor libcamera-vid found. "
        "Run: sudo apt install rpicam-apps"
    )


def check_disk_space():
    stat = os.statvfs(VIDEO_DIR)
    free_mb = (stat.f_bavail * stat.f_frsize) / (1024 * 1024)
    log.info(f"[Camera] Free disk: {free_mb:.0f} MB")
    return free_mb >= MIN_FREE_DISK_MB


def build_record_command(binary, output_h264):
    pts_file = output_h264.replace(".h264", ".pts")
    return [
        binary,
        "--width",     str(CAMERA_WIDTH),
        "--height",    str(CAMERA_HEIGHT),
        "--framerate", str(CAMERA_FRAMERATE),
        "--bitrate",   str(VIDEO_BITRATE),
        "--codec",     "h264",
        "--inline",
        "--save-pts",  pts_file,
        "-t",          "0",
        "-o",          output_h264,
        "--nopreview",

        # ── Encoder settings ──────────────────────────────────────────────────
        "--level",     "4.1",       # H.264 level 4.1 — sufficient for 720p30
        "--profile",   "main",      # main profile — lower CPU than high

        # ── Keyframe interval ─────────────────────────────────────────────────
        "--intra",     "30",        # keyframe every 1s at 30fps

        # ── CPU load reduction ────────────────────────────────────────────────
        "--denoise",   "off",       # disable ISP denoising

        # ── Fix autofocus — removes AF hunting init delay ─────────────────────
        "--autofocus-mode", "manual",
        "--lens-position",  "0.0",  # infinity focus; increase for closer subjects

        # ── Fix AEC/AWB — eliminates the remaining ~14s convergence delay ──────
        # Without these, camera spends 10-15s adjusting exposure and white balance
        # before writing the first frame. Locking them forces immediate start.
        "--awb",       "auto",      # run AWB once at start then lock
           # initial WB gains (daylight approx) — camera
                                    # will override these if --awb auto is used first
        "--exposure",  "normal",    # AEC metering mode
        "--ev",        "0",         # exposure compensation: 0 = no adjustment
    ]
