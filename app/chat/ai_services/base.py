from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)


class LLMProviderError(Exception):
    """Base exception for LLM provider failures."""
    pass


class QuotaExhaustedError(LLMProviderError):
    """Raised when an API key has insufficient credits or quota exhausted."""
    pass


class BaseLLMProvider(ABC):
    """Abstract base provider interface for modular LLM text generation and embeddings."""

    def __init__(self, model_id: str):
        self.model_id = model_id

    @abstractmethod
    def generate_response(self, prompt: str, api_key: str | None = None) -> str:
        """Generates a text completion given a prompt and optional API key."""
        pass

    @abstractmethod
    def get_embedding(self, text: str, api_key: str | None = None) -> list[float]:
        """Generates a 1536-dimensional vector embedding for the input text."""
        pass
