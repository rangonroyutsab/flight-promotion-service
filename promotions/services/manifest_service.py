import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

from django.conf import settings
from django.utils import timezone

from promotions.clients.minio_client import MinioClient
from promotions.schemas.run_manifest import RunManifest
from promotions.schemas.latest_pointer import LatestPointer

logger = logging.getLogger(__name__)


class ManifestService:
    def __init__(self):
        self.minio = MinioClient()

    def get_manifest(self, run_date: str) -> Optional[RunManifest]:
        """Returns a validated RunManifest if it exists for the given date, or None."""
        manifest_key = f"promotion-runs/{run_date}.json"
        data = self.minio.get_object(manifest_key)
        if data is None:
            return None
        logger.debug("Loaded manifest for %s from MinIO.", run_date)
        return RunManifest(**data)

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

        # schema_version defaults to "1.0" via Pydantic field default
        manifest = RunManifest(
            date=run_date,
            timezone=settings.TIME_ZONE,
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
        logger.info("Manifest published for %s (succeeded=%d, failed=%d).", run_date, succeeded, failed)

        # schema_version defaults to "1.0" via Pydantic field default
        pointer = LatestPointer(
            date=run_date,
            manifest_key=manifest_key,
            updated_at=timezone.now().isoformat()
        )
        self.minio.upload_object("latest.json", pointer.model_dump(mode="json"))
        logger.info("Latest pointer updated to %s.", run_date)

        return manifest_key
