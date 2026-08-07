import uuid
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
from typing import List, Dict, Any

from promotions.clients.elasticsearch_client import ElasticsearchClient
from promotions.clients.ai.gemini import GeminiProvider
from promotions.services.prompt_builder import PromptBuilder
from promotions.services.manifest_service import ManifestService
from promotions.services.promotion_storage import PromotionStorageService

class GenerationPipeline:
    def __init__(self):
        self.es = ElasticsearchClient()
        self.ai = GeminiProvider()
        self.manifest_svc = ManifestService()
        self.storage = PromotionStorageService()
        self.tz = ZoneInfo("Asia/Dhaka")

    def get_time_boundaries(self, now_local: datetime, is_scheduled: bool):
        """Encapsulate time boundary calculations."""
        start_of_day = now_local.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day.replace(day=start_of_day.day + 1) if start_of_day.day < 28 else (start_of_day + timedelta(days=1))
        
        effective_start = start_of_day if is_scheduled else max(now_local, start_of_day)
        
        start_utc = effective_start.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        end_utc = end_of_day.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        
        return start_utc, end_utc

    def run(self, is_scheduled: bool = True):
        now_local = datetime.now(self.tz)
        local_date = now_local.strftime("%Y-%m-%d")
        
        start_utc, end_utc = self.get_time_boundaries(now_local, is_scheduled)
        
        processing_results = []
        existing_manifest = self.manifest_svc.get_manifest(local_date)
        
        if existing_manifest:
            pass 
        else:
            flights = self.es.search_flights(start_utc, end_utc)
            
            for flight_hit in flights:
                flight = flight_hit["_source"]
                flight_id = flight_hit["_id"]
                
                promo_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{local_date}:{flight_id}"))
                prompt_text = PromptBuilder.build_flight_prompt(flight)
                
                try:
                    ai_res = self.ai.generate_promotion(prompt_text)
                    canonical_key = self.storage.save_promotion(
                        promo_uuid=promo_uuid,
                        local_date=local_date,
                        prompt_text=prompt_text,
                        ai_response=ai_res,
                        flight_data=flight
                    )
                    
                    processing_results.append({
                        "promotion_id": promo_uuid,
                        "canonical_key": canonical_key,
                        "status": "success"
                    })
                except Exception as e:
                    processing_results.append({
                        "promotion_id": promo_uuid,
                        "canonical_key": None,
                        "status": "failed",
                        "error": str(e)
                    })
            
            self.manifest_svc.publish_run(
                run_date=local_date,
                started_at=now_local,
                finished_at=datetime.now(self.tz),
                processing_results=processing_results
            )
