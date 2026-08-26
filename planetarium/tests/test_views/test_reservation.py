from django.contrib.auth import get_user_model
from django.utils import timezone
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from planetarium.models import AstronomyShow, PlanetariumDome, ShowSession, Reservation

RESERVATION_URL = reverse("planetarium:reservation-list")

User = get_user_model()


class ReservationApiTests(TestCase):
    """Tests for Reservation ViewSet user restriction and creation."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="user@test.com", password="password123"
        )
        self.other_user = User.objects.create_user(
            email="other@test.com", password="password123"
        )
        self.admin = User.objects.create_superuser(
            email="admin@test.com", password="password123"
        )

        self.show = AstronomyShow.objects.create(
            title="Supernova", description="Star explosion", duration=50
        )
        self.dome = PlanetariumDome.objects.create(
            name="Dome 1", rows=10, seats_in_row=10
        )
        self.session = ShowSession.objects.create(
            astronomy_show=self.show,
            planetarium_dome=self.dome,
            show_time=timezone.now(),
            price=12.00,
        )

    def test_unauthenticated_reservation_access_denied(self):
        """Test that unauthenticated user cannot view or create reservations."""
        res = self.client.get(RESERVATION_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_sees_only_own_reservations(self):
        """Test regular user receives only their own reservations."""
        res_user = Reservation.objects.create(user=self.user)
        Reservation.objects.create(user=self.other_user)

        self.client.force_authenticate(self.user)
        res = self.client.get(RESERVATION_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data["results"]), 1)
        self.assertEqual(res.data["results"][0]["id"], res_user.id)

    def test_admin_sees_all_reservations(self):
        """Test staff user can see reservations of all users."""
        Reservation.objects.create(user=self.user)
        Reservation.objects.create(user=self.other_user)

        self.client.force_authenticate(self.admin)
        res = self.client.get(RESERVATION_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data["results"]), 2)

    def test_create_reservation_assigns_authenticated_user(self):
        """Test creating reservation attaches currently authenticated user automatically."""
        self.client.force_authenticate(self.user)
        payload = {
            "tickets": [{"show_session": self.session.id, "row": 2, "seat_in_row": 3}]
        }
        res = self.client.post(RESERVATION_URL, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        reservation = Reservation.objects.get(id=res.data["id"])
        self.assertEqual(reservation.user, self.user)
