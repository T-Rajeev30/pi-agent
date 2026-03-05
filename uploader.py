import os
import json
import time
import logging
import boto3
from boto3.s3.transfer import TransferConfig

from config import (
    AWS_ACCESS_KEY,
    AWS_BUCKET,
    AWS_REGION,
    AWS_SECRET_KEY,
    DEVICE_ID,
    S3_ROOT_FOLDER,
    S3_CHUNK_SIZE,
    DELETE_AFTER_UPLOAD,
)

from upload_queue import add_to_queue

log = logging.getLogger(__name__)


# --------------------------------------------------
# Upload Progress Logger
# --------------------------------------------------

class ProgressPercentage:

    def __init__(self, filename, logger):

        self._filename = filename
        self._size = float(os.path.getsize(filename))
        self._seen_so_far = 0
        self._logger = logger
        self._last_logged = 0

    def __call__(self, bytes_amount):

        self._seen_so_far += bytes_amount
        percentage = (self._seen_so_far / self._size) * 100

        if int(percentage) >= self._last_logged + 10:

            self._last_logged = int(percentage)

            self._logger.info(
                f"[Uploader] Upload progress: {percentage:.1f}% "
                f"({self._seen_so_far/1024/1024:.2f} MB / "
                f"{self._size/1024/1024:.2f} MB)"
            )


# --------------------------------------------------
# Upload Function
# --------------------------------------------------

def upload_file(file_path, mqtt_client, recording_id):

    def publish(status, s3_url=None):

        payload = {
            "recordingId": recording_id,
            "status": status,
        }

        if s3_url:
            payload["s3Url"] = s3_url

        try:

            mqtt_client.publish(
                f"pi/{DEVICE_ID}/film_status",
                json.dumps(payload),
                qos=1
            )

        except Exception as e:

            log.warning(f"[Uploader] MQTT publish failed: {e}")


    # -------- File existence check --------

    if not os.path.exists(file_path):

        log.warning("[Uploader] File missing, skipping upload")

        return True


    file_name = os.path.basename(file_path)
    s3_key = f"{S3_ROOT_FOLDER}/{DEVICE_ID}/{file_name}"


    try:

        publish("uploading")

        s3 = boto3.client(
            "s3",
            region_name=AWS_REGION,
            aws_access_key_id=AWS_ACCESS_KEY,
            aws_secret_access_key=AWS_SECRET_KEY
        )


        # -------- Static multipart config --------

        chunk_size = S3_CHUNK_SIZE

        config = TransferConfig(
            multipart_threshold=S3_CHUNK_SIZE,
            multipart_chunksize=chunk_size,
            max_concurrency=1,
            use_threads=False
        )


        size_mb = os.path.getsize(file_path) / (1024 * 1024)

        log.info(f"[Uploader] Upload started — size: {size_mb:.2f} MB")


        progress = ProgressPercentage(file_path, log)


        # -------- Retry Logic --------

        max_retries = 5

        for attempt in range(1, max_retries + 1):

            try:

                s3.upload_file(
                    file_path,
                    AWS_BUCKET,
                    s3_key,
                    ExtraArgs={"ContentType": "video/mp4"},
                    Config=config,
                    Callback=progress
                )

                break

            except Exception as e:

                wait_time = 2 ** attempt

                log.warning(
                    f"[Uploader] Upload failed "
                    f"(attempt {attempt}/{max_retries}). "
                    f"Retrying in {wait_time}s..."
                )

                time.sleep(wait_time)

                if attempt == max_retries:

                    raise e


        # -------- Success --------

        s3_url = f"https://{AWS_BUCKET}.s3.{AWS_REGION}.amazonaws.com/{s3_key}"

        log.info(f"[Uploader] Uploaded → {s3_url}")


        if DELETE_AFTER_UPLOAD:

            try:

                os.remove(file_path)

                log.info("[Uploader] Local file deleted")

            except Exception as e:

                log.warning(f"[Uploader] File delete failed: {e}")


        publish("completed", s3_url)

        return True


    except Exception as e:

        log.error(f"[Uploader] Upload failed: {e}")


        # -------- Queue retry protection --------

        if not os.path.exists(file_path):

            log.warning("[Uploader] File disappeared before queue")

            publish("failed")

            return False


        try:

            add_to_queue(file_path, recording_id)

        except Exception as qe:

            log.error(f"[Uploader] Queue add failed: {qe}")


        publish("failed")

        return False
