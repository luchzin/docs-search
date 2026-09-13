import uuid
from django.conf import settings
from django.db import models


class AIModel(models.Model):
    PROVIDER_CHOICES = (
        ("gemini", "Google Gemini"),
        ("openai", "OpenAI ChatGPT"),
        ("claude", "Anthropic Claude"),
        ("deepseek", "DeepSeek AI"),
    )

    model_id = models.CharField(max_length=100, primary_key=True)
    name = models.CharField(max_length=100)
    provider = models.CharField(max_length=50, choices=PROVIDER_CHOICES)
    provider_name = models.CharField(max_length=100)
    description = models.TextField(blank=True, default="")
    is_default = models.BooleanField(default=False)
    requires_api_key = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-is_default", "provider_name", "name"]

    def __str__(self):
        return f"{self.name} ({self.model_id})"


class UserAIConfig(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="ai_config",
        null=True,
        blank=True,
    )
    selected_model = models.ForeignKey(
        AIModel, on_delete=models.SET_NULL, null=True, blank=True
    )
    api_keys = models.JSONField(default=dict, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        username = self.user.username if self.user else "Anonymous"
        return f"AIConfig for {username}"


class ChatSession(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="chats",
        null=True,
        blank=True,
    )
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