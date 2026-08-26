from django.test import TestCase
from planetarium.models import ShowTheme, AstronomyShow
from planetarium.serializers import (
    AstronomyShowSerializer,
    AstronomyShowListSerializer,
    AstronomyShowDetailSerializer,
)


class AstronomyShowSerializerTests(TestCase):
    """Tests for AstronomyShow serializers including list and detail variants."""

    def setUp(self):
        self.theme = ShowTheme.objects.create(name="Stars")
        self.show = AstronomyShow.objects.create(
            title="Hubble Journey", description="Deep space views", duration=45
        )
        self.show.description_themes.add(self.theme)

    def test_astronomy_show_deserialization_valid_data(self):
        """Test deserialization and creation of AstronomyShow with valid PrimaryKeyRelatedField themes."""
        payload = {
            "title": "James Webb",
            "description": "New cosmos images",
            "duration": 50,
            "description_themes": [self.theme.id],
        }
        serializer = AstronomyShowSerializer(data=payload)
        self.assertTrue(serializer.is_valid())
        show = serializer.save()
        self.assertEqual(show.title, "James Webb")
        self.assertIn(self.theme, show.description_themes.all())

    def test_astronomy_show_list_serializer(self):
        """Test AstronomyShowListSerializer formats themes as slug names."""
        serializer = AstronomyShowListSerializer(self.show)
        self.assertEqual(serializer.data["description_themes"], ["Stars"])

    def test_astronomy_show_detail_serializer(self):
        """Test AstronomyShowDetailSerializer nests full ShowThemeSerializer object."""
        serializer = AstronomyShowDetailSerializer(self.show)
        self.assertEqual(
            serializer.data["description_themes"],
            [{"id": self.theme.id, "name": "Stars"}],
        )
