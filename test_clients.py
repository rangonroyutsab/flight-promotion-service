import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

import datetime
from django.utils import timezone
from promotions.clients.elasticsearch_client import ElasticsearchClient
from promotions.clients.minio_client import MinioClient
from promotions.clients.ai.gemini import GeminiProvider
from promotions.services.prompt_builder import PromptBuilder
from promotions.services.manifest_service import ManifestService
from promotions.services.promotion_reader import PromotionReader

def run_tests():
    print("--- Testing Elasticsearch ---")
    try:
        es = ElasticsearchClient()
        # The sample data spans a wide range; we use a broad 10-year window to guarantee a hit
        flights = es.search_flights("2020-01-01T00:00:00Z", "2030-01-01T00:00:00Z")
        print(f"✅ Success! Found {len(flights)} flights matching our criteria.")
        if flights:
            print(f"Sample Flight Origin: {flights[0]['_source']['OriginCityName']}")
    except Exception as e:
        print(f"❌ Failed: {e}")

    print("\n--- Testing MinIO ---")
    try:
        minio = MinioClient()
        test_key = "test-upload.json"
        test_data = {"status": "success", "message": "hello world"}
        
        print("Uploading test object...")
        minio.upload_object(test_key, test_data)
        
        print("Downloading test object...")
        downloaded = minio.get_object(test_key)
        
        if downloaded == test_data:
            print(f"✅ Success! Data matches: {downloaded}")
        else:
            print(f"❌ Failed: Data mismatch.")
    except Exception as e:
        print(f"❌ Failed: {e}")

    print("\n--- Testing Gemini AI ---")
    try:
        ai = GeminiProvider()
        response = ai.generate_promotion(
            "Write a short, fake promotional offer for a flight. You MUST return ONLY a JSON object with two string keys: 'title' and 'content'."
        )
        print(f"✅ Success! Received valid AIResponse.")
        print(f"Title: {response.title}")
        print(f"Content: {response.content}")
    except Exception as e:
        print(f"❌ Failed: {e}")

    print("\n--- Testing Phase 2 Services ---")
    try:
        # Test PromptBuilder
        test_flight = {
            "FlightNum": "1234X",
            "Carrier": "TestAir",
            "timestamp": "2026-08-07T01:30:00+06:00",
            "OriginCityName": "Dhaka",
            "OriginCountry": "BD",
            "DestCityName": "New York",
            "DestCountry": "US",
            "AvgTicketPrice": 724.51,
            "FlightTimeMin": 840,
            "DistanceMiles": 7852.4
        }
        prompt = PromptBuilder.build_flight_prompt(test_flight)
        if "1234X" in prompt and "JetBeats" not in prompt:
            print("✅ PromptBuilder works!")
        else:
            print(f"❌ PromptBuilder output incorrect: {prompt}")

        # Test ManifestService
        manifest_svc = ManifestService()
        dummy_processing = [
            {"status": "success", "canonical_key": "promotions/2026-08-07/dummy.json", "promotion_id": "dummy"}
        ]
        
        # Upload a dummy canonical object so ConcurrentObjectReader doesn't fail
        minio_client = MinioClient()
        minio_client.upload_object("promotions/2026-08-07/dummy.json", {"test": "dummy_data"})

        manifest_key = manifest_svc.publish_run(
            run_date="2026-08-07",
            started_at=timezone.now(),
            finished_at=timezone.now(),
            processing_results=dummy_processing
        )
        print(f"✅ ManifestService published to: {manifest_key}")

        # Test PromotionReader / ConcurrentObjectReader
        reader = PromotionReader()
        results = reader.get_latest_promotions()
        if len(results) == 1 and results[0].get("test") == "dummy_data":
            print("✅ PromotionReader & ConcurrentObjectReader successfully fetched dummy data from latest manifest!")
        else:
            print(f"❌ PromotionReader returned unexpected results: {results}")

    except Exception as e:
        print(f"❌ Phase 2 Services failed: {e}")

if __name__ == "__main__":
    run_tests()
