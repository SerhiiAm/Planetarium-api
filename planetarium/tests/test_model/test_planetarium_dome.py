from django.core.exceptions import ValidationError
from django.test import TestCase
from planetarium.models import PlanetariumDome


class PlanetariumDomeModelTests(TestCase):
    """Test suite for PlanetariumDome model validation, properties, and constraints."""

    def test_dome_capacity_and_size_property(self):
        """Test that capacity and dome_size dynamic properties calculate correctly."""
        dome = PlanetariumDome.objects.create(
            name="Small Dome", rows=10, seats_in_row=10
        )
        self.assertEqual(dome.capacity, 100)
        self.assertEqual(dome.dome_size, "small")

    def test_dome_rows_validation_error(self):
        """Test that setting rows outside the allowed range [7, 20] raises ValidationError."""

        dome = PlanetariumDome(name="Bad Dome", rows=5, seats_in_row=10)
        with self.assertRaises(ValidationError):
            dome.full_clean()
