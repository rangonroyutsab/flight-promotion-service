from datetime import datetime
from typing import List, Dict, Any
from django.utils import timezone
from promotions.clients.minio_client import MinioClient
from promotions.schemas.run_manifest import RunManifest
from promotions.schemas.latest_pointer import LatestPointer

class ManifestService:
    def __init__(self):
        self.minio = MinioClient()

    def get_manifest(self, run_date: str):
        """Returns the manifest data if it exists, or None."""
        manifest_key = f"promotion-runs/{run_date}.json"
        return self.minio.get_object(manifest_key)

    def publish_run(
        self, 
        run_date: str, 
        started_at: datetime, 
        finished_at: datetime, 
        processing_results: List[Dict[str, Any]]
    ):
        """
        Groups the results of generated promotions into a manifest, uploads it,
        and updates the latest pointer.
        """
        succeeded = sum(1 for item in processing_results if item.get("status") == "success")
        failed = sum(1 for item in processing_results if item.get("status") == "failed")
        
        manifest = RunManifest(
            schema_version="1.0",
            date=run_date,
            timezone="Asia/Dhaka",
            status="completed",
            started_at=started_at.isoformat(),
            finished_at=finished_at.isoformat(),
            selected_count=len(processing_results),
            succeeded_count=succeeded,
            failed_count=failed,
            items=processing_results
        )
        
        manifest_key = f"promotion-runs/{run_date}.json"
        
        self.minio.upload_object(manifest_key, manifest.model_dump(mode="json"))

        pointer = LatestPointer(
            schema_version="1.0",
            date=run_date,
            manifest_key=manifest_key,
            updated_at=timezone.now().isoformat()
        )
        self.minio.upload_object("latest.json", pointer.model_dump(mode="json"))
        
        return manifest_key
