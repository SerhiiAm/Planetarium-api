import uuid
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from planetarium.models import AstronomyShow, ShowTheme
from planetarium.serializers import (
    AstronomyShowListSerializer,
    AstronomyShowDetailSerializer,
)

ASTRONOMY_SHOW_URL = reverse("planetarium:astronomyshow-list")


def detail_url(show_id: int) -> str:
    return reverse("planetarium:astronomyshow-detail", args=[show_id])


def sample_show(**params) -> AstronomyShow:
    defaults = {
        "title": f"Test Show {uuid.uuid4()}",
        "description": "Test description for astronomy show.",
        "duration": 60,
    }
    defaults.update(params)
    return AstronomyShow.objects.create(**defaults)


class UnauthenticatedAstronomyShowApiTests(TestCase):
    """Test suite for unauthenticated user requests to AstronomyShow API."""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test that authentication is required to access the astronomy show list."""
        response = self.client.get(ASTRONOMY_SHOW_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedAstronomyShowApiTests(TestCase):
    """Test suite for regular authenticated user access to AstronomyShow API."""

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="user@test.com",
            password="testpassword123",
        )
        self.client.force_authenticate(user=self.user)

    def test_astronomy_shows_list(self):
        """Test retrieving a list of astronomy shows for an authenticated user."""
        sample_show()
        show_with_theme = sample_show()
        theme_1 = ShowTheme.objects.create(name="Stars")
        theme_2 = ShowTheme.objects.create(name="Planets")
        show_with_theme.description_themes.add(theme_1, theme_2)

        res = self.client.get(ASTRONOMY_SHOW_URL)
        shows = AstronomyShow.objects.all()
        serializer = AstronomyShowListSerializer(shows, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["results"], serializer.data)

    def test_filter_shows_by_theme(self):
        """Test filtering astronomy shows by multiple theme IDs."""
        show_without_theme = sample_show()
        show_with_theme_1 = sample_show(title="Show with Theme 1")
        show_with_theme_2 = sample_show(title="Show with Theme 2")

        theme_1 = ShowTheme.objects.create(name="Stars")
        theme_2 = ShowTheme.objects.create(name="Planets")

        show_with_theme_1.description_themes.add(theme_1)
        show_with_theme_2.description_themes.add(theme_2)

        res = self.client.get(
            ASTRONOMY_SHOW_URL, {"description_themes": f"{theme_1.id},{theme_2.id}"}
        )

        serializer_without_theme = AstronomyShowListSerializer(show_without_theme)
        serializer_show_theme_1 = AstronomyShowListSerializer(show_with_theme_1)
        serializer_show_theme_2 = AstronomyShowListSerializer(show_with_theme_2)

        self.assertIn(serializer_show_theme_1.data, res.data["results"])
        self.assertIn(serializer_show_theme_2.data, res.data["results"])
        self.assertNotIn(serializer_without_theme.data, res.data["results"])

    def test_retrieve_show_detail(self):
        """Test retrieving detailed information of a specific astronomy show."""
        show = sample_show()
        show.description_themes.add(ShowTheme.objects.create(name="Galaxies"))

        url = detail_url(show.id)
        res = self.client.get(url)
        serializer = AstronomyShowDetailSerializer(show)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_create_show_forbidden(self):
        """Test that a regular user cannot create an astronomy show (403 Forbidden)."""
        payload = {
            "title": "Forbidden Show Title",
            "description": "Some info",
            "duration": 45,
        }

        res = self.client.post(ASTRONOMY_SHOW_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class AdminAstronomyShowApiTests(TestCase):
    """
    Test suite for admin user permissions and management operations
    in AstronomyShow API.
    """

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="admin@test.com",
            password="testpassword123",
            is_staff=True,
        )
        self.client.force_authenticate(user=self.user)

    def test_create_astronomy_show(self):
        """Test that an admin user can successfully create a new astronomy show."""
        payload = {
            "title": "Black Holes Exploration",
            "description": "Deep dive into singularities.",
            "duration": 90,
        }

        res = self.client.post(ASTRONOMY_SHOW_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        show = AstronomyShow.objects.get(id=res.data["id"])
        for key in payload:
            self.assertEqual(payload[key], getattr(show, key))

    def test_create_astronomy_show_with_themes(self):
        """Test creating an astronomy show with multiple associated themes by admin."""
        theme_1 = ShowTheme.objects.create(name="Stars")
        theme_2 = ShowTheme.objects.create(name="Nebulas")

        payload = {
            "title": "Journey Through Space",
            "description": "Amazing space show.",
            "duration": 60,
            "description_themes": [theme_1.id, theme_2.id],
        }

        res = self.client.post(ASTRONOMY_SHOW_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        show = AstronomyShow.objects.get(id=res.data["id"])
        themes = show.description_themes.all()

        self.assertIn(theme_1, themes)
        self.assertIn(theme_2, themes)
        self.assertEqual(themes.count(), 2)
