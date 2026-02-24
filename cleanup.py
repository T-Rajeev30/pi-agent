import os
from config import VIDEO_DIR, MIN_FREE_DISK_MB

def get_free_mb():
    stat = os.statvfs(VIDEO_DIR)
    return (stat.f_bavail * stat.f_frsize) / (1024 * 1024)

def cleanup_old_files():
    if not os.path.exists(VIDEO_DIR):
        return

    files = sorted(
        [os.path.join(VIDEO_DIR, f) for f in os.listdir(VIDEO_DIR)],
        key=os.path.getmtime
    )

    while files and get_free_mb() < MIN_FREE_DISK_MB:
        oldest = files.pop(0)
        try:
            os.remove(oldest)
            print(f"[Cleanup] Removed {oldest}")
        except Exception as e:
            print(f"[Cleanup] Failed removing {oldest}: {e}")

