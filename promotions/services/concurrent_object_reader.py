import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any

from promotions.clients.minio_client import MinioClient

logger = logging.getLogger(__name__)


class ConcurrentObjectReader:
    def __init__(self, max_workers: int = 5):
        self.minio = MinioClient()
        self.max_workers = max_workers

    def fetch_all(self, keys: List[str]) -> List[Dict[str, Any]]:
        results = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_key = {executor.submit(self.minio.get_object, key): key for key in keys}
            for future in as_completed(future_to_key):
                key = future_to_key[future]
                try:
                    data = future.result()
                    if data:
                        results.append(data)
                except Exception:
                    logger.warning(
                        "Failed to fetch MinIO object for key '%s'.", key, exc_info=True
                    )
        return results
