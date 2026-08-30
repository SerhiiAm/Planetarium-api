from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework_simplejwt.exceptions import InvalidToken
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import (
    OutstandingToken,
    BlacklistedToken,
)

from user.serializers import CustomTokenRefreshSerializer, UserSerializer

User = get_user_model()


class CustomTokenRefreshSerializerTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com",
            password="password123"
        )
        self.refresh_session_1 = RefreshToken.for_user(self.user)
        self.refresh_session_2 = RefreshToken.for_user(self.user)

    def test_reuse_detected_revokes_all_user_sessions(self):
        """
        Scenario 1: R1 Token Theft Attack.
        A hacker steals R1 and refreshes it (R1 is added to the blacklist,
        and the hacker receives R2).
        When the victim attempts to use their R1, the system detects a token
        reuse attempt and revokes absolutely all active tokens for that user
        (including session_2).
        """
        serializer = CustomTokenRefreshSerializer()

        data = serializer.validate({"refresh": str(self.refresh_session_1)})
        self.assertIn("access", data)

        self.assertTrue(
            BlacklistedToken.objects.filter(
                token__token=str(self.refresh_session_1)
            ).exists()
        )

        with self.assertRaises(InvalidToken) as cm:
            serializer.validate({"refresh": str(self.refresh_session_1)})

        self.assertIn("Reuse detected!", str(cm.exception))

        total_user_tokens = OutstandingToken.objects.filter(user=self.user).count()
        blacklisted_user_tokens = BlacklistedToken.objects.filter(
            token__user=self.user
        ).count()

        self.assertEqual(total_user_tokens, 3)
        self.assertEqual(blacklisted_user_tokens, 3)

    def test_race_condition_concurrent_refresh_with_same_r1(self):
        """
        Scenario 2: Token Race Condition (Parallel Access).
        Both parties (the Victim and the Hacker) possess an instance of R1.
        The first successful request validates R1. The second request encounters
        an error and revokes all active sessions.
        """
        serializer = CustomTokenRefreshSerializer()
        shared_r1 = str(self.refresh_session_1)

        serializer.validate({"refresh": shared_r1})

        with self.assertRaises(InvalidToken):
            serializer.validate({"refresh": shared_r1})

        with self.assertRaises(InvalidToken):
            serializer.validate({"refresh": str(self.refresh_session_2)})

    def test_bulk_create_ignores_already_blacklisted_tokens(self):
        """
        Scenario 3: Testing N+1 Optimization and bulk_create.
        Ensuring that a cascade revocation does not trigger an IntegrityError
        for tokens that are ALREADY blacklisted.
        """
        serializer = CustomTokenRefreshSerializer()

        token_2_obj = OutstandingToken.objects.get(token=str(self.refresh_session_2))
        BlacklistedToken.objects.create(token=token_2_obj)

        serializer.validate({"refresh": str(self.refresh_session_1)})

        with self.assertRaises(InvalidToken):
            serializer.validate({"refresh": str(self.refresh_session_1)})

        self.assertEqual(
            BlacklistedToken.objects.filter(token__user=self.user).count(), 3
        )


class UserSerializerTests(TestCase):
    def setUp(self):
        self.user_data = {
            "email": "testuser@example.com",
            "password": "password123",
            "first_name": "John",
            "last_name": "Smith",
        }

    def test_create_user_with_hashed_password(self):
        """The serializer correctly hashes the password upon creation"""
        serializer = UserSerializer(data=self.user_data)
        self.assertTrue(serializer.is_valid())
        user = serializer.save()

        self.assertEqual(user.email, self.user_data["email"])
        self.assertTrue(user.check_password(self.user_data["password"]))
        self.assertNotIn("password", serializer.data)

    def test_update_user_password_hashes_properly(self):
        """Updating the password via the serializer overwrites the hash."""
        user = User.objects.create_user(**self.user_data)
        new_password = "newsecurepassword123"

        serializer = UserSerializer(
            instance=user,
            data={"password": new_password},
            partial=True,
        )
        self.assertTrue(serializer.is_valid())
        updated_user = serializer.save()

        self.assertTrue(updated_user.check_password(new_password))

    def test_read_only_fields_cannot_be_modified(self):
        """Поля is_staff и id игнорируются при попытке записи."""
        self.user_data["is_staff"] = True
        serializer = UserSerializer(data=self.user_data)
        self.assertTrue(serializer.is_valid())
        user = serializer.save()

        self.assertFalse(user.is_staff)
