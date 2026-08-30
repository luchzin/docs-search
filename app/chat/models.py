import uuid
from django.db import models


class ChatSession(models.Model):
  id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
  title = models.CharField(max_length=255, default="New Chat")
  created_at = models.DateTimeField(auto_now_add=True)
  updated_at = models.DateTimeField(auto_now=True)

  def __str__(self):
    return f"{self.title} ({self.id})"


class Message(models.Model):
  ROLE_CHOICES = (
      ("user", "User"),
      ("assistant", "Assistant"),
      ("system", "System"),
  )

  id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
  session = models.ForeignKey(
      ChatSession, on_delete=models.CASCADE, related_name="messages"
  )
  role = models.CharField(max_length=15, choices=ROLE_CHOICES)
  content = models.TextField()
  created_at = models.DateTimeField(auto_now_add=True)

  class Meta:
    ordering = ["created_at"]

  def __str__(self):
    return f"{self.role}: {self.content[:30]}"