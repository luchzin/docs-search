import re
from django.contrib.auth import get_user_model
from rest_framework import serializers
from djoser.serializers import (
    UserCreateSerializer as BaseUserCreateSerializer,
    UserSerializer as BaseUserSerializer,
    TokenCreateSerializer as BaseTokenCreateSerializer,
)

User = get_user_model()


class UserCreateSerializer(BaseUserCreateSerializer):
    class Meta(BaseUserCreateSerializer.Meta):
        model = User
        fields = (
            "id",
            "email",
            "username",
            "password",
        )
        extra_kwargs = {
            "username": {"required": False, "allow_blank": True},
        }

    def validate_username(self, value):
        if value:
            value = re.sub(r"[^\w.@+-]", "_", value.strip())
        return value

    def perform_create(self, validated_data):
        username = validated_data.get("username")
        if not username or User.objects.filter(username=username).exists():
            email = validated_data.get("email", "")
            raw = username or (email.split("@")[0] if email else "user")
            base_username = re.sub(r"[^\w.@+-]", "_", raw)
            candidate = base_username
            counter = 1
            while User.objects.filter(username=candidate).exists():
                candidate = f"{base_username}_{counter}"
                counter += 1
            validated_data["username"] = candidate

        return super().perform_create(validated_data)


class UserSerializer(BaseUserSerializer):
    class Meta(BaseUserSerializer.Meta):
        model = User
        fields = ("id", "username", "email")


class CustomTokenCreateSerializer(BaseTokenCreateSerializer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["email"] = serializers.CharField(required=False, write_only=True)
        self.fields[self.username_field].required = False

    def validate(self, attrs):
        password = attrs.get("password")
        email = attrs.get("email")
        username = attrs.get(self.username_field)

        login_identifier = email or username
        if not login_identifier:
            raise serializers.ValidationError(
                {"detail": "Email or username is required."}
            )

        user = User.objects.filter(email__iexact=login_identifier).first()
        if not user:
            user = User.objects.filter(username__iexact=login_identifier).first()

        if user:
            attrs[self.username_field] = user.get_username()
        elif email and not username:
            attrs[self.username_field] = email

        return super().validate(attrs)
