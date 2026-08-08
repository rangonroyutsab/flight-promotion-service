import logging
from typing import Any

from apps.promotions.clients.minio_client import MinioClient
from apps.promotions.schemas.latest_pointer import LatestPointer
from apps.promotions.schemas.promotion_object import DailyPromotionsOutput
from apps.promotions.schemas.run_manifest import RunManifest

logger = logging.getLogger(__name__)


class PromotionReader:
    def __init__(self):
        self.minio = MinioClient()

    def get_latest_promotions(self) -> tuple[RunManifest | None, list[dict[str, Any]]]:
        pointer_data = self.minio.get_object("latest.json")
        if not pointer_data:
            return None, []

        pointer = LatestPointer(**pointer_data)
        return self.get_promotions_for_date(pointer.date)

    def get_promotions_for_date(
        self, date_str: str
    ) -> tuple[RunManifest | None, list[dict[str, Any]]]:
        output_key = f"outputs/{date_str}/{date_str}.json"
        output_data = self.minio.get_object(output_key)

        manifest_key = f"promotion-runs/{date_str}.json"
        manifest_data = self.minio.get_object(manifest_key)
        manifest = RunManifest(**manifest_data) if manifest_data else None

        if not output_data:
            return manifest, []

        daily_output = DailyPromotionsOutput(**output_data)
        promotions_list = [p.model_dump(mode="json") for p in daily_output.promotions]

        return manifest, promotions_list
