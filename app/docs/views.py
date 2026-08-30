from pgvector.django import CosineDistance
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response

from .models import Document, DocumentChunk
from .serializers import DocumentChunkSerializer, DocumentSerializer


class DocumentViewSet(viewsets.ModelViewSet):
  queryset = Document.objects.all().order_by("-uploaded_at")
  serializer_class = DocumentSerializer
  parser_classes = (MultiPartParser, FormParser)  # Enables file upload handling

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