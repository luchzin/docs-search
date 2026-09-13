import os
import logging
import requests
from django.conf import settings
from .base import BaseLLMProvider, QuotaExhaustedError, LLMProviderError

logger = logging.getLogger(__name__)

try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None


class GeminiProvider(BaseLLMProvider):
    """Google Gemini AI Provider (Default system AI using gemini-3.6-flash)."""

    def _get_api_key(self, user_api_key: str | None = None) -> str | None:
        # Ignore third-party keys (e.g. OpenAI sk-...) if passed when model is Gemini
        if user_api_key and (user_api_key.startswith("sk-") or user_api_key.startswith("sk-ant-") or len(user_api_key.strip()) < 10):
            user_api_key = None

        return (
            user_api_key
            or getattr(settings, "GEMINI_API_KEY", None)
            or getattr(settings, "GOOGLE_API_KEY", None)
            or os.environ.get("GEMINI_API_KEY")
            or os.environ.get("GOOGLE_API_KEY")
        )

    def generate_response(self, prompt: str, api_key: str | None = None) -> str:
        key = self._get_api_key(api_key)
        if not key:
            raise ValueError("Gemini API key is not configured on server or request.")

        target_model = self.model_id if self.model_id else "gemini-3.6-flash"
        if target_model in ["gemini-2.0-flash", "gemini-2.5-flash", "gemini-1.5-flash", "gemini"]:
            target_model = "gemini-3.6-flash"

        candidate_models = [target_model, "gemini-3.6-flash"]

        last_error = None

        # Try Google GenAI SDK first
        if genai:
            try:
                client = genai.Client(api_key=key)
                for g_model in candidate_models:
                    try:
                        res = client.models.generate_content(
                            model=g_model,
                            contents=prompt,
                            config=types.GenerateContentConfig(
                                automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True)
                            ),
                        )
                        if res and res.text:
                            return res.text.strip()
                    except Exception as ge:
                        err_str = str(ge).lower()
                        if "resource_exhausted" in err_str or "quota" in err_str or "429" in err_str:
                            raise QuotaExhaustedError("Google Gemini API quota or rate limit exceeded. Please try again later or add Gemini API key.")
                        logger.warning(f"Gemini SDK generate_content with {g_model} failed: {ge}")
                        last_error = ge
            except QuotaExhaustedError:
                raise
            except Exception as e:
                logger.warning(f"Gemini SDK error, using REST fallback: {e}")
                last_error = e

        # REST API fallback
        for g_model in candidate_models:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{g_model}:generateContent?key={key}"
            payload = {"contents": [{"parts": [{"text": prompt}]}]}
            try:
                resp = requests.post(url, json=payload, timeout=20)
                if resp.status_code == 200:
                    data = resp.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        if parts:
                            return parts[0].get("text", "").strip()
                elif resp.status_code == 429:
                    raise QuotaExhaustedError("Google Gemini API quota or rate limit exceeded. Please try again later.")
                else:
                    logger.warning(f"Gemini REST endpoint {g_model} returned status {resp.status_code}: {resp.text}")
                    last_error = f"HTTP {resp.status_code}: {resp.text}"
            except QuotaExhaustedError:
                raise
            except Exception as re:
                logger.warning(f"Gemini REST endpoint error for {g_model}: {re}")
                last_error = re

        raise LLMProviderError(f"Failed to generate response using Gemini API ({last_error}).")

    def get_embedding(self, text: str, api_key: str | None = None) -> list[float]:
        key = self._get_api_key(api_key)
        if not key:
            raise ValueError("Gemini API key missing for embedding calculation.")

        embed_candidates = ["text-embedding-004", "gemini-embedding-001", "gemini-embedding-2"]

        if genai:
            try:
                client = genai.Client(api_key=key)
                for embed_model in embed_candidates:
                    try:
                        res = client.models.embed_content(
                            model=embed_model,
                            contents=text,
                            config=types.EmbedContentConfig(output_dimensionality=1536),
                        )
                        if res:
                            vals = None
                            if hasattr(res, "embeddings") and res.embeddings:
                                vals = res.embeddings[0].values
                            elif hasattr(res, "embedding") and res.embedding:
                                vals = getattr(res.embedding, "values", None)
                            if vals:
                                return list(vals)
                    except Exception as e:
                        logger.debug(f"Gemini embed_content with {embed_model} failed: {e}")
            except Exception as e:
                logger.warning(f"Gemini SDK embedding failed, trying REST: {e}")

        # REST fallback
        for embed_model in embed_candidates:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{embed_model}:embedContent?key={key}"
            payload = {
                "model": f"models/{embed_model}",
                "content": {"parts": [{"text": text}]},
                "outputDimensionality": 1536,
            }
            try:
                resp = requests.post(url, json=payload, timeout=10)
                if resp.status_code == 200:
                    data = resp.json()
                    vals = data.get("embedding", {}).get("values")
                    if vals:
                        return list(vals)
            except Exception as e:
                logger.warning(f"Gemini embedding REST failed: {e}")

        raise LLMProviderError("Failed to fetch vector embedding from Gemini API.")
