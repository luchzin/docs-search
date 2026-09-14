from rest_framework import serializers
from .models import ChatSession, Message, AIModel, UserAIConfig
from app.docs.serializers import DocumentSerializer


class AIModelSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source="model_id", read_only=True)

    class Meta:
        model = AIModel
        fields = [
            "id",
            "model_id",
            "name",
            "provider",
            "provider_name",
            "description",
            "is_default",
            "requires_api_key",
        ]


class UserAIConfigSerializer(serializers.ModelSerializer):
    selected_model_id = serializers.CharField(
        source="selected_model.model_id", read_only=True
    )

    class Meta:
        model = UserAIConfig
        fields = ["selected_model", "selected_model_id", "api_keys", "updated_at"]


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ["id", "role", "content", "created_at"]
        read_only_fields = ["id", "created_at"]


class ChatSessionSerializer(serializers.ModelSerializer):
    messages = serializers.SerializerMethodField()
    documents = DocumentSerializer(many=True, read_only=True)

    class Meta:
        model = ChatSession
        fields = ["id", "title", "created_at", "updated_at", "messages", "documents"]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_messages(self, obj):
        return []