import json
import os
import tempfile
import threading
import time
import logging
from config import UPLOAD_QUEUE_FILE, UPLOAD_RETRY_INTERVAL

log = logging.getLogger(__name__)
_lock = threading.Lock()


def _load_queue():
    if not os.path.exists(UPLOAD_QUEUE_FILE):
        return []
    try:
        with open(UPLOAD_QUEUE_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        log.error(f"[Queue] Failed to load queue file ({e}) — starting fresh")
        return []


def _save_queue(queue):
    """
    ✅ FIX: Atomic write using a temp file + os.replace().
    Previously a direct open()+write could corrupt the queue file if the Pi
    crashed mid-write, silently losing all queued upload entries.
    os.replace() is atomic on Linux — the queue file is never in a partial state.
    """
    dir_ = os.path.dirname(UPLOAD_QUEUE_FILE) or "."
    os.makedirs(dir_, exist_ok=True)
    try:
        with tempfile.NamedTemporaryFile(
            "w", dir=dir_, delete=False, suffix=".tmp"
        ) as tf:
            json.dump(queue, tf)
            tmp_path = tf.name
        os.replace(tmp_path, UPLOAD_QUEUE_FILE)  # atomic on Linux
    except Exception as e:
        log.error(f"[Queue] Failed to save queue: {e}")


def add_to_queue(file_path, recording_id):
    """
    ✅ FIX: Deduplication check added.
    Previously the same file could be queued multiple times (e.g. on MQTT
    reconnect), causing redundant uploads and wasted bandwidth.
    """
    with _lock:
        queue = _load_queue()

        # Deduplicate by file path
        if any(item["file"] == file_path for item in queue):
            log.warning(f"[Queue] Already queued, skipping duplicate: {file_path}")
            return

        queue.append({
            "file":        file_path,
            "recordingId": recording_id,
            "retries":     0,           # ✅ NEW: track attempt count for backoff
        })
        _save_queue(queue)
        log.warning(f"[Queue] Added for retry: {file_path}")


def start_retry_worker(upload_func, mqtt_client):
    def worker():
        while True:
            time.sleep(UPLOAD_RETRY_INTERVAL)
            with _lock:
                queue = _load_queue()
                if not queue:
                    continue

                log.info(f"[Queue] Retrying {len(queue)} file(s)")
                remaining = []
                now = time.time()

                for item in queue:
                    file_path  = item["file"]
                    retries    = item.get("retries", 0)
                    next_retry = item.get("next_retry_at", 0)

                    # ✅ FIX: Skip files whose backoff window hasn't elapsed yet
                    if now < next_retry:
                        remaining.append(item)
                        continue

                    # ✅ FIX: Drop files that no longer exist — avoids clogging
                    # the queue forever with entries for already-deleted files.
                    if not os.path.exists(file_path):
                        log.warning(
                            f"[Queue] File no longer exists, dropping: {file_path}"
                        )
                        continue

                    success = upload_func(
                        file_path, mqtt_client, item["recordingId"], retry=True
                    )

                    if not success:
                        # ✅ FIX: Exponential backoff — doubles wait time each failure,
                        # capped at 1 hour. Avoids hammering S3 when network is down.
                        new_retries = retries + 1
                        backoff_sec = min(
                            UPLOAD_RETRY_INTERVAL * (2 ** new_retries),
                            3600
                        )
                        log.warning(
                            f"[Queue] Retry {new_retries} failed for "
                            f"{os.path.basename(file_path)} — "
                            f"next attempt in {backoff_sec}s"
                        )
                        remaining.append({
                            **item,
                            "retries":      new_retries,
                            "next_retry_at": now + backoff_sec,
                        })

                _save_queue(remaining)

    threading.Thread(target=worker, daemon=True, name="upload-retry-worker").start()
