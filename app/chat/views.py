from rest_framework import status, viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import ChatSession, Message, AIModel, UserAIConfig
from .serializers import (
    ChatSessionSerializer,
    MessageSerializer,
    AIModelSerializer,
    UserAIConfigSerializer,
)
from app.docs.services import generate_rag_response


DEFAULT_MODELS_DATA = [
    {
        "model_id": "gemini-3.6-flash",
        "name": "Gemini 3.6 Flash",
        "provider": "gemini",
        "provider_name": "Google Gemini",
        "description": "Fast, highly performant default AI model by Google (Built-in, no API key required)",
        "is_default": True,
        "requires_api_key": False,
    },
    {
        "model_id": "gemini-1.5-pro",
        "name": "Gemini 1.5 Pro",
        "provider": "gemini",
        "provider_name": "Google Gemini",
        "description": "Advanced reasoning with high quality responses",
        "is_default": False,
        "requires_api_key": False,
    },
    {
        "model_id": "gpt-4o",
        "name": "GPT-4o",
        "provider": "openai",
        "provider_name": "OpenAI ChatGPT",
        "description": "Flagship intelligence model for multimodal tasks",
        "is_default": False,
        "requires_api_key": True,
    },
    {
        "model_id": "gpt-4o-mini",
        "name": "GPT-4o Mini",
        "provider": "openai",
        "provider_name": "OpenAI ChatGPT",
        "description": "Lightweight and efficient OpenAI model",
        "is_default": False,
        "requires_api_key": True,
    },
    {
        "model_id": "claude-3-5-sonnet",
        "name": "Claude 3.5 Sonnet",
        "provider": "claude",
        "provider_name": "Anthropic Claude",
        "description": "State-of-the-art reasoning and coding performance",
        "is_default": False,
        "requires_api_key": True,
    },
    {
        "model_id": "deepseek-chat",
        "name": "DeepSeek V3",
        "provider": "deepseek",
        "provider_name": "DeepSeek AI",
        "description": "High efficiency open-weights baseline model",
        "is_default": False,
        "requires_api_key": True,
    },
]


def ensure_default_models():
    """Populates AIModel table if empty."""
    try:
        if not AIModel.objects.exists():
            for mdata in DEFAULT_MODELS_DATA:
                AIModel.objects.create(**mdata)
    except Exception:
        pass


class AIModelViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet to list available AI models and details."""
    queryset = AIModel.objects.all()
    serializer_class = AIModelSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        ensure_default_models()
        return AIModel.objects.all().order_by("-is_default", "provider_name", "name")


class UserAIConfigViewSet(viewsets.ViewSet):
    """ViewSet for fetching and updating user AI preferences & API keys."""
    permission_classes = [permissions.AllowAny]

    def list(self, request):
        user = request.user if request.user.is_authenticated else None
        if user:
            config, _ = UserAIConfig.objects.get_or_create(user=user)
            serializer = UserAIConfigSerializer(config)
            return Response(serializer.data)
        return Response({
            "selected_model_id": "gemini-3.6-flash",
            "api_keys": {},
        })

    def create(self, request):
        user = request.user if request.user.is_authenticated else None
        model_id = request.data.get("selected_model_id")
        api_keys = request.data.get("api_keys", {})

        selected_model = None
        if model_id:
            ensure_default_models()
            selected_model = AIModel.objects.filter(model_id=model_id).first()

        if user:
            config, _ = UserAIConfig.objects.get_or_create(user=user)
            if selected_model:
                config.selected_model = selected_model
            if isinstance(api_keys, dict):
                config.api_keys.update(api_keys)
            config.save()
            return Response(UserAIConfigSerializer(config).data)

        return Response({
            "selected_model_id": model_id or "gemini-3.6-flash",
            "api_keys": api_keys,
            "message": "Saved locally in session",
        })


class ChatSessionViewSet(viewsets.ModelViewSet):
    serializer_class = ChatSessionSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            return ChatSession.objects.filter(user=user).order_by("-updated_at")
        if getattr(self, "action", None) == "list":
            return ChatSession.objects.none()
        return ChatSession.objects.filter(user__isnull=True).order_by("-updated_at")

    def perform_create(self, serializer):
        user = self.request.user if self.request.user.is_authenticated else None
        serializer.save(user=user)

    @action(detail=True, methods=["get"], url_path="messages")
    def list_messages(self, request, pk=None):
        """Paginated endpoint to fetch messages for a session.
        Query Params:
          - limit: max messages to return (default 20, max 100)
          - before_id: fetch messages created before the message with this ID
        """
        try:
            session = self.get_object()
        except Exception:
            user = request.user if request.user.is_authenticated else None
            session = ChatSession.objects.filter(id=pk, user=user).first()
            if not session and not request.user.is_authenticated:
                session = ChatSession.objects.filter(id=pk, user__isnull=True).first()
            if not session:
                return Response({"error": "Session not found"}, status=status.HTTP_404_NOT_FOUND)

        try:
            limit = int(request.query_params.get("limit", 20))
            limit = max(1, min(limit, 100))
        except (ValueError, TypeError):
            limit = 20

        before_id = request.query_params.get("before_id")

        qs = Message.objects.filter(session=session)
        if before_id:
            try:
                before_msg = Message.objects.filter(id=before_id, session=session).first()
                if before_msg:
                    qs = qs.filter(created_at__lt=before_msg.created_at)
            except Exception:
                pass

        total_count = Message.objects.filter(session=session).count()
        messages_list = list(qs.order_by("-created_at")[: limit + 1])

        has_more = len(messages_list) > limit
        if has_more:
            messages_list = messages_list[:limit]

        # Reverse back to chronological order (oldest first)
        messages_list.reverse()

        serializer = MessageSerializer(messages_list, many=True)
        return Response({
            "results": serializer.data,
            "has_more": has_more,
            "total_count": total_count,
        })

    @action(detail=True, methods=["post"], url_path="send-message")
    def send_message(self, request, pk=None):
        """Custom endpoint to send a user message and trigger RAG pipeline."""
        try:
            session = self.get_object()
        except Exception:
            user = request.user if request.user.is_authenticated else None
            session, _ = ChatSession.objects.get_or_create(id=pk, defaults={"user": user})

        user_content = request.data.get("content")

        if not user_content:
            return Response(
                {"error": "Message content is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 1. Save user message
        user_msg = Message.objects.create(
            session=session, role="user", content=user_content
        )

        model_name = request.data.get("model")
        api_key_val = request.data.get("api_key")

        # 2. Call RAG pipeline (vector search in pgvector -> generate LLM/context response)
        assistant_reply_text = generate_rag_response(
            session, user_content, model_name=model_name, api_key=api_key_val
        )

        # 3. Save assistant message
        assistant_msg = Message.objects.create(
            session=session, role="assistant", content=assistant_reply_text
        )

        return Response(
            {
                "user_message": MessageSerializer(user_msg).data,
                "assistant_message": MessageSerializer(assistant_msg).data,
            },
            status=status.HTTP_201_CREATED,
        )