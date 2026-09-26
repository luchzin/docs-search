import os
import math
import hashlib
import logging
from django.conf import settings
from pgvector.django import CosineDistance
from .models import Document, DocumentChunk
from app.chat.ai_services.factory import LLMFactory
from app.chat.ai_services.base import QuotaExhaustedError, LLMProviderError

logger = logging.getLogger(__name__)

try:
    import pypdf
except ImportError:
    pypdf = None

try:
    import docx
except ImportError:
    docx = None


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


def get_embedding(text: str, model_name: str | None = None, api_key: str | None = None) -> list[float]:
    """Generates 1536-dimensional vector embedding using the configured modular LLM provider."""
    try:
        provider = LLMFactory.get_provider(model_name)
        return provider.get_embedding(text, api_key=api_key)
    except Exception as e:
        logger.debug(f"Selected provider get_embedding failed ({e}); trying Gemini system default embedding.")
        try:
            from app.chat.ai_services.gemini_provider import GeminiProvider
            return GeminiProvider(model_id="gemini-3.6-flash").get_embedding(text)
        except Exception as ge:
            logger.warning(f"Gemini fallback embedding failed ({ge}), using deterministic fallback.")
            return _generate_deterministic_embedding(text, dim=1536)


def extract_pages_from_document(file_path: str) -> list[tuple[int, str]]:
    """Extracts text per page/section from PDF, DOCX, TXT, MD, CSV, JSON, or LOG files."""
    pages = []
    if not os.path.exists(file_path):
        return pages

    ext = os.path.splitext(file_path)[1].lower()

    # 1. PDF Documents
    if ext == ".pdf":
        if pypdf:
            try:
                reader = pypdf.PdfReader(file_path)
                for idx, page in enumerate(reader.pages, start=1):
                    text = page.extract_text() or ""
                    if text.strip():
                        pages.append((idx, text.strip()))
            except Exception as e:
                logger.error(f"Error reading PDF with pypdf: {e}")

    # 2. Word Documents (.docx)
    elif ext == ".docx":
        if docx:
            try:
                doc = docx.Document(file_path)
                text_blocks = []
                # Extract paragraph text
                for p in doc.paragraphs:
                    if p.text.strip():
                        text_blocks.append(p.text.strip())
                # Extract table cell text
                for table in doc.tables:
                    for row in table.rows:
                        row_text = " | ".join(cell.text.strip() for cell in row.cells if cell.text.strip())
                        if row_text:
                            text_blocks.append(row_text)

                if text_blocks:
                    current_page = []
                    current_len = 0
                    page_idx = 1
                    for block in text_blocks:
                        current_page.append(block)
                        current_len += len(block)
                        if current_len >= 1500:
                            pages.append((page_idx, "\n".join(current_page)))
                            page_idx += 1
                            current_page = []
                            current_len = 0
                    if current_page:
                        pages.append((page_idx, "\n".join(current_page)))
            except Exception as e:
                logger.error(f"Error reading DOCX with python-docx: {e}")

        # ZIP XML fallback for DOCX text extraction (handles text frames, headers, tables, etc.)
        if not pages:
            try:
                import zipfile
                import xml.etree.ElementTree as ET
                with zipfile.ZipFile(file_path) as z:
                    xml_content = z.read("word/document.xml")
                    tree = ET.fromstring(xml_content)
                    texts = [node.text for node in tree.iter() if node.tag.endswith("}t") and node.text]
                    full_text = " ".join(texts).strip()
                    if full_text:
                        page_size = 2000
                        for page_idx, start_pos in enumerate(range(0, len(full_text), page_size), start=1):
                            pages.append((page_idx, full_text[start_pos : start_pos + page_size]))
            except Exception as ze:
                logger.error(f"ZIP XML fallback reading DOCX failed: {ze}")

    # 3. Text, Markdown, CSV, JSON, LOG, or Fallback
    if not pages:
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                raw_text = f.read().strip()
                if raw_text:
                    page_size = 2000
                    for page_idx, start_pos in enumerate(range(0, len(raw_text), page_size), start=1):
                        pages.append((page_idx, raw_text[start_pos : start_pos + page_size]))
        except Exception as e:
            logger.error(f"Error reading file as text fallback: {e}")

    return pages


