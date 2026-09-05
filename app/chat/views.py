from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import ChatSession, Message
from .serializers import ChatSessionSerializer, MessageSerializer
from app.docs.services import generate_rag_response


class ChatSessionViewSet(viewsets.ModelViewSet):
  serializer_class = ChatSessionSerializer

  def get_queryset(self):
    user = self.request.user
    if user.is_authenticated:
      return ChatSession.objects.filter(user=user).order_by("-updated_at")
    return ChatSession.objects.filter(user__isnull=True).order_by("-updated_at")

  def perform_create(self, serializer):
    user = self.request.user
    if user.is_authenticated:
      serializer.save(user=user)
    else:
      serializer.save()

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

    # 2. Call RAG pipeline (vector search in pgvector -> generate LLM/context response)
    assistant_reply_text = generate_rag_response(session, user_content)

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