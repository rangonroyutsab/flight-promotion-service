import datetime
import logging

from django.conf import settings
from rest_framework import status
from rest_framework.views import APIView

from apps.promotions.services.promotion_reader import PromotionReader

from .responses import error_response, success_response

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
                datetime.datetime.strptime(date_str, "%Y-%m-%d").replace(
                    tzinfo=datetime.timezone.utc
                )
            except ValueError:
                return error_response(
                    code="invalid_date",
                    message="The date must use the YYYY-MM-DD format.",
                    status_code=status.HTTP_400_BAD_REQUEST,
                )
            reader = PromotionReader()
            manifest, results = reader.get_promotions_for_date(date_str)
            fallback_date = date_str
        else:
            reader = PromotionReader()
            manifest, results = reader.get_latest_promotions()
            fallback_date = datetime.datetime.now(tz=datetime.timezone.utc).strftime(
                "%Y-%m-%d"
            )

        return self._build_list_response(request, manifest, results, fallback_date)

    def _format_promotion_item(self, promo_obj):
        """Map output JSON promotion object to response item structure (title and content only)."""
        promo_id = promo_obj["promotion_id"]
        title = promo_obj.get("title") or promo_obj.get("promotion", {}).get(
            "title", ""
        )
        content = promo_obj.get("content") or promo_obj.get("promotion", {}).get(
            "content", ""
        )
        return {"id": promo_id, "title": title, "content": content}

    def _build_list_response(self, request, manifest, results, fallback_date):
        items = [self._format_promotion_item(r) for r in results]
        actual_count = len(items)

        if not manifest:
            meta = {
                "date": fallback_date,
                "count": actual_count,
                "timezone": settings.TIME_ZONE,
                "partial": False,
            }
            return success_response(data=items, meta=meta)

        expected_count = manifest.succeeded_count
        partial = actual_count < expected_count

        meta = {
            "date": manifest.date,
            "count": actual_count,
            "timezone": manifest.timezone,
            "partial": partial,
        }
        if partial:
            meta["unavailable_count"] = expected_count - actual_count

        return success_response(data=items, meta=meta)
