import json
import os
import threading
import time
import logging

from config import UPLOAD_QUEUE_FILE, UPLOAD_RETRY_INTERVAL

log = logging.getLogger(__name__)
_lock = threading.Lock()


def _load_queue():
    if not os.path.exists(UPLOAD_QUEUE_FILE):
        return []
    with open(UPLOAD_QUEUE_FILE, "r") as f:
        return json.load(f)


def _save_queue(queue):
    with open(UPLOAD_QUEUE_FILE, "w") as f:
        json.dump(queue, f)


def add_to_queue(file_path, recording_id):
    with _lock:
        queue = _load_queue()
        queue.append({"file": file_path, "recordingId": recording_id})
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

                for item in queue:
                    success = upload_func(
                        item["file"], mqtt_client, item["recordingId"], retry=True
                    )
                    if not success:
                        remaining.append(item)

                _save_queue(remaining)

    threading.Thread(target=worker, daemon=True).start()
