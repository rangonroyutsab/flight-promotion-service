from typing import List, Dict, Any, Tuple, Optional
from promotions.clients.minio_client import MinioClient
from .concurrent_object_reader import ConcurrentObjectReader
from promotions.schemas.run_manifest import RunManifest
from promotions.schemas.latest_pointer import LatestPointer

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
            item.get("canonical_key") 
            for item in manifest.items 
            if item.get("status") == "success" and item.get("canonical_key")
        ]
        
        results = self.concurrent_reader.fetch_all(success_keys)
        return manifest, results
