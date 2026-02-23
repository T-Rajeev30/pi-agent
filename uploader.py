import json
import logging
import os
import boto3
from boto3.s3.transfer import TransferConfig
from botocore.exceptions import BotoCoreError, ClientError

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


def upload_file(file_path, mqtt_client, recording_id, retry=False):

    def publish(status, s3_url=None):
        payload = {"status": status, "recordingId": recording_id}
        if s3_url:
            payload["s3Url"] = s3_url

        mqtt_client.publish(
            f"pi/{DEVICE_ID}/film_status",
            json.dumps(payload),
            qos=1
        )

    if not os.path.exists(file_path):
        return True

    file_name = os.path.basename(file_path)

    # ✅ REQUIRED STRUCTURE:
    # bucket/StatCams_Recording/pi-001/file.mp4
    s3_key = f"{S3_ROOT_FOLDER}/{DEVICE_ID}/{file_name}"

    try:
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

        log.info(f"[Uploader] Uploading → {s3_key}")

        s3.upload_file(
            file_path,
            AWS_BUCKET,
            s3_key,
            ExtraArgs={"ContentType": "video/mp4"},
            Config=config
        )

        s3_url = f"https://{AWS_BUCKET}.s3.{AWS_REGION}.amazonaws.com/{s3_key}"

        log.info(f"[Uploader] Uploaded → {s3_url}")

        if DELETE_AFTER_UPLOAD:
            os.remove(file_path)
            log.info("[Uploader] Local file deleted")

        publish("completed", s3_url)
        return True

    except Exception as e:
        log.error(f"[Uploader] Upload failed: {e}")

        if not retry:
            add_to_queue(file_path, recording_id)

        publish("failed")
        return False
Y
