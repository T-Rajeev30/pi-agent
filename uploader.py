import json, logging, os
import boto3
from boto3.s3.transfer import TransferConfig
from botocore.exceptions import BotoCoreError, ClientError
from config import AWS_ACCESS_KEY, AWS_BUCKET, AWS_REGION, AWS_SECRET_KEY, DEVICE_ID, S>

log = logging.getLogger(__name__)

def upload_file(file_path, mqtt_client, recording_id):
    def publish(status, s3_url=None):
        payload = {"status": status, "recordingId": recording_id}
        if s3_url:
            payload["s3Url"] = s3_url
        mqtt_client.publish(f"pi/{DEVICE_ID}/film_status", json.dumps(payload), qos=1)
        log.info(f"[Uploader] Status -> {status}")

    publish("uploading")
    if not os.path.exists(file_path):
        log.error(f"[Uploader] File not found: {file_path}")
        publish("failed")
        return

    file_name = os.path.basename(file_path)
    s3_key = S3_PREFIX + file_name
    log.info(f"[Uploader] Uploading {file_path} -> s3://{AWS_BUCKET}/{s3_key}")
    try:
        s3 = boto3.client("s3", region_name=AWS_REGION,
                          aws_access_key_id=AWS_ACCESS_KEY,
                          aws_secret_access_key=AWS_SECRET_KEY)
        config = TransferConfig(multipart_threshold=S3_CHUNK_SIZE,
                                multipart_chunksize=S3_CHUNK_SIZE,
                                max_concurrency=1, use_threads=False)
        s3.upload_file(file_path, AWS_BUCKET, s3_key,
                       ExtraArgs={"ContentType": "video/mp4"}, Config=config)
        s3_url = f"https://{AWS_BUCKET}.s3.{AWS_REGION}.amazonaws.com/{s3_key}"
        os.remove(file_path)
        log.info(f"[Uploader] Done: {s3_url}")
        publish("completed", s3_url=s3_url)
    except (BotoCoreError, ClientError) as e:
        log.error(f"[Uploader] S3 error: {e}")
        publish("failed")
    except Exception as e:
        log.error(f"[Uploader] Error: {e}")
        publish("failed")
