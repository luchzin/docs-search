import os
import logging
import requests
from django.conf import settings
from .base import BaseLLMProvider, QuotaExhaustedError, LLMProviderError

logger = logging.getLogger(__name__)

try:
    import openai
except ImportError:
    openai = None


def _get_openai_module():
    global openai
    if openai is None:
        try:
            import openai as _o
            openai = _o
        except ImportError:
            pass
    return openai


class DeepSeekProvider(BaseLLMProvider):
    """DeepSeek AI LLM Provider (DeepSeek V3 / deepseek-chat)."""

    def _get_api_key(self, user_api_key: str | None = None) -> str | None:
        return (
            user_api_key
            or getattr(settings, "DEEPSEEK_API_KEY", None)
            or os.environ.get("DEEPSEEK_API_KEY")
        )

    def generate_response(self, prompt: str, api_key: str | None = None) -> str:
        key = self._get_api_key(api_key)
        if not key:
            raise ValueError("DeepSeek API key is required to use DeepSeek models.")

        target_model = self.model_id if self.model_id else "deepseek-chat"
        mod = _get_openai_module()

        if mod:
            try:
                client = mod.OpenAI(api_key=key, base_url="https://api.deepseek.com")
                res = client.chat.completions.create(
                    model=target_model,
                    messages=[
                        {"role": "system", "content": "You are a helpful document retrieval assistant."},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.3,
                )
                return res.choices[0].message.content.strip()
            except Exception as e:
                err_str = str(e).lower()
                if "insufficient_balance" in err_str or "credit" in err_str or "429" in err_str or "quota" in err_str:
                    raise QuotaExhaustedError("You have no credits or balance remaining on your DeepSeek account. Please add credits to continue or switch to Gemini AI.")
                logger.warning(f"DeepSeek OpenAI-client call failed: {e}")

        url = "https://api.deepseek.com/chat/completions"
        headers = {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": target_model,
            "messages": [
                {"role": "system", "content": "You are a helpful document retrieval assistant."},
                {"role": "user", "content": prompt},
            ],
        }
        resp = requests.post(url, headers=headers, json=payload, timeout=25)
        if resp.status_code == 200:
            data = resp.json()
            choices = data.get("choices", [])
            if choices:
                return choices[0].get("message", {}).get("content", "").strip()

        if resp.status_code == 429 or "insufficient" in resp.text.lower() or "balance" in resp.text.lower():
            raise QuotaExhaustedError("You have no credits or balance remaining on your DeepSeek account. Please add credits to continue or switch to Gemini AI.")

        raise LLMProviderError(f"DeepSeek API call failed with status {resp.status_code}: {resp.text}")

    def get_embedding(self, text: str, api_key: str | None = None) -> list[float]:
        from .gemini_provider import GeminiProvider
        gemini = GeminiProvider(model_id="gemini-3.6-flash")
        try:
            return gemini.get_embedding(text)
        except Exception:
            from app.docs.services import _generate_deterministic_embedding
            return _generate_deterministic_embedding(text)
