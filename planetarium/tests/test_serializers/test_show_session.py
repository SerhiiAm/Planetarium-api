from django.utils import timezone
from django.test import TestCase
from planetarium.models import AstronomyShow, PlanetariumDome, ShowSession
from planetarium.serializers import ShowSessionSerializer, ShowSessionListSerializer


class ShowSessionSerializerTests(TestCase):
    """Tests for ShowSession serializers, validation, and price formatting."""

    def setUp(self):
        self.show = AstronomyShow.objects.create(
            title="Black Holes", description="Event Horizon", duration=60
        )
        self.dome = PlanetariumDome.objects.create(
            name="Main Dome", rows=10, seats_in_row=10
        )
        self.show_time = timezone.now()

    def test_show_session_validation_triggers_model_clean(self):
        """Test that custom validation in ShowSessionSerializer delegates to model's validate_show_session."""
        payload = {
            "astronomy_show": self.show.id,
            "planetarium_dome": self.dome.id,
            "show_time": self.show_time,
            "price": "15.50",
        }
        serializer = ShowSessionSerializer(data=payload)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_show_session_list_serializer_price_formatting(self):
        """Test that ShowSessionListSerializer properly formats price with dollar sign."""
        session = ShowSession.objects.create(
            astronomy_show=self.show,
            planetarium_dome=self.dome,
            show_time=self.show_time,
            price=20.00,
        )
        serializer = ShowSessionListSerializer(session)
        self.assertEqual(serializer.data["price"], "$20")
        self.assertEqual(serializer.data["duration"], 60)
