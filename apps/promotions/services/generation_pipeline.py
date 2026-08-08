import logging
import uuid
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from django.conf import settings

from apps.promotions.clients.ai.gemini import GeminiProvider
from apps.promotions.clients.elasticsearch_client import ElasticsearchClient
from apps.promotions.schemas.promotion_input import PromotionInputItem
from apps.promotions.schemas.promotion_object import PromotionObject
from apps.promotions.services.manifest_service import ManifestService
from apps.promotions.services.promotion_storage import PromotionStorageService
from apps.promotions.services.prompt_builder import PromptBuilder

logger = logging.getLogger(__name__)


class GenerationPipeline:
    def __init__(self, es=None, ai=None, manifest_svc=None, storage=None):
        self.es = es or ElasticsearchClient()
        self.ai = ai or GeminiProvider()
        self.manifest_svc = manifest_svc or ManifestService()
        self.storage = storage or PromotionStorageService()
        self.tz = ZoneInfo(settings.TIME_ZONE)

    def get_time_boundaries(self, now_local: datetime, is_scheduled: bool):
        """Encapsulate time boundary calculations."""
        start_of_day = now_local.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)

        effective_start = start_of_day if is_scheduled else max(now_local, start_of_day)

        start_utc = effective_start.astimezone(timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
        end_utc = end_of_day.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        return start_utc, end_utc

    def run(self, is_scheduled: bool = True):
        now_local = datetime.now(self.tz)
        local_date = now_local.strftime("%Y-%m-%d")

        logger.info(
            "GenerationPipeline starting for date: %s (scheduled=%s)",
            local_date,
            is_scheduled,
        )

        start_utc, end_utc = self.get_time_boundaries(now_local, is_scheduled)

        existing_manifest = self.manifest_svc.get_manifest(local_date)
        if existing_manifest:
            logger.info("Run for %s already exists. Skipping.", local_date)
            return

        flights = self.es.search_flights(start_utc, end_utc)
        logger.info("Found %d eligible flights for %s.", len(flights), local_date)

        input_items: list[PromotionInputItem] = []
        promotion_objects: list[PromotionObject] = []
        processing_results = []

        for flight_hit in flights:
            flight = flight_hit["_source"]
            flight_id = flight_hit["_id"]

            promo_uuid = str(
                uuid.uuid5(uuid.NAMESPACE_DNS, f"{local_date}:{flight_id}")
            )
            prompt_text = PromptBuilder.build_flight_prompt(flight)

            input_item = PromotionInputItem(
                promotion_id=promo_uuid,
                flight_id=str(flight_id),
                prompt_text=prompt_text,
                flight=flight,
            )
            input_items.append(input_item)

            try:
                ai_res = self.ai.generate_promotion(prompt_text)
                promo_obj = PromotionObject(
                    promotion_id=promo_uuid, title=ai_res.title, content=ai_res.content
                )
                promotion_objects.append(promo_obj)
                processing_results.append(
                    {"promotion_id": promo_uuid, "status": "success"}
                )
                logger.info("Promotion %s generated successfully.", promo_uuid)
            except Exception as e:
                logger.exception(
                    "Failed to generate promotion for flight %s.", flight_id
                )

                processing_results.append(
                    {"promotion_id": promo_uuid, "status": "failed", "error": str(e)}
                )

        input_key = self.storage.save_inputs(local_date, input_items)
        output_key = self.storage.save_outputs(local_date, promotion_objects)

        self.manifest_svc.publish_run(
            run_date=local_date,
            started_at=now_local,
            finished_at=datetime.now(self.tz),
            processing_results=processing_results,
            input_key=input_key,
            output_key=output_key,
        )
        logger.info(
            "GenerationPipeline finished for %s: %d succeeded, %d failed.",
            local_date,
            sum(1 for r in processing_results if r["status"] == "success"),
            sum(1 for r in processing_results if r["status"] == "failed"),
        )
