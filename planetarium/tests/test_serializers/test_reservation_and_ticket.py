from django.contrib.auth import get_user_model
from django.utils import timezone
from django.test import TestCase
from planetarium.models import (
    AstronomyShow,
    PlanetariumDome,
    ShowSession,
    Reservation,
    Ticket,
)
from planetarium.serializers import TicketSerializer, ReservationSerializer

User = get_user_model()


class ReservationAndTicketSerializerTests(TestCase):
    """Tests for Reservation and Ticket serializers and atomic creation logic."""

    def setUp(self):

        self.user = User.objects.create_user(
            email="test@example.com", password="password123"
        )

        self.show = AstronomyShow.objects.create(
            title="Starfall", description="Meteor shower", duration=30
        )

        self.dome = PlanetariumDome.objects.create(
            name="Small Dome", rows=10, seats_in_row=10
        )

        self.session = ShowSession.objects.create(
            astronomy_show=self.show,
            planetarium_dome=self.dome,
            show_time=timezone.now(),
            price=10.00,
        )

    def test_ticket_validation(self):
        """Test TicketSerializer validates ticket seat/row boundary conditions."""
        payload = {
            "show_session": self.session.id,
            "row": 1,
            "seat_in_row": 2,
        }
        serializer = TicketSerializer(data=payload)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_reservation_creation_with_nested_tickets(self):
        """Test creation of Reservation along with nested Tickets in atomic transaction."""
        payload = {
            "tickets": [
                {"show_session": self.session.id, "row": 1, "seat_in_row": 1},
                {"show_session": self.session.id, "row": 1, "seat_in_row": 2},
            ]
        }
        serializer = ReservationSerializer(data=payload)
        self.assertTrue(serializer.is_valid(), serializer.errors)

        reservation = serializer.save(user=self.user)
        self.assertEqual(Reservation.objects.count(), 1)
        self.assertEqual(Ticket.objects.count(), 2)
        self.assertEqual(reservation.tickets.count(), 2)
