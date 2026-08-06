import abc

class BaseAIProvider(abc.ABC):
    @abc.abstractmethod
    def generate_promotion(self, prompt: str) -> dict:
        """Generate promotion content given a prompt."""
        pass
