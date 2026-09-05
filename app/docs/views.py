from pgvector.django import CosineDistance
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response

from .models import Document, DocumentChunk
from .serializers import DocumentChunkSerializer, DocumentSerializer
from .services import process_and_store_document


class DocumentViewSet(viewsets.ModelViewSet):
  serializer_class = DocumentSerializer
  parser_classes = (MultiPartParser, FormParser)  # Enables file upload handling

  def get_queryset(self):
    queryset = Document.objects.all().order_by("-uploaded_at")
    session_id = self.request.query_params.get("session")
    if session_id:
      queryset = queryset.filter(session_id=session_id)
    return queryset

  def perform_create(self, serializer):
    title = serializer.validated_data.get("title")
    file_obj = serializer.validated_data.get("file")
    if not title and file_obj:
      title = file_obj.name

    session_val = self.request.data.get("session")
    session_obj = serializer.validated_data.get("session")

    if not session_obj and session_val:
      from app.chat.models import ChatSession
      try:
        session_obj, _ = ChatSession.objects.get_or_create(id=session_val)
      except Exception:
        session_obj = None

    kwargs = {"title": title or "Untitled Document"}
    if session_obj:
      kwargs["session"] = session_obj

    instance = serializer.save(**kwargs)
    process_and_store_document(instance)

  @action(detail=False, methods=["post"], url_path="search")
  def vector_search(self, request):
    """Custom endpoint to perform similarity search on chunks.

    Expects body: {"embedding": [0.012, -0.043, ...]}
    """
    query_embedding = request.data.get("embedding")
    if not query_embedding:
      return Response(
          {"error": "Embedding array is required"},
          status=status.HTTP_400_BAD_REQUEST,
      )

    top_chunks = (
        DocumentChunk.objects.annotate(
            distance=CosineDistance("embedding", query_embedding)
        )
        .order_by("distance")[:5]
    )

    serializer = DocumentChunkSerializer(top_chunks, many=True)
    return Response(serializer.data)