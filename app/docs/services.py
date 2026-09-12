import os
import math
import hashlib
import logging
import requests
from django.conf import settings
from pgvector.django import CosineDistance
from .models import Document, DocumentChunk

logger = logging.getLogger(__name__)

try:
    import pypdf
except ImportError:
    pypdf = None

try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None

try:
    import openai
except ImportError:
    openai = None


def get_gemini_api_key() -> str | None:
    return (
        getattr(settings, "GEMINI_API_KEY", None)
        or getattr(settings, "GOOGLE_API_KEY", None)
        or os.environ.get("GEMINI_API_KEY")
        or os.environ.get("GOOGLE_API_KEY")
    )


def _generate_deterministic_embedding(text: str, dim: int = 1536) -> list[float]:
    """Generates a deterministic unit vector embedding (1536 dims) for fallback usage."""
    vec = [0.0] * dim
    words = text.lower().split()
    if not words:
        words = ["empty"]

    for word in words:
        h = int(hashlib.md5(word.encode("utf-8")).hexdigest(), 16)
        idx1 = h % dim
        idx2 = (h >> 16) % dim
        idx3 = (h >> 32) % dim
        vec[idx1] += 1.0
        vec[idx2] += 0.5
        vec[idx3] += 0.25

    text_hash = int(hashlib.sha256(text.encode("utf-8")).hexdigest(), 16)
    for i in range(min(16, dim)):
        val = ((text_hash >> (i * 4)) & 0xF) / 15.0 - 0.5
        vec[i] += val

    norm = math.sqrt(sum(v * v for v in vec))
    if norm > 0:
        vec = [v / norm for v in vec]
    else:
        vec[0] = 1.0
    return vec


def get_embedding(text: str, api_key: str | None = None) -> list[float]:
    """Generates 1536-dimensional vector embedding using Gemini API, OpenAI API, or fallback."""
    gemini_key = api_key or get_gemini_api_key()
    if gemini_key:
        try:
            if genai:
                client = genai.Client(api_key=gemini_key)
                for embed_model in ["gemini-embedding-001", "gemini-embedding-2", "text-embedding-004"]:
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

            # REST fallback for Gemini Embeddings API
            for embed_model in ["gemini-embedding-001", "gemini-embedding-2", "text-embedding-004"]:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{embed_model}:embedContent?key={gemini_key}"
                payload = {
                    "model": f"models/{embed_model}",
                    "content": {"parts": [{"text": text}]},
                    "outputDimensionality": 1536,
                }
                resp = requests.post(url, json=payload, timeout=10)
                if resp.status_code == 200:
                    data = resp.json()
                    vals = data.get("embedding", {}).get("values")
                    if vals:
                        return list(vals)
            logger.warning("Gemini embedding REST response non-200")
        except Exception as e:
            logger.warning(f"Gemini embedding API failed, checking OpenAI / fallback: {e}")

    openai_key = getattr(settings, "OPENAI_API_KEY", None) or os.environ.get("OPENAI_API_KEY")
    if openai_key and openai:
        try:
            client = openai.OpenAI(api_key=openai_key)
            response = client.embeddings.create(
                input=text,
                model="text-embedding-3-small"
            )
            return response.data[0].embedding
        except Exception as e:
            logger.warning(f"OpenAI embedding API failed, falling back: {e}")

    return _generate_deterministic_embedding(text, dim=1536)


def extract_pages_from_pdf(file_path: str) -> list[tuple[int, str]]:
    """Extracts text per page from a PDF file. Returns list of (page_number, text)."""
    pages = []
    if pypdf and os.path.exists(file_path):
        try:
            reader = pypdf.PdfReader(file_path)
            for idx, page in enumerate(reader.pages, start=1):
                text = page.extract_text() or ""
                if text.strip():
                    pages.append((idx, text.strip()))
        except Exception as e:
            logger.error(f"Error reading PDF with pypdf: {e}")

    if not pages and os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                raw_text = f.read().strip()
                if raw_text:
                    pages.append((1, raw_text))
        except Exception as e:
            logger.error(f"Error reading file as text fallback: {e}")

    return pages


