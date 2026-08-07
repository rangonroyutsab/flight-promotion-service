import logging

import requests
from django.conf import settings
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from promotions.schemas.ai_response import AIResponse

logger = logging.getLogger(__name__)


class AIProviderError(Exception):
    """Custom exception raised when the AI provider fails to generate a valid response."""
    pass


class GeminiProvider:
    def generate_promotion(self, prompt: str) -> AIResponse:
        """
        Generate a flight promotion using the Gemini API.

        The @retry decorator is intentionally applied inside this method (as a
        local inner function) rather than at class-definition time. This avoids
        reading settings.DEFAULT_MAX_RETRIES before Django's app registry is
        fully initialized (which would happen if @retry were a class-level decorator).
        """
        @retry(
            stop=stop_after_attempt(settings.DEFAULT_MAX_RETRIES),
            wait=wait_exponential(multiplier=1, min=2, max=10),
            retry=retry_if_exception_type((requests.exceptions.RequestException,))
        )
        def _call_api(prompt: str) -> AIResponse:
            if not settings.GEMINI_API_URL or not settings.AI_API_KEY:
                raise AIProviderError("Gemini API URL or Key is not configured.")

            # Using the standard Gemini REST API payload structure for generateContent
            payload = {
                "contents": [{
                    "parts": [{"text": prompt}]
                }],
                "generationConfig": {
                    "response_mime_type": "application/json"
                }
            }

            headers = {
                "Content-Type": "application/json",
                "x-goog-api-key": settings.AI_API_KEY
            }

            try:
                response = requests.post(
                    settings.GEMINI_API_URL,
                    json=payload,
                    headers=headers,
                    timeout=settings.DEFAULT_TIMEOUT_SECONDS
                )
                response.raise_for_status()

                data = response.json()
                # Extract text from the standard Gemini response payload
                text_response = data.get("candidates", [])[0].get("content", {}).get("parts", [])[0].get("text", "{}")

                # Pydantic will parse the JSON string and validate the schema
                return AIResponse.model_validate_json(text_response)

            except requests.exceptions.RequestException as e:
                # Let Tenacity catch this and retry
                logger.warning("Gemini API request failed (will retry): %s", e)
                raise
            except (KeyError, IndexError, ValueError) as e:
                # Validation or parsing error — don't retry bad AI output indefinitely
                raise AIProviderError(f"Failed to parse or validate Gemini response: {str(e)}")

        return _call_api(prompt)
