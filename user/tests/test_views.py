from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

CREATE_USER_URL = reverse("user:create")
MANAGE_USER_URL = reverse("user:manage_user")
TOKEN_OBTAIN_URL = reverse("user:token_obtain_pair")
TOKEN_REFRESH_URL = reverse("user:token_refresh")
TOKEN_VERIFY_URL = reverse("user:token_verify")


class PublicUserApiTests(APITestCase):
    """Test public user API endpoints."""

    def test_create_user_success(self):
        """Test creating a user with valid payload is successful."""
        payload = {
            "email": "newuser@example.com",
            "password": "password123",
            "first_name": "John",
            "last_name": "Smith",
        }
        response = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(email=payload["email"]).exists())

    def test_manage_user_unauthorized(self):
        """Test authentication is required for managing user profile."""
        response = self.client.get(MANAGE_USER_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateUserApiTests(APITestCase):
    """Test authenticated user API endpoints."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="testuser@example.com",
            password="password123",
            first_name="John",
            last_name="Smith",
        )
        self.client.force_authenticate(user=self.user)

    def test_retrieve_profile_success(self):
        """Test retrieving profile for an authenticated user."""
        response = self.client.get(MANAGE_USER_URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], self.user.email)
        self.assertEqual(response.data["first_name"], self.user.first_name)

    def test_update_profile_success(self):
        """Test updating profile for an authenticated user."""
        payload = {"first_name": "UpdatedName"}
        response = self.client.patch(MANAGE_USER_URL, payload)

        self.user.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.user.first_name, payload["first_name"])


class TokenRefreshViewTests(APITestCase):
    """Test custom token refresh view endpoint."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="tokenuser@example.com",
            password="password123",
        )
        self.refresh_token = RefreshToken.for_user(self.user)

    def test_token_refresh_success(self):
        """Test refreshing token returns a new access token."""
        payload = {"refresh": str(self.refresh_token)}
        response = self.client.post(TOKEN_REFRESH_URL, payload)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
