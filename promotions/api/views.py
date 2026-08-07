import datetime
import logging

from django.conf import settings
from django.urls import reverse
from rest_framework import status
from rest_framework.views import APIView

from .responses import success_response, error_response
from promotions.services.promotion_reader import PromotionReader
from promotions.models import PromotionPrompt

logger = logging.getLogger(__name__)


class PromotionsListView(APIView):
    """
    Handles both 'latest' and 'date-specific' promotion listing.

    GET /api/v1/promotions/           — returns latest promotions
    GET /api/v1/promotions/?date=YYYY-MM-DD — returns promotions for a specific date
    """

    def get(self, request, *args, **kwargs):
        date_str = request.query_params.get("date")

        if date_str:
            # Validate date format
            try:
                datetime.datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                return error_response(
                    code="invalid_date",
                    message="The date must use the YYYY-MM-DD format.",
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            reader = PromotionReader()
            manifest, results = reader.get_promotions_for_date(date_str)
            fallback_date = date_str
        else:
            reader = PromotionReader()
            manifest, results = reader.get_latest_promotions()
            fallback_date = datetime.datetime.now().strftime("%Y-%m-%d")

        return self._build_list_response(request, manifest, results, fallback_date)

    def _format_promotion_summary(self, request, promo_obj):
        """Map canonical MinIO object to list summary structure."""
        promo_id = promo_obj["promotion_id"]
        return {
            "id": promo_id,
            "title": promo_obj["promotion"]["title"],
            "content": promo_obj["promotion"]["content"],
            "detail_url": request.build_absolute_uri(reverse("promotion-detail", args=[promo_id]))
        }

    def _build_list_response(self, request, manifest, results, fallback_date):
        if not manifest:
            meta = {
                "date": fallback_date,
                "count": 0,
                "timezone": settings.TIME_ZONE,
                "partial": False,
            }
            return success_response(data=[], meta=meta)

        summaries = [self._format_promotion_summary(request, r) for r in results]

        expected_count = manifest.succeeded_count
        actual_count = len(summaries)
        partial = actual_count < expected_count

        meta = {
            "date": manifest.date,
            "count": actual_count,
            "timezone": manifest.timezone,
            "partial": partial,
        }
        if partial:
            meta["unavailable_count"] = expected_count - actual_count

        return success_response(data=summaries, meta=meta)


class PromotionDetailView(APIView):
    def get(self, request, promotion_id, *args, **kwargs):
        try:
            prompt = PromotionPrompt.objects.get(id=promotion_id)
        except PromotionPrompt.DoesNotExist:
            return error_response(
                code="promotion_not_found",
                message="Promotion not found.",
                status_code=status.HTTP_404_NOT_FOUND
            )

        reader = PromotionReader()
        promo_data = reader.get_promotion_by_id(prompt.minio_object_key)

        if not promo_data or promo_data.get("promotion_id") != str(promotion_id):
            return error_response(
                code="promotion_not_found",
                message="Promotion not found.",
                status_code=status.HTTP_404_NOT_FOUND
            )

        mapped_data = {
            "id": promo_data["promotion_id"],
            "title": promo_data["promotion"]["title"],
            "content": promo_data["promotion"]["content"],
            "flight": promo_data["flight"],
            "generated_at": promo_data["generation"]["generated_at"]
        }

        return success_response(data=mapped_data)
