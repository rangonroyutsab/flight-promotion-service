from unittest.mock import MagicMock, patch

from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from apps.promotions.schemas.ai_response import AIResponse
from apps.promotions.schemas.promotion_input import PromotionInputItem
from apps.promotions.schemas.promotion_object import PromotionObject
from apps.promotions.services.generation_pipeline import GenerationPipeline
from apps.promotions.services.promotion_storage import PromotionStorageService


class MockMinioClient:
    def __init__(self):
        self.store = {}

    def upload_object(self, key: str, data: dict):
        self.store[key] = data

    def get_object(self, key: str):
        return self.store.get(key)


class PromotionStorageServiceTest(TestCase):
    def setUp(self):
        self.mock_minio = MockMinioClient()
        self.storage = PromotionStorageService(minio_client=self.mock_minio)

    def test_save_inputs_and_outputs(self):
        date_str = "2026-08-06"
        input_item = PromotionInputItem(
            promotion_id="promo-1",
            flight_id="flight-100",
            prompt_text="Test prompt",
            flight={"FlightNum": "100"},
        )
        input_key = self.storage.save_inputs(date_str, [input_item])
        self.assertEqual(input_key, "inputs/2026-08-06/2026-08-06.json")

        promo_obj = PromotionObject(
            promotion_id="promo-1",
            title="Fly to NYC",
            content="Great deal to New York!",
        )
        output_key = self.storage.save_outputs(date_str, [promo_obj])
        self.assertEqual(output_key, "outputs/2026-08-06/2026-08-06.json")

        self.assertTrue(self.storage.has_outputs(date_str))
        self.assertIn("inputs/2026-08-06/2026-08-06.json", self.mock_minio.store)
        self.assertIn("outputs/2026-08-06/2026-08-06.json", self.mock_minio.store)

        output_data = self.mock_minio.store["outputs/2026-08-06/2026-08-06.json"]
        promo_dict = output_data["promotions"][0]
        self.assertNotIn("schema_version", output_data)
        self.assertNotIn("schema_version", promo_dict)
        self.assertNotIn("generation", promo_dict)
        self.assertNotIn("flight", promo_dict)


class GenerationPipelineTest(TestCase):
    def test_pipeline_run_stores_single_json_inputs_and_outputs(self):
        mock_es = MagicMock()
        mock_es.search_flights.return_value = [
            {
                "_id": "F1",
                "_source": {
                    "FlightNum": "AA100",
                    "DestCountry": "US",
                    "AvgTicketPrice": 650.0,
                },
            }
        ]

        mock_ai = MagicMock()
        mock_ai.generate_promotion.return_value = AIResponse(
            title="Special Flight to US",
            content="Enjoy amazing discounts on flights to US.",
        )

        mock_minio = MockMinioClient()
        storage = PromotionStorageService(minio_client=mock_minio)
        manifest_svc = MagicMock()
        manifest_svc.get_manifest.return_value = None

        pipeline = GenerationPipeline(
            es=mock_es, ai=mock_ai, manifest_svc=manifest_svc, storage=storage
        )

        pipeline.run(is_scheduled=True)

        # Verify keys in storage
        input_keys = [k for k in mock_minio.store if k.startswith("inputs/")]
        output_keys = [k for k in mock_minio.store if k.startswith("outputs/")]

        self.assertEqual(len(input_keys), 1)
        self.assertEqual(len(output_keys), 1)

        input_data = mock_minio.store[input_keys[0]]
        output_data = mock_minio.store[output_keys[0]]

        self.assertEqual(len(input_data["inputs"]), 1)
        self.assertEqual(input_data["inputs"][0]["flight_id"], "F1")
        self.assertIn("flight", input_data["inputs"][0])

        self.assertEqual(len(output_data["promotions"]), 1)
        promo_dict = output_data["promotions"][0]
        self.assertEqual(promo_dict["title"], "Special Flight to US")
        self.assertNotIn("schema_version", promo_dict)
        self.assertNotIn("generation", promo_dict)
        self.assertNotIn("flight", promo_dict)


class PromotionAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()

    @patch("apps.promotions.services.promotion_reader.MinioClient")
    def test_list_promotions_returns_200(self, mock_minio_cls):
        mock_minio_cls.return_value.get_object.return_value = None
        response = self.client.get("/api/v1/promotions/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("data", response.data)
        self.assertIn("meta", response.data)

    @patch("apps.promotions.services.promotion_reader.MinioClient")
    def test_list_promotions_by_date_returns_200(self, mock_minio_cls):
        mock_minio_cls.return_value.get_object.return_value = None
        response = self.client.get("/api/v1/promotions/?date=2026-08-06")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("data", response.data)
        self.assertIn("meta", response.data)

    def test_removed_detail_endpoint_returns_404(self):
        response = self.client.get(
            "/api/v1/promotions/0b5172a2-df37-516c-b5ed-ca6165ea2f4e"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
