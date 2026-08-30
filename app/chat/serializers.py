from rest_framework import serializers
from .models import ChatSession, Message


class MessageSerializer(serializers.ModelSerializer):

  class Meta:
    model = Message
    fields = ["id", "role", "content", "created_at"]
    read_only_fields = ["id", "created_at"]


class ChatSessionSerializer(serializers.ModelSerializer):
  messages = MessageSerializer(many=True, read_only=True)

  class Meta:
    model = ChatSession
    fields = ["id", "title", "created_at", "updated_at", "messages"]
    read_only_fields = ["id", "created_at", "updated_at"]