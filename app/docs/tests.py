import os
from tempfile import NamedTemporaryFile
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient
from app.chat.models import ChatSession, Message
from app.docs.models import Document, DocumentChunk
from app.docs.services import (
    _generate_deterministic_embedding,
    get_embedding,
    chunk_text,
    process_and_store_document,
    generate_rag_response,
)


class DocumentRagTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.session = ChatSession.objects.create(title="Test Chat Session")

    def test_deterministic_embedding_dimension(self):
        vec = _generate_deterministic_embedding("Hello world PDF test")
        self.assertEqual(len(vec), 1536)
        self.assertAlmostEqual(sum(v * v for v in vec), 1.0, places=3)

    def test_get_embedding(self):
        vec = get_embedding("Document retrieval query")
        self.assertEqual(len(vec), 1536)

    def test_chunk_text(self):
        pages = [(1, "Page one text content " * 30), (2, "Page two text content " * 20)]
        chunks = chunk_text(pages, chunk_size=200, overlap=50)
        self.assertGreater(len(chunks), 1)
        self.assertEqual(chunks[0]["page_number"], 1)

    def test_document_upload_and_chunk_creation(self):
        # Create dummy text PDF
        dummy_file = SimpleUploadedFile("sample_report.txt", b"Quantum computing is a rapidly-emerging technology that harnesses the laws of quantum mechanics to solve problems too complex for classical computers. Key concepts include qubits, superposition, and quantum entanglement.")
        
        response = self.client.post(
            "/api/v1/documents/",
            {
                "file": dummy_file,
                "title": "Quantum Computing Specs",
                "session": str(self.session.id),
            },
            format="multipart"
        )
        self.assertEqual(response.status_code, 201)
        
        doc_id = response.data["id"]
        document = Document.objects.get(id=doc_id)
        
        # Verify chunks created in pgvector
        chunks = DocumentChunk.objects.filter(document=document)
        self.assertGreater(chunks.count(), 0)
        first_chunk = chunks.first()
        self.assertIsNotNone(first_chunk.embedding)
        self.assertEqual(len(first_chunk.embedding), 1536)

    def test_send_message_rag_pipeline(self):
        # Create document with chunks
        doc = Document.objects.create(session=self.session, title="Annual Report")
        DocumentChunk.objects.create(
            document=doc,
            chunk_index=0,
            page_number=1,
            content="The annual revenue increased by 25% due to high market demand for AI products.",
            embedding=get_embedding("The annual revenue increased by 25% due to high market demand for AI products.")
        )

        response = self.client.post(
            f"/api/v1/chat/{self.session.id}/send-message/",
            {"content": "How much did annual revenue increase?"},
            format="json"
        )
        self.assertEqual(response.status_code, 201)
        self.assertIn("user_message", response.data)
        self.assertIn("assistant_message", response.data)
        
        assistant_content = response.data["assistant_message"]["content"]
        self.assertTrue(len(assistant_content) > 0)
        self.assertIn("Annual Report", assistant_content)
