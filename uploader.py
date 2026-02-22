import boto3
import os
from config import AWS_ACCESS_KEY, AWS_SECRET_KEY, AWS_REGION, AWS_BUCKET, S3_PREFIX

s3 = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name=AWS_REGION
)

def upload_large(file_path):
    filename = os.path.basename(file_path)
    key = S3_PREFIX + filename

    print("Uploading:", key)

    config = boto3.s3.transfer.TransferConfig(
        multipart_threshold=64*1024*1024,
        multipart_chunksize=64*1024*1024,
        max_concurrency=4,
        use_threads=True
    )

    s3.upload_file(
        file_path,
        AWS_BUCKET,
        key,
        ExtraArgs={"ContentType": "video/mp4"},
        Config=config
    )

    url = f"https://{AWS_BUCKET}.s3.{AWS_REGION}.amazonaws.com/{key}"
    print("Uploaded:", url)
    return url