def extract_pages_from_pdf(file_path: str) -> list[tuple[int, str]]:
    """Alias for backwards compatibility."""
    return extract_pages_from_document(file_path)


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
    pages = extract_pages_from_document(file_path)

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
    """Executes RAG pipeline: embeds user query, searches pgvector, and generates response via modular LLM provider."""
    provider = LLMFactory.get_provider(model_name)
    query_embedding = get_embedding(user_query, model_name=model_name, api_key=api_key)

    # 1. Fetch active session documents and titles in order
    session_docs = Document.objects.filter(session=session) if session else Document.objects.none()
    if not session_docs.exists():
        session_docs = Document.objects.all()

    doc_list_by_order = list(session_docs.order_by("uploaded_at"))

    # Auto re-index documents if they are missing chunks or contain only dummy placeholder chunks
    for doc in doc_list_by_order:
        if doc.file and os.path.exists(doc.file.path):
            existing_chunks = list(doc.chunks.all())
            is_placeholder = (
                len(existing_chunks) == 0 or
                (len(existing_chunks) == 1 and existing_chunks[0].content.strip() == f"Document: {doc.title}".strip())
            )
            if is_placeholder:
                logger.info(f"Auto re-indexing document '{doc.title}' (ID {doc.id}) to extract full content chunks.")
                process_and_store_document(doc)

    chunk_qs = DocumentChunk.objects.filter(document__session=session) if session else DocumentChunk.objects.none()
    if not chunk_qs.exists():
        chunk_qs = DocumentChunk.objects.all()

    if not chunk_qs.exists():
        return "No document chunks available in the database. Please upload a document first."

    query_lower = user_query.lower()
    target_doc = None

    # 2. Check if user query matches a document title directly
    for doc in doc_list_by_order:
        if doc.title and (doc.title.lower() in query_lower or os.path.splitext(doc.title)[0].lower() in query_lower):
            target_doc = doc
            break

    # 3. Check for ordinal or positional references (e.g. "second file", "2nd document", "file 2", "latest file")
    if not target_doc and len(doc_list_by_order) >= 2:
        if any(w in query_lower for w in ["second file", "2nd file", "second document", "2nd document", "file 2", "document 2"]):
            target_doc = doc_list_by_order[1]
        elif any(w in query_lower for w in ["first file", "1st file", "first document", "1st document", "file 1", "document 1"]):
            target_doc = doc_list_by_order[0]
        elif any(w in query_lower for w in ["third file", "3rd file", "third document", "3rd document", "file 3", "document 3"]) and len(doc_list_by_order) >= 3:
            target_doc = doc_list_by_order[2]
        elif any(w in query_lower for w in ["latest file", "last file", "newest file", "new file", "latest document", "last document"]):
            target_doc = doc_list_by_order[-1]

    # 4. Retrieve context chunks
    top_chunks = []
    if target_doc:
        # User specified or targeted a specific document — load rich context from target_doc
        target_chunks = list(
            DocumentChunk.objects.filter(document=target_doc)
            .annotate(distance=CosineDistance("embedding", query_embedding))
            .order_by("distance")[:6]
        )
        if not target_chunks:
            target_chunks = list(DocumentChunk.objects.filter(document=target_doc)[:6])

        other_chunks = list(
            chunk_qs.exclude(document=target_doc)
            .annotate(distance=CosineDistance("embedding", query_embedding))
            .order_by("distance")[:4]
        )
        top_chunks = target_chunks + other_chunks
    else:
        # General or multi-document query — perform balanced retrieval across ALL session documents
        chunks_per_doc = max(3, 10 // max(1, len(doc_list_by_order)))
        for doc in doc_list_by_order:
            doc_chunks = list(
                DocumentChunk.objects.filter(document=doc)
                .annotate(distance=CosineDistance("embedding", query_embedding))
                .order_by("distance")[:chunks_per_doc]
            )
            if not doc_chunks:
                doc_chunks = list(DocumentChunk.objects.filter(document=doc)[:chunks_per_doc])
            top_chunks.extend(doc_chunks)

    context_text = "\n\n".join(
        f"[Document: {c.document.title}, Page {c.page_number or 1}]\n{c.content}"
        for c in top_chunks
    )

    doc_list_str = "\n".join([f"  {idx+1}. {doc.title}" for idx, doc in enumerate(doc_list_by_order)])

    prompt = (
        "You are an AI assistant helping with document search, analysis, and retrieval.\n"
        f"Available Documents in this Chat Session ({len(doc_list_by_order)} total):\n"
        f"{doc_list_str}\n\n"
        "Instructions:\n"
        "- Answer the user's question accurately using the provided document context below.\n"
        "- When the user asks about a specific file (e.g. 'second file', '2nd document', or by title), refer to its content in the context.\n"
        "- Include the relevant document title(s) in your response as source references.\n\n"
        f"Context:\n{context_text}\n\n"
        f"User Question: {user_query}\nAnswer:"
    )

    try:
        return provider.generate_response(prompt, api_key=api_key)
    except QuotaExhaustedError as qe:
        logger.warning(f"Quota exhausted error for model '{model_name}': {qe}")
        return f"⚠️ **API Quota / Token Error**\n\nYou have no API tokens or credits remaining for the selected model ({model_name or 'selected AI model'}). Please add credits to your API account or switch to the default **Google Gemini AI**."
    except Exception as e:
        err_text = str(e).lower()
        if any(keyword in err_text for keyword in ["insufficient_quota", "credit_balance_exhausted", "quota", "credit", "429", "no credits"]):
            logger.warning(f"Quota error detected for model '{model_name}': {e}")
            return f"⚠️ **API Quota / Token Error**\n\nYou have no API tokens or credits remaining for the selected model ({model_name or 'selected AI model'}). Please add credits to your API account or switch to the default **Google Gemini AI**."

        logger.error(f"Provider generate_response failed ({e}).")
        return f"⚠️ **AI Agent Error**\n\nSomething went wrong while processing your request. The AI agent could not process the work right now. Please try again or select another AI model."
