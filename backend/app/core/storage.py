from functools import lru_cache

import boto3
from botocore.client import BaseClient
from botocore.exceptions import ClientError

from app.core.config import settings
from app.logger import app_logger


@lru_cache(maxsize=1)
def get_s3_client() -> BaseClient:
    return boto3.client(
        "s3",
        endpoint_url=settings.MINIO_ENDPOINT,
        aws_access_key_id=settings.MINIO_ROOT_USER,
        aws_secret_access_key=settings.MINIO_ROOT_PASSWORD,
        region_name=settings.MINIO_REGION,
    )


def ensure_bucket(bucket: str) -> None:
    client = get_s3_client()
    try:
        client.head_bucket(Bucket=bucket)
        return
    except ClientError as err:
        code = err.response.get("Error", {}).get("Code", "")
        if code not in ("404", "NoSuchBucket", "NotFound"):
            raise

    client.create_bucket(Bucket=bucket)
    app_logger.info("Created object storage bucket: %s", bucket)
