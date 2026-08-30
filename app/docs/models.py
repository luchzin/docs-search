import uuid
from django.db import models
from pgvector.django import VectorField  # Import pgvector field


class Document(models.Model):
  id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
  title = models.CharField(max_length=255)
  file = models.FileField(upload_to="uploads/")
  uploaded_at = models.DateTimeField(auto_now_add=True)

  def __str__(self):
    return self.title


class DocumentChunk(models.Model):
  id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
  document = models.ForeignKey(
      Document, on_delete=models.CASCADE, related_name="chunks"
  )
  content = models.TextField()
  page_number = models.IntegerField(null=True, blank=True)
  chunk_index = models.IntegerField()

  # 1536 dimensions for OpenAI text-embedding-3-small
  embedding = VectorField(dimensions=1536, null=True, blank=True)

  class Meta:
    ordering = ["chunk_index"]

  def __str__(self):
    return f"{self.document.title} - Chunk {self.chunk_index}"