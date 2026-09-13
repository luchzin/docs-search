import os
import logging
import requests
from django.conf import settings
from .base import BaseLLMProvider, QuotaExhaustedError, LLMProviderError

logger = logging.getLogger(__name__)

try:
    import anthropic
except ImportError:
    anthropic = None


class ClaudeProvider(BaseLLMProvider):
    """Anthropic Claude LLM Provider (Claude 3.5 Sonnet, etc.)."""

    def _get_api_key(self, user_api_key: str | None = None) -> str | None:
        return (
            user_api_key
            or getattr(settings, "ANTHROPIC_API_KEY", None)
            or os.environ.get("ANTHROPIC_API_KEY")
        )

    def generate_response(self, prompt: str, api_key: str | None = None) -> str:
        key = self._get_api_key(api_key)
        if not key:
            raise ValueError("Anthropic API key is required to use Claude models.")

        target_model = self.model_id if self.model_id else "claude-3-5-sonnet-20241022"
        if target_model == "claude-3-5-sonnet":
            target_model = "claude-3-5-sonnet-20241022"

        if anthropic:
            try:
                client = anthropic.Anthropic(api_key=key)
                res = client.messages.create(
                    model=target_model,
                    max_tokens=1024,
                    messages=[{"role": "user", "content": prompt}],
                )
                if res and res.content:
                    return res.content[0].text.strip()
            except Exception as e:
                err_str = str(e).lower()
                if "rate_limit" in err_str or "credit" in err_str or "balance" in err_str or "429" in err_str:
                    raise QuotaExhaustedError("You have no credits or tokens remaining on your Anthropic account. Please check your billing settings or switch to Gemini AI.")
                logger.warning(f"Anthropic SDK call failed: {e}")

        # Fallback HTTP REST request
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        payload = {
            "model": target_model,
            "max_tokens": 1024,
            "messages": [{"role": "user", "content": prompt}],
        }
        resp = requests.post(url, headers=headers, json=payload, timeout=25)
        if resp.status_code == 200:
            data = resp.json()
            content = data.get("content", [])
            if content:
                return content[0].get("text", "").strip()

        if resp.status_code == 429 or "credit" in resp.text.lower() or "balance" in resp.text.lower():
            raise QuotaExhaustedError("You have no credits or tokens remaining on your Anthropic account. Please check your billing settings or switch to Gemini AI.")

        raise LLMProviderError(f"Claude API failed with status {resp.status_code}: {resp.text}")

    def get_embedding(self, text: str, api_key: str | None = None) -> list[float]:
        from .gemini_provider import GeminiProvider
        gemini = GeminiProvider(model_id="gemini-3.6-flash")
        try:
            return gemini.get_embedding(text)
        except Exception:
            from app.docs.services import _generate_deterministic_embedding
            return _generate_deterministic_embedding(text)
