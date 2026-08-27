from django.test import TestCase
from planetarium.models import ShowTheme, AstronomyShow
from planetarium.serializers import ShowThemeSerializer, ShowThemeDetailSerializer


class ShowThemeSerializerTests(TestCase):
    """Tests for ShowTheme serializers and related astronomy show relations."""

    def setUp(self):
        self.theme = ShowTheme.objects.create(name="Space Exploration")

    def test_show_theme_serialization(self):
        """Test that ShowTheme model is correctly serialized."""
        serializer = ShowThemeSerializer(self.theme)
        expected_data = {
            "id": self.theme.id,
            "name": "Space Exploration",
        }
        self.assertEqual(serializer.data, expected_data)

    def test_show_theme_detail_serialization(self):
        """
        Test that ShowThemeDetailSerializer includes related astronomy show
        titles as slugs.
        """
        show = AstronomyShow.objects.create(
            title="Apollo 11", description="Moon landing", duration=60
        )
        show.description_themes.add(self.theme)

        serializer = ShowThemeDetailSerializer(self.theme)
        self.assertIn("astronomy_shows", serializer.data)
        self.assertEqual(serializer.data["astronomy_shows"], ["Apollo 11"])
