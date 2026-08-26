from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from planetarium.models import (
    Ticket,
    ShowSession,
    PlanetariumDome,
    AstronomyShow,
    Reservation,
)
from django.utils import timezone


class TicketValidationTests(TestCase):
    """Test suite for validating ticket row and seat restrictions."""

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="user@test.com",
            password="testpassword123",
        )
        self.dome = PlanetariumDome.objects.create(
            name="Dome", rows=10, seats_in_row=10
        )
        self.show = AstronomyShow.objects.create(
            title="Show", description="Desc", duration=60
        )
        self.session = ShowSession.objects.create(
            astronomy_show=self.show,
            planetarium_dome=self.dome,
            show_time=timezone.now(),
        )

    def test_ticket_seat_out_of_range_raises_error(self):
        """Test that selecting a seat number outside the dome's limit raises ValidationError."""
        ticket = Ticket(
            row=5,
            seat_in_row=15,
            show_session=self.session,
        )
        with self.assertRaises(ValidationError):
            Ticket.validate_ticket(
                row=ticket.row,
                seat_in_row=ticket.seat_in_row,
                planetarium_dome=self.session.planetarium_dome,
                error_to_raise=ValidationError,
            )

    def test_duplicate_ticket_seat_and_row_raises_integrity_error(self):
        """Test that buying the exact same seat for the same session raises ValidationError."""
        reservation = Reservation.objects.create(user=self.user)
        Ticket.objects.create(
            row=1, seat_in_row=1, show_session=self.session, reservation=reservation
        )
        with self.assertRaises(ValidationError):
            Ticket.objects.create(
                row=1, seat_in_row=1, show_session=self.session, reservation=reservation
            )
