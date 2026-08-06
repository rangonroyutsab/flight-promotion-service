from .base import BaseAIProvider

class GeminiProvider(BaseAIProvider):
    def generate_promotion(self, prompt: str) -> dict:
        # TODO: Implement Gemini API call
        return {"title": "Sample Gemini Title", "content": "Sample Gemini Content"}
