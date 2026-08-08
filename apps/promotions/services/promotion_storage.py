import logging
from datetime import datetime, timezone

from apps.promotions.clients.minio_client import MinioClient
from apps.promotions.schemas.promotion_input import (
    DailyPromotionsInput,
    PromotionInputItem,
)
from apps.promotions.schemas.promotion_object import (
    DailyPromotionsOutput,
    PromotionObject,
)

logger = logging.getLogger(__name__)


class PromotionStorageService:
    def __init__(self, minio_client: MinioClient = None):
        self.minio = minio_client or MinioClient()

    def save_inputs(
        self, local_date: str, input_items: list[PromotionInputItem]
    ) -> str:
        """
        Saves all generation inputs (prompts and flight details) for a given date
        into inputs/{local_date}/{local_date}.json in MinIO.
        Returns the MinIO object key.
        """
        key = f"inputs/{local_date}/{local_date}.json"
        daily_input = DailyPromotionsInput(
            date=local_date,
            created_at=datetime.now(timezone.utc).isoformat(),
            inputs=input_items,
        )
        self.minio.upload_object(key, daily_input.model_dump(mode="json"))
        logger.info("Saved %d input prompts to MinIO at '%s'.", len(input_items), key)
        return key

    def save_outputs(
        self, local_date: str, promotion_objects: list[PromotionObject]
    ) -> str:
        """
        Saves all generated promotion contents for a given date together
        into outputs/{local_date}/{local_date}.json in MinIO.
        Returns the MinIO object key.
        """
        key = f"outputs/{local_date}/{local_date}.json"
        daily_output = DailyPromotionsOutput(
            date=local_date,
            generated_at=datetime.now(timezone.utc).isoformat(),
            promotions=promotion_objects,
        )
        self.minio.upload_object(key, daily_output.model_dump(mode="json"))
        logger.info(
            "Saved %d promotion outputs to MinIO at '%s'.", len(promotion_objects), key
        )
        return key

    def has_outputs(self, local_date: str) -> bool:
        """Checks if generated promotion outputs already exist for the date."""
        key = f"outputs/{local_date}/{local_date}.json"
        return self.minio.get_object(key) is not None
