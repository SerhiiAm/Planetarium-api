from datetime import timedelta
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.test import TestCase
from planetarium.models import ShowSession, PlanetariumDome, AstronomyShow


class ShowSessionValidationTests(TestCase):
    """Test suite for ShowSession model validation and overlap checks."""

    def setUp(self):
        self.dome = PlanetariumDome.objects.create(
            name="Main Dome", rows=10, seats_in_row=10
        )
        self.show = AstronomyShow.objects.create(
            title="Space Show", description="Desc", duration=60
        )
        self.now = timezone.now()

    def test_overlapping_session_raises_error(self):
        """Test that creating a session overlapping with an existing show and its 30-minute break raises ValidationError."""
        ShowSession.objects.create(
            astronomy_show=self.show,
            planetarium_dome=self.dome,
            show_time=self.now,
        )

        overlapping_session = ShowSession(
            astronomy_show=self.show,
            planetarium_dome=self.dome,
            show_time=self.now + timedelta(minutes=40),
        )

        with self.assertRaises(ValidationError):
            overlapping_session.full_clean()

    def test_exact_same_show_time_raises_integrity_error(self):
        """Test that creating a session at the exact same start time in the same dome raises ValidationError."""
        ShowSession.objects.create(
            astronomy_show=self.show, planetarium_dome=self.dome, show_time=self.now
        )
        with self.assertRaises(ValidationError):
            ShowSession.objects.create(
                astronomy_show=self.show, planetarium_dome=self.dome, show_time=self.now
            )
