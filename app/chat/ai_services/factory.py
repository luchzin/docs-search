import logging
from .base import BaseLLMProvider
from .gemini_provider import GeminiProvider
from .openai_provider import OpenAIProvider
from .claude_provider import ClaudeProvider
from .deepseek_provider import DeepSeekProvider

logger = logging.getLogger(__name__)


class LLMFactory:
    """Factory class to retrieve modular LLM provider instances based on model ID or provider name."""

    @staticmethod
    def get_provider(model_name: str | None = None) -> BaseLLMProvider:
        normalized = (model_name or "gemini-3.6-flash").lower()

        if "gpt" in normalized or "openai" in normalized:
            return OpenAIProvider(model_id=normalized)

        if "claude" in normalized or "anthropic" in normalized:
            return ClaudeProvider(model_id=normalized)

        if "deepseek" in normalized:
            return DeepSeekProvider(model_id=normalized)

        # Default provider is Google Gemini 3.6 Flash
        return GeminiProvider(model_id=normalized)
