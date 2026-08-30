from rest_framework import serializers
from .models import Document, DocumentChunk


class DocumentChunkSerializer(serializers.ModelSerializer):

  class Meta:
    model = DocumentChunk
    fields = ["id", "content", "page_number", "chunk_index"]


class DocumentSerializer(serializers.ModelSerializer):
  chunks = DocumentChunkSerializer(many=True, read_only=True)

  class Meta:
    model = Document
    fields = ["id", "title", "file", "uploaded_at", "chunks"]
    read_only_fields = ["id", "uploaded_at"]