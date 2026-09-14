from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from app.chat.models import AIModel, UserAIConfig, ChatSession
from app.docs.models import Document, DocumentChunk
from app.chat.ai_services.factory import LLMFactory
from app.chat.ai_services.gemini_provider import GeminiProvider
from app.chat.ai_services.openai_provider import OpenAIProvider
from app.chat.ai_services.claude_provider import ClaudeProvider
from app.chat.ai_services.deepseek_provider import DeepSeekProvider
from app.chat.ai_services.base import QuotaExhaustedError
from app.docs.services import generate_rag_response
from unittest.mock import patch


class AIModelBackendTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.session = ChatSession.objects.create(title="Test Session")
        self.doc = Document.objects.create(session=self.session, title="Test Doc")
        self.chunk = DocumentChunk.objects.create(
            document=self.doc,
            content="Sample text content for RAG search.",
            chunk_index=0,
            embedding=[0.1] * 1536,
        )

    def test_llm_factory_providers(self):
        gemini_p = LLMFactory.get_provider("gemini-3.6-flash")
        self.assertIsInstance(gemini_p, GeminiProvider)

        openai_p = LLMFactory.get_provider("gpt-4o")
        self.assertIsInstance(openai_p, OpenAIProvider)

        claude_p = LLMFactory.get_provider("claude-3-5-sonnet")
        self.assertIsInstance(claude_p, ClaudeProvider)

        deepseek_p = LLMFactory.get_provider("deepseek-chat")
        self.assertIsInstance(deepseek_p, DeepSeekProvider)

    def test_models_api_endpoint(self):
        res = self.client.get("/api/v1/models/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        data = res.json()
        self.assertTrue(len(data) >= 6)
        
        # Verify gemini default model
        gemini_model = next((m for m in data if m["model_id"] == "gemini-3.6-flash"), None)
        self.assertIsNotNone(gemini_model)
        self.assertTrue(gemini_model["is_default"])
        self.assertFalse(gemini_model["requires_api_key"])

    def test_ai_config_api_endpoint(self):
        res = self.client.get("/api/v1/ai-config/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        post_data = {
            "selected_model_id": "gpt-4o",
            "api_keys": {"openai": "sk-test-key-12345"},
        }
        res_post = self.client.post("/api/v1/ai-config/", post_data, format="json")
        self.assertEqual(res_post.status_code, status.HTTP_200_OK)

    @patch.object(OpenAIProvider, "generate_response")
    def test_quota_exhausted_error_handling(self, mock_gen):
        mock_gen.side_effect = QuotaExhaustedError("Insufficient quota on OpenAI account.")
        reply = generate_rag_response(self.session, "What is this?", model_name="gpt-4o")
        self.assertIn("API Quota / Token Error", reply)

    @patch.object(OpenAIProvider, "generate_response")
    def test_general_agent_error_handling(self, mock_gen):
        mock_gen.side_effect = RuntimeError("Generic connection timeout")
        reply = generate_rag_response(self.session, "What is this?", model_name="gpt-4o")
        self.assertIn("AI Agent Error", reply)

    def test_messages_pagination(self):
        from app.chat.models import Message
        import time
        # Create 25 messages in session
        created_msgs = []
        for i in range(25):
            msg = Message.objects.create(
                session=self.session,
                role="user" if i % 2 == 0 else "assistant",
                content=f"Message {i+1}",
            )
            created_msgs.append(msg)

        # Fetch first page (limit=10)
        res = self.client.get(f"/api/v1/chat/{self.session.id}/messages/?limit=10")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        data = res.json()
        self.assertEqual(len(data["results"]), 10)
        self.assertTrue(data["has_more"])
        self.assertEqual(data["total_count"], 25)
        # Results should be newest 10 messages (i=15..24), in chronological order
        self.assertEqual(data["results"][-1]["content"], "Message 25")
        self.assertEqual(data["results"][0]["content"], "Message 16")

        # Fetch second page using before_id = ID of Message 16
        first_msg_id = data["results"][0]["id"]
        res_page2 = self.client.get(f"/api/v1/chat/{self.session.id}/messages/?limit=10&before_id={first_msg_id}")
        self.assertEqual(res_page2.status_code, status.HTTP_200_OK)
        data2 = res_page2.json()
        self.assertEqual(len(data2["results"]), 10)
        self.assertTrue(data2["has_more"])
        self.assertEqual(data2["results"][-1]["content"], "Message 15")
        self.assertEqual(data2["results"][0]["content"], "Message 6")
