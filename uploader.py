import os
import json
import logging
import boto3
from boto3.s3.transfer import TransferConfig

from config import (
    AWS_ACCESS_KEY,
    AWS_SECRET_KEY,
    AWS_REGION,
    AWS_BUCKET,
    DEVICE_ID,
    DELETE_AFTER_UPLOAD,
    S3_ROOT_FOLDER,
    S3_CHUNK_SIZE
)

from upload_queue import add_to_queue

log = logging.getLogger(__name__)


class ProgressPercentage:

    def __init__(self, filename, logger):
        self._filename = filename
        self._logger = logger
        self._size = float(os.path.getsize(filename))
        self._seen_so_far = 0

    def __call__(self, bytes_amount):

        self._seen_so_far += bytes_amount
        percentage = (self._seen_so_far / self._size) * 100

        mb_done = self._seen_so_far / (1024 * 1024)
        mb_total = self._size / (1024 * 1024)

        self._logger.info(
            f"[Uploader] Upload progress: {percentage:.1f}% "
            f"({mb_done:.2f} MB / {mb_total:.2f} MB)"
        )


def upload_file(file_path, mqtt_client, recording_id):

    def publish(status, s3_url=None):

        payload = {
            "recordingId": recording_id,
            "status": status
        }

        if s3_url:
            payload["s3Url"] = s3_url

        try:
            log.info(f"[Uploader] Publishing status → {status}")

            mqtt_client.publish(
                f"pi/{DEVICE_ID}/film_status",
                json.dumps(payload),
                qos=1
            )

        except Exception as e:
            log.warning(f"[Uploader] MQTT publish failed: {e}")


    if not os.path.exists(file_path):

        log.error("[Uploader] File missing — upload failed")
        publish("failed")
        return False


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


        config = TransferConfig(
            multipart_threshold=S3_CHUNK_SIZE,
            multipart_chunksize=S3_CHUNK_SIZE,
            max_concurrency=1,
            use_threads=False
        )


        progress = ProgressPercentage(file_path, log)

        log.info(f"[Uploader] Upload started → {file_name}")


        s3.upload_file(
            file_path,
            AWS_BUCKET,
            s3_key,
            ExtraArgs={"ContentType": "video/mp4"},
            Config=config,
            Callback=progress
        )


        log.info("[Uploader] Verifying upload on S3")

        s3.head_object(Bucket=AWS_BUCKET, Key=s3_key)


        s3_url = f"https://{AWS_BUCKET}.s3.{AWS_REGION}.amazonaws.com/{s3_key}"

        log.info(f"[Uploader] Upload verified → {s3_url}")


        if DELETE_AFTER_UPLOAD:

            try:
                os.remove(file_path)
                log.info("[Uploader] Local file deleted after verification")

            except Exception as e:
                log.warning(f"[Uploader] File delete failed: {e}")


        publish("completed", s3_url)

        return True


    except Exception as e:

        log.error(f"[Uploader] Upload failed: {e}")

        try:
            add_to_queue(file_path, recording_id)

        except Exception as qe:
            log.error(f"[Uploader] Queue add failed: {qe}")

        publish("failed")

        return False
