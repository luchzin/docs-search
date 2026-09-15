from rest_framework import serializers
from .models import Document, DocumentChunk


class DocumentChunkSerializer(serializers.ModelSerializer):

  class Meta:
    model = DocumentChunk
    fields = ["id", "content", "page_number", "chunk_index"]


class DocumentSerializer(serializers.ModelSerializer):
  chunks = DocumentChunkSerializer(many=True, read_only=True)
  size = serializers.SerializerMethodField()

  class Meta:
    model = Document
    fields = ["id", "title", "file", "size", "uploaded_at", "session", "chunks"]
    read_only_fields = ["id", "uploaded_at"]

  def get_size(self, obj):
    try:
      if obj.file and hasattr(obj.file, "size"):
        return obj.file.size
    except Exception:
      pass
    return 0