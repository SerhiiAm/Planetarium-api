from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from planetarium.models import PlanetariumDome

PLANETARIUM_DOME_URL = reverse("planetarium:planetariumdome-list")

User = get_user_model()


class PlanetariumDomeApiTests(TestCase):
    """Tests for PlanetariumDome ViewSet access permissions and CRUD operations."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="user@test.com", password="password123"
        )
        self.admin = User.objects.create_superuser(
            email="admin@test.com", password="password123"
        )
        self.dome = PlanetariumDome.objects.create(
            name="Main Dome", rows=10, seats_in_row=10
        )

    def test_unauthenticated_user_denied(self):
        """Test that unauthenticated requests to list planetarium domes are denied."""
        res = self.client.get(PLANETARIUM_DOME_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_user_can_list_domes(self):
        """Test that authenticated regular users can retrieve planetarium domes list."""
        self.client.force_authenticate(self.user)
        res = self.client.get(PLANETARIUM_DOME_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data["results"]), 1)
        self.assertEqual(res.data["results"][0]["name"], self.dome.name)

    def test_regular_user_cannot_create_dome(self):
        """Test that regular users cannot create a planetarium dome."""
        self.client.force_authenticate(self.user)
        payload = {"name": "New Dome", "rows": 10, "seats_in_row": 10}
        res = self.client.post(PLANETARIUM_DOME_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_user_can_create_dome(self):
        """Test that admin users can successfully create a new dome."""
        self.client.force_authenticate(self.admin)
        payload = {"name": "New Dome", "rows": 10, "seats_in_row": 10}
        res = self.client.post(PLANETARIUM_DOME_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(PlanetariumDome.objects.filter(name="New Dome").exists())
