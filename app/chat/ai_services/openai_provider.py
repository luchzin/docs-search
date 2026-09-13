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


class OpenAIProvider(BaseLLMProvider):
    """OpenAI Model Provider (GPT-4o, GPT-4o-mini, etc.)."""

    def _get_api_key(self, user_api_key: str | None = None) -> str | None:
        return (
            user_api_key
            or getattr(settings, "OPENAI_API_KEY", None)
            or os.environ.get("OPENAI_API_KEY")
        )

    def generate_response(self, prompt: str, api_key: str | None = None) -> str:
        key = self._get_api_key(api_key)
        if not key:
            raise ValueError("OpenAI API key is required to use OpenAI models.")

        model_name = self.model_id if self.model_id else "gpt-4o-mini"
        mod = _get_openai_module()

        if mod:
            try:
                client = mod.OpenAI(api_key=key)
                response = client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": "You are a helpful document retrieval assistant."},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.3,
                )
                return response.choices[0].message.content.strip()
            except Exception as e:
                err_str = str(e).lower()
                if "insufficient_quota" in err_str or "credit_balance_exhausted" in err_str or "429" in err_str or "quota" in err_str:
                    raise QuotaExhaustedError("You have no credits or tokens remaining on your OpenAI account. Please add credits at https://platform.openai.com/account/billing or switch to Gemini AI.")
                logger.warning(f"OpenAI SDK call failed: {e}, attempting HTTP REST fallback...")

        # REST API Fallback
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": "You are a helpful document retrieval assistant."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.3,
        }
        resp = requests.post(url, headers=headers, json=payload, timeout=25)
        if resp.status_code == 200:
            data = resp.json()
            choices = data.get("choices", [])
            if choices:
                return choices[0].get("message", {}).get("content", "").strip()

        resp_text = resp.text
        if resp.status_code == 429 or "insufficient_quota" in resp_text or "credit_balance_exhausted" in resp_text:
            raise QuotaExhaustedError("You have no credits or tokens remaining on your OpenAI account. Please add credits at https://platform.openai.com/account/billing or switch to Gemini AI.")

        raise LLMProviderError(f"OpenAI API call failed (status {resp.status_code}): {resp_text}")

    def get_embedding(self, text: str, api_key: str | None = None) -> list[float]:
        key = self._get_api_key(api_key)
        if not key:
            raise ValueError("OpenAI API key missing for embedding calculation.")

        mod = _get_openai_module()
        if mod:
            try:
                client = mod.OpenAI(api_key=key)
                response = client.embeddings.create(
                    input=text,
                    model="text-embedding-3-small"
                )
                return response.data[0].embedding
            except Exception as e:
                err_str = str(e).lower()
                if "insufficient_quota" in err_str or "credit_balance_exhausted" in err_str or "429" in err_str:
                    raise QuotaExhaustedError("OpenAI API quota exhausted.")
                logger.warning(f"OpenAI SDK embedding failed: {e}, using REST fallback...")

        url = "https://api.openai.com/v1/embeddings"
        headers = {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        }
        payload = {
            "input": text,
            "model": "text-embedding-3-small",
        }
        resp = requests.post(url, headers=headers, json=payload, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            emb_data = data.get("data", [])
            if emb_data:
                return emb_data[0].get("embedding", [])

        if resp.status_code == 429 or "insufficient_quota" in resp.text or "credit_balance_exhausted" in resp.text:
            raise QuotaExhaustedError("OpenAI API quota exhausted.")

        raise LLMProviderError("Failed to fetch OpenAI vector embedding.")
