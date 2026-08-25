from django.contrib.auth import get_user_model
from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.exceptions import InvalidToken
from rest_framework_simplejwt.token_blacklist.models import (
    BlacklistedToken,
    OutstandingToken,
)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = (
            "id",
            "email",
            "first_name",
            "last_name",
            "password",
            "is_staff",
        )
        read_only_fields = ("id", "is_staff")
        extra_kwargs = {
            "password": {
                "write_only": True,
                "min_length": 5,
                "style": {"input_type": "password"},
                "label": _("Password"),
            },
        }

    def create(self, validated_data):
        """create user with a hashed password"""
        return get_user_model().objects.create_user(**validated_data)

    def update(self, instance, validated_data):
        """update user with a hashed password"""
        password = validated_data.pop("password", None)
        user = super().update(instance, validated_data)

        if password:
            user.set_password(password)
            user.save()

        return user


class CustomTokenRefreshSerializer(TokenRefreshSerializer):
    """
    Serializer for token renewal with reuse detection
    """

    def validate(self, attrs):
        raw_token = attrs["refresh"]

        if BlacklistedToken.objects.filter(token__token=raw_token).exists():

            outstanding_token = OutstandingToken.objects.filter(token=raw_token).first()

            if outstanding_token:
                user_id = outstanding_token.user_id

                active_user_tokens = OutstandingToken.objects.filter(user_id=user_id)

                existing_blacklisted_ids = set(
                    BlacklistedToken.objects.filter(token__user_id=user_id)
                    .values_list("token_id", flat=True)
                )

                tokens_to_blacklist = [
                    BlacklistedToken(token=t)
                    for t in active_user_tokens
                    if t.id not in existing_blacklisted_ids
                ]

                if tokens_to_blacklist:
                    BlacklistedToken.objects.bulk_create(
                        tokens_to_blacklist,
                        ignore_conflicts=True
                    )

            raise InvalidToken(
                "Reuse detected! All sessions revoked. Please login again."
            )

        return super().validate(attrs)
