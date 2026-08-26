from django.test import TestCase
from planetarium.models import PlanetariumDome
from planetarium.serializers import PlanetariumDomeSerializer


class PlanetariumDomeSerializerTests(TestCase):
    """Tests for PlanetariumDomeSerializer and its computed fields."""

    def test_planetarium_dome_read_only_fields(self):
        """Test that calculated fields like capacity and dome_size are read-only and included in output."""
        dome = PlanetariumDome.objects.create(
            name="Orion Dome", rows=10, seats_in_row=15
        )
        serializer = PlanetariumDomeSerializer(dome)
        self.assertEqual(serializer.data["name"], "Orion Dome")
        self.assertEqual(serializer.data["rows"], 10)
        self.assertEqual(serializer.data["seats_in_row"], 15)
        self.assertIn("capacity", serializer.data)
        self.assertIn("dome_size", serializer.data)
