import os
import subprocess
import logging
from pathlib import Path

VIDEO_DIR = Path("/home/pi/videos")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [WATCHDOG] %(levelname)s: %(message)s"
)

def convert_to_mp4(h264_path: Path):
    mp4_path = h264_path.with_suffix(".mp4")

    if mp4_path.exists():
        logging.info(f"MP4 already exists: {mp4_path.name}")
        return mp4_path

    logging.info(f"Converting {h264_path.name} → mp4")

    cmd = [
        "ffmpeg",
        "-y",
        "-fflags", "+genpts",
        "-r", "30",
        "-i", str(h264_path),
        "-c", "copy",
        str(mp4_path)
    ]

    result = subprocess.run(cmd, capture_output=True)

    if result.returncode != 0:
        logging.error(f"FFmpeg failed for {h264_path.name}")
        return None

    logging.info(f"Conversion done: {mp4_path.name}")
    return mp4_path


def upload_file(mp4_path: Path):
    """
    Replace this with your actual uploader call.
    """
    try:
        # call your existing uploader function here
        # example:
        # from uploader import upload
        # upload(mp4_path)

        logging.info(f"Uploading: {mp4_path.name}")
        return True
    except Exception as e:
        logging.error(f"Upload failed: {e}")
        return False


def cleanup_related_files(mp4_path: Path):
    base = mp4_path.stem
    h264 = VIDEO_DIR / f"{base}.h264"
    pts = VIDEO_DIR / f"{base}.pts"

    if h264.exists():
        h264.unlink()
        logging.info(f"Deleted {h264.name}")

    if pts.exists():
        pts.unlink()
        logging.info(f"Deleted {pts.name}")

    mp4_path.unlink()
    logging.info(f"Deleted {mp4_path.name}")


def process_videos():
    for h264_file in VIDEO_DIR.glob("*.h264"):
        base = h264_file.stem
        mp4_file = VIDEO_DIR / f"{base}.mp4"

        # Case 1: MP4 already exists → clean leftovers
        if mp4_file.exists():
            logging.info(f"MP4 found for {base}, cleaning leftovers")
            cleanup_related_files(mp4_file)
            continue

        # Case 2: Need conversion
        mp4_path = convert_to_mp4(h264_file)
        if not mp4_path:
            continue

        # Upload
        success = upload_file(mp4_path)
        if success:
            cleanup_related_files(mp4_path)
        else:
            logging.warning(f"Keeping file for retry: {mp4_path.name}")


if __name__ == "__main__":
    logging.info("Watchdog started")
    process_videos()
    logging.info("Watchdog finished")
