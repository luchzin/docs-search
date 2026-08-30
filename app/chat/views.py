from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import ChatSession, Message
from .serializers import ChatSessionSerializer, MessageSerializer


class ChatSessionViewSet(viewsets.ModelViewSet):
  queryset = ChatSession.objects.all().order_by("-updated_at")
  serializer_class = ChatSessionSerializer

  @action(detail=True, methods=["post"], url_path="send-message")
  def send_message(self, request, pk=None):
    """Custom endpoint to send a user message and trigger RAG pipeline."""
    session = self.get_object()
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

    # 2. TODO: Call your RAG service here (search pgvector chunks -> call LLM)
    assistant_reply_text = (
        f"Echo response to: '{user_content}'. Replace with LLM logic."
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