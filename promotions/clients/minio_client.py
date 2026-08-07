import json
import io
import logging
from typing import Optional
from minio import Minio
from minio.error import S3Error
import urllib3
from django.conf import settings
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger(__name__)


class MinioClient:
    def __init__(self):
        # minio client expects endpoint without scheme
        endpoint = settings.MINIO_ENDPOINT
        if "://" in endpoint:
            endpoint = endpoint.split("://", 1)[1]
        self.client = Minio(
            endpoint,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE,
        )
        self.bucket = settings.MINIO_BUCKET

    @retry(
        stop=stop_after_attempt(settings.DEFAULT_MAX_RETRIES),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((S3Error, urllib3.exceptions.HTTPError))
    )
    def upload_object(self, key: str, data: dict):
        """Upload object to MinIO bucket."""
        json_data = json.dumps(data).encode('utf-8')
        data_stream = io.BytesIO(json_data)

        self.client.put_object(
            bucket_name=self.bucket,
            object_name=key,
            data=data_stream,
            length=len(json_data),
            content_type='application/json'
        )

    @retry(
        stop=stop_after_attempt(settings.DEFAULT_MAX_RETRIES),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((S3Error, urllib3.exceptions.HTTPError))
    )
    def get_object(self, key: str) -> Optional[dict]:
        """Get object from MinIO bucket."""
        try:
            with self.client.get_object(self.bucket, key) as response:
                return json.loads(response.read().decode('utf-8'))
        except S3Error as e:
            if e.code == 'NoSuchKey':
                return None
            raise
