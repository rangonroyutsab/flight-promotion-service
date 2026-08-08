import logging

import requests
from django.conf import settings
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from apps.promotions.schemas.ai_response import AIResponse

logger = logging.getLogger(__name__)


class AIProviderError(Exception):
    """Custom exception raised when the AI provider fails to generate a valid response."""


class GeminiProvider:
    def generate_promotion(self, prompt: str) -> AIResponse:
        """Generate a flight promotion using the Gemini API."""

        @retry(
            stop=stop_after_attempt(settings.DEFAULT_MAX_RETRIES),
            wait=wait_exponential(multiplier=1, min=2, max=10),
            retry=retry_if_exception_type((requests.exceptions.RequestException,)),
        )
        def _call_api(prompt: str) -> AIResponse:
            if not settings.GEMINI_API_URL or not settings.AI_API_KEY:
                raise AIProviderError("Gemini API URL or Key is not configured.")

            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"response_mime_type": "application/json"},
            }

            headers = {
                "Content-Type": "application/json",
                "x-goog-api-key": settings.AI_API_KEY,
            }

            try:
                response = requests.post(
                    settings.GEMINI_API_URL,
                    json=payload,
                    headers=headers,
                    timeout=settings.DEFAULT_TIMEOUT_SECONDS,
                )
                response.raise_for_status()
                data = response.json()
                text_response = (
                    data.get("candidates", [])[0]
                    .get("content", {})
                    .get("parts", [])[0]
                    .get("text", "{}")
                )

                return AIResponse.model_validate_json(text_response)

            except requests.exceptions.RequestException as e:
                logger.warning("Gemini API request failed (will retry): %s", e)
                raise
            except (KeyError, IndexError, ValueError) as e:
                raise AIProviderError(
                    f"Failed to parse or validate Gemini response: {e!s}"
                )

        return _call_api(prompt)
