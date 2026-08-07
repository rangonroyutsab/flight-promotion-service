import logging
from datetime import datetime, timezone
from typing import Dict, Any

from django.conf import settings

from promotions.clients.minio_client import MinioClient
from promotions.models import PromotionPrompt
from promotions.schemas.promotion_object import PromotionObject, PromotionContent, GenerationMeta
from promotions.schemas.ai_response import AIResponse

logger = logging.getLogger(__name__)


class PromotionStorageService:
    def __init__(self, minio_client: MinioClient = None):
        self.minio = minio_client or MinioClient()

    def save_promotion(
        self,
        promo_uuid: str,
        local_date: str,
        prompt_text: str,
        ai_response: AIResponse,
        flight_data: Dict[str, Any]
    ) -> str:
        """
        Saves the prompt audit log to Postgres and the canonical JSON to MinIO.
        Returns the canonical MinIO key.
        """
        canonical_key = f"promotions/{local_date}/{promo_uuid}.json"

        PromotionPrompt.objects.update_or_create(
            id=promo_uuid,
            defaults={
                "prompt_text": prompt_text,
                "minio_object_key": canonical_key
            }
        )

        # schema_version defaults to "1.0" via Pydantic field default
        promo_obj = PromotionObject(
            promotion_id=promo_uuid,
            promotion=PromotionContent(title=ai_response.title, content=ai_response.content),
            flight=flight_data,
            generation=GenerationMeta(
                provider=settings.AI_PROVIDER,
                model=settings.AI_MODEL,
                generated_at=datetime.now(timezone.utc).isoformat()
            )
        )
        self.minio.upload_object(canonical_key, promo_obj.model_dump(mode="json"))
        logger.debug("Promotion %s saved to MinIO at key '%s'.", promo_uuid, canonical_key)

        return canonical_key
