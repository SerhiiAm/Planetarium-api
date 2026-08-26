from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from planetarium.models import ShowTheme

SHOW_THEME_URL = reverse("planetarium:showtheme-list")

User = get_user_model()


class ShowThemeApiTests(TestCase):
    """Tests for ShowTheme API with IsAdminOrReadOnly permissions."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="user@test.com", password="password123"
        )
        self.admin = User.objects.create_superuser(
            email="admin@test.com", password="password123"
        )
        self.theme = ShowTheme.objects.create(name="Stars")

    def test_unauthenticated_user_denied(self):
        """Test that unauthenticated users cannot access list view."""
        res = self.client.get(SHOW_THEME_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_user_can_list(self):
        """Test that authenticated regular users can list themes."""
        self.client.force_authenticate(self.user)
        res = self.client.get(SHOW_THEME_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_regular_user_cannot_create_theme(self):
        """Test that regular users are restricted from creating themes."""
        self.client.force_authenticate(self.user)
        payload = {"name": "Galaxies"}
        res = self.client.post(SHOW_THEME_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_user_can_create_theme(self):
        """Test that admin users can create themes."""
        self.client.force_authenticate(self.admin)
        payload = {"name": "Galaxies"}
        res = self.client.post(SHOW_THEME_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
