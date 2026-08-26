import tempfile
from PIL import Image
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from planetarium.models import AstronomyShow, ShowTheme

ASTRONOMY_SHOW_URL = reverse("planetarium:astronomyshow-list")

User = get_user_model()


class AstronomyShowApiTests(TestCase):
    """Tests for AstronomyShow ViewSet including filtering and image uploading."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="user@test.com", password="password123"
        )
        self.admin = User.objects.create_superuser(
            email="admin@test.com", password="password123"
        )
        self.client.force_authenticate(self.user)

        self.theme_space = ShowTheme.objects.create(name="Space")
        self.theme_planets = ShowTheme.objects.create(name="Planets")

        self.show1 = AstronomyShow.objects.create(
            title="Mars Exploration", description="About Mars", duration=60
        )
        self.show1.description_themes.add(self.theme_planets)

        self.show2 = AstronomyShow.objects.create(
            title="Galaxies Far Away", description="Deep space", duration=90
        )
        self.show2.description_themes.add(self.theme_space)

    def test_filter_astronomy_shows_by_title(self):
        """Test filtering astronomy shows by title substring."""
        res = self.client.get(ASTRONOMY_SHOW_URL, {"title": "Mars"})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data["results"]), 1)
        self.assertEqual(res.data["results"][0]["id"], self.show1.id)

    def test_filter_astronomy_shows_by_themes(self):
        """Test filtering astronomy shows by theme IDs."""
        res = self.client.get(
            ASTRONOMY_SHOW_URL, {"description_themes": f"{self.theme_space.id}"}
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data["results"]), 1)
        self.assertEqual(res.data["results"][0]["id"], self.show2.id)

    def test_upload_image_forbidden_for_regular_user(self):
        """Test uploading an image is forbidden for non-admin users."""
        url = reverse("planetarium:astronomyshow-upload-image", args=[self.show1.id])
        res = self.client.post(url, {}, format="multipart")
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_upload_image_admin_success(self):
        """Test image upload action succeeds for admin user."""
        self.client.force_authenticate(self.admin)
        url = reverse("planetarium:astronomyshow-upload-image", args=[self.show1.id])

        with tempfile.NamedTemporaryFile(suffix=".jpg") as image_file:
            img = Image.new("RGB", (10, 10))
            img.save(image_file, format="JPEG")
            image_file.seek(0)
            res = self.client.post(url, {"image": image_file}, format="multipart")

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("image", res.data)
        self.show1.refresh_from_db()
        self.assertTrue(self.show1.image)
