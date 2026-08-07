import logging
from typing import List, Dict, Any, Tuple, Optional

from promotions.clients.minio_client import MinioClient
from promotions.services.concurrent_object_reader import ConcurrentObjectReader
from promotions.schemas.run_manifest import RunManifest
from promotions.schemas.latest_pointer import LatestPointer

logger = logging.getLogger(__name__)


class PromotionReader:
    def __init__(self):
        self.minio = MinioClient()
        self.concurrent_reader = ConcurrentObjectReader()

    def get_latest_promotions(self) -> Tuple[Optional[RunManifest], List[Dict[str, Any]]]:
        pointer_data = self.minio.get_object("latest.json")
        if not pointer_data:
            return None, []

        pointer = LatestPointer(**pointer_data)
        return self.get_promotions_by_manifest(pointer.manifest_key)

    def get_promotions_for_date(self, date_str: str) -> Tuple[Optional[RunManifest], List[Dict[str, Any]]]:
        manifest_key = f"promotion-runs/{date_str}.json"
        return self.get_promotions_by_manifest(manifest_key)

    def get_promotions_by_manifest(self, manifest_key: str) -> Tuple[Optional[RunManifest], List[Dict[str, Any]]]:
        manifest_data = self.minio.get_object(manifest_key)
        if not manifest_data:
            return None, []

        manifest = RunManifest(**manifest_data)

        success_keys = [
            item.canonical_key
            for item in manifest.items
            if item.status == "success" and item.canonical_key
        ]

        results = self.concurrent_reader.fetch_all(success_keys)
        return manifest, results

    def get_promotion_by_id(self, minio_object_key: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves a single promotion object from MinIO by its stored object key.
        Centralises MinIO access so views don't need to instantiate MinioClient directly.
        """
        logger.debug("Fetching promotion from MinIO key '%s'.", minio_object_key)
        return self.minio.get_object(minio_object_key)