def chunk_text(pages: list[tuple[int, str]], chunk_size: int = 600, overlap: int = 150) -> list[dict]:
    """Splits page texts into chunks with chunk_index, page_number, and content."""
    chunks = []
    global_chunk_idx = 0

    for page_num, page_text in pages:
        if len(page_text) <= chunk_size:
            chunks.append({
                "chunk_index": global_chunk_idx,
                "page_number": page_num,
                "content": page_text,
            })
            global_chunk_idx += 1
        else:
            start = 0
            while start < len(page_text):
                end = start + chunk_size
                chunk_content = page_text[start:end]
                chunks.append({
                    "chunk_index": global_chunk_idx,
                    "page_number": page_num,
                    "content": chunk_content,
                })
                global_chunk_idx += 1
                start += (chunk_size - overlap)

    return chunks


def process_and_store_document(document: Document) -> list[DocumentChunk]:
    """Extracts text from document file, chunks it, generates embeddings, and saves to pgvector."""
    if not document.file:
        return []

    file_path = document.file.path
    pages = extract_pages_from_pdf(file_path)

    if not pages:
        pages = [(1, f"Document: {document.title}")]

    raw_chunks = chunk_text(pages)
    
    document.chunks.all().delete()

    created_chunks = []
    for chunk_data in raw_chunks:
        embedding = get_embedding(chunk_data["content"])
        chunk_obj = DocumentChunk.objects.create(
            document=document,
            chunk_index=chunk_data["chunk_index"],
            page_number=chunk_data["page_number"],
            content=chunk_data["content"],
            embedding=embedding,
        )
        created_chunks.append(chunk_obj)

    logger.info(f"Processed document '{document.title}': created {len(created_chunks)} chunks in pgvector.")
    return created_chunks


def generate_rag_response(session, user_query: str, model_name: str | None = None, api_key: str | None = None) -> str:
    """Executes RAG pipeline: embeds user query, searches pgvector, and generates response via Gemini/OpenAI/Synthesizer."""
    query_embedding = get_embedding(user_query, api_key=api_key)

    chunk_qs = DocumentChunk.objects.filter(document__session=session)
    if not chunk_qs.exists():
        chunk_qs = DocumentChunk.objects.all()

    if not chunk_qs.exists():
        return "No document chunks available in the database. Please upload a PDF document first."

    top_chunks = (
        chunk_qs.annotate(distance=CosineDistance("embedding", query_embedding))
        .order_by("distance")[:5]
    )

    context_text = "\n\n".join(
        f"[Document: {c.document.title}, Page {c.page_number or 1}]\n{c.content}"
        for c in top_chunks
    )
    prompt = (
        "You are an AI assistant helping with document search and retrieval.\n"
        "Answer the user's question accurately using ONLY the provided document context below.\n"
        "Include the document title in your response as the source reference.\n\n"
        f"Context:\n{context_text}\n\n"
        f"User Question: {user_query}\nAnswer:"
    )

    gemini_key = api_key or get_gemini_api_key()
    target_gemini_model = model_name if (model_name and "gemini" in model_name) else "gemini-3.6-flash"

    if gemini_key:
        try:
            if genai:
                client = genai.Client(api_key=gemini_key)
                for g_model in [target_gemini_model, "gemini-3.6-flash", "gemini-2.5-flash"]:
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
                        logger.debug(f"Gemini generate_content with {g_model} failed: {ge}")

            # REST fallback for Gemini Generation API
            for g_model in [target_gemini_model, "gemini-3.6-flash", "gemini-2.5-flash"]:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{g_model}:generateContent?key={gemini_key}"
                payload = {"contents": [{"parts": [{"text": prompt}]}]}
                resp = requests.post(url, json=payload, timeout=15)
                if resp.status_code == 200:
                    data = resp.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        if parts:
                            return parts[0].get("text", "").strip()
            logger.warning("Gemini generation REST response non-200")
        except Exception as e:
            logger.warning(f"Gemini generation API failed, checking OpenAI / fallback: {e}")

    openai_key = getattr(settings, "OPENAI_API_KEY", None) or os.environ.get("OPENAI_API_KEY")
    if openai_key and openai:
        try:
            client = openai.OpenAI(api_key=openai_key)
            target_openai_model = model_name if (model_name and "gpt" in model_name) else "gpt-4o-mini"
            res = client.chat.completions.create(
                model=target_openai_model,
                messages=[
                    {"role": "system", "content": "You are a helpful document retrieval assistant."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
            )
            return res.choices[0].message.content.strip()
        except Exception as e:
            logger.warning(f"OpenAI chat completion failed, falling back to local synthesizer: {e}")

    sources_summary = "\n".join(f"- Document: {c.document.title} (Page {c.page_number or 1}): {c.content}" for c in top_chunks)
    reply = f"Based on the relevant documents:\n\n{sources_summary}"
    return reply
