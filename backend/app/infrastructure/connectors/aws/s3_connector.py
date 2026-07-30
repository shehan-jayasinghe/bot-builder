import logging
import os
from typing import BinaryIO

import boto3
from botocore.client import BaseClient
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class S3Connector:
    """Upload and read objects from AWS cloud S3."""

    def __init__(
        self,
        *,
        bucket: str | None = None,
        region: str | None = None,
        endpoint_url: str | None = None,
        access_key_id: str | None = None,
        secret_access_key: str | None = None,
    ) -> None:
        self._bucket = bucket or os.getenv("S3_BUCKET", "bot-builder-kb")
        self._region = region or os.getenv("AWS_REGION", "us-east-1")
        self._endpoint_url = endpoint_url or os.getenv("S3_ENDPOINT_URL")
        self._access_key_id = access_key_id or os.getenv("AWS_ACCESS_KEY_ID")
        self._secret_access_key = secret_access_key or os.getenv("AWS_SECRET_ACCESS_KEY")
        self._client: BaseClient | None = None

    @property
    def bucket(self) -> str:
        return self._bucket

    def _get_client(self) -> BaseClient:
        if self._client is None:
            kwargs: dict = {"region_name": self._region}
            if self._endpoint_url:
                kwargs["endpoint_url"] = self._endpoint_url
            if self._access_key_id and self._secret_access_key:
                kwargs["aws_access_key_id"] = self._access_key_id
                kwargs["aws_secret_access_key"] = self._secret_access_key
            self._client = boto3.client("s3", **kwargs)
        return self._client

    def upload_stream(
        self,
        *,
        key: str,
        stream: BinaryIO,
        content_type: str | None = None,
    ) -> str:
        """Stream a file object to S3. Returns the object key."""
        extra_args = {}
        if content_type:
            extra_args["ContentType"] = content_type

        try:
            self._get_client().upload_fileobj(stream, self._bucket, key, ExtraArgs=extra_args or None)
        except ClientError:
            logger.exception("Failed to upload object to S3: %s", key)
            raise

        logger.info("Uploaded object to s3://%s/%s", self._bucket, key)
        return key

    def download_stream(self, *, key: str, stream: BinaryIO) -> None:
        """Download an S3 object into a writable stream."""
        try:
            self._get_client().download_fileobj(self._bucket, key, stream)
        except ClientError:
            logger.exception("Failed to download object from S3: %s", key)
            raise

    def delete_object(self, *, key: str) -> None:
        try:
            self._get_client().delete_object(Bucket=self._bucket, Key=key)
        except ClientError:
            logger.exception("Failed to delete object from S3: %s", key)
            raise

    def build_uri(self, *, key: str) -> str:
        return f"s3://{self._bucket}/{key}"

    def read_bytes(self, *, key: str) -> bytes:
        try:
            response = self._get_client().get_object(Bucket=self._bucket, Key=key)
            return response["Body"].read()
        except ClientError:
            logger.exception("Failed to read object from S3: %s", key)
            raise

    def ping(self) -> bool:
        try:
            self._get_client().head_bucket(Bucket=self._bucket)
            return True
        except ClientError:
            logger.warning("S3 bucket not reachable: %s", self._bucket)
            return False
