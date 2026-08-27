from django.contrib.auth import get_user_model
from django.utils import timezone
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from planetarium.models import (
    AstronomyShow,
    PlanetariumDome,
    ShowSession,
    Ticket,
    Reservation,
)

SHOW_SESSION_URL = reverse("planetarium:showsession-list")

User = get_user_model()


class ShowSessionApiTests(TestCase):
    """Tests for ShowSession ViewSet including tickets_available calculation."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="user@test.com", password="password123"
        )
        self.client.force_authenticate(self.user)

        self.show = AstronomyShow.objects.create(
            title="Black Hole", description="Event horizon", duration=45
        )
        self.dome = PlanetariumDome.objects.create(
            name="Big Dome", rows=10, seats_in_row=10
        )
        self.session = ShowSession.objects.create(
            astronomy_show=self.show,
            planetarium_dome=self.dome,
            show_time=timezone.now(),
            price=15.00,
        )

    def test_show_session_tickets_available_calculation(self):
        """
        Test that tickets_available is calculated correctly for authenticated
        user.
        """
        reservation = Reservation.objects.create(user=self.user)
        Ticket.objects.create(
            show_session=self.session, reservation=reservation, row=1, seat_in_row=1
        )
        Ticket.objects.create(
            show_session=self.session, reservation=reservation, row=1, seat_in_row=2
        )

        res = self.client.get(SHOW_SESSION_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["results"][0]["tickets_available"], 98)
