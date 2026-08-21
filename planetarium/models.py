import uuid
from pathlib import Path
from datetime import timedelta
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from decimal import Decimal
from planetarium_service import settings


class ShowTheme(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name_plural = "show themes"
        ordering = ["name"]

    def __str__(self):
        return f"{self.id} - {self.name}"


def astronomy_show_image_path(instance: "AstronomyShow", filename: str) -> Path:
    ext = Path(filename).suffix
    filename = f"{slugify(instance.title)}--{uuid.uuid4()}{ext}"
    return Path("uploads/astronomy_shows/") / filename


class AstronomyShow(models.Model):
    title = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    duration = models.PositiveIntegerField(default=60)
    description_themes = models.ManyToManyField(
        ShowTheme, related_name="astronomy_shows"
    )
    image = models.ImageField(
        upload_to=astronomy_show_image_path, null=True, blank=True
    )

    class Meta:
        verbose_name_plural = "astronomy shows"
        ordering = ["title"]

    def __str__(self):
        return f"Show: {self.title} (id = {self.id})"


class PlanetariumDome(models.Model):
    name = models.CharField(max_length=255)
    rows = models.IntegerField(validators=[
        MinValueValidator(7),
        MaxValueValidator(20)
    ])
    seats_in_row = models.IntegerField(validators=[
        MinValueValidator(7),
        MaxValueValidator(15)
    ])

    @property
    def capacity(self) -> int:
        return self.rows * self.seats_in_row

    @property
    def dome_size(self) -> str:
        if self.capacity <= 100:
            return "small"
        elif self.capacity <= 200:
            return "medium"
        return "large"

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    class Meta:
        verbose_name_plural = "planetarium domes"
        ordering = ["name"]

        constraints = [
            models.CheckConstraint(
                condition=models.Q(rows__gte=7) & models.Q(rows__lte=20),
                name="planetarium_dome_rows_range",
            ),
            models.CheckConstraint(
                condition=models.Q(seats_in_row__gte=7) & models.Q(seats_in_row__lte=15),
                name="planetarium_dome_seats_in_row_range",
            ),
        ]

    def __str__(self):
        return f"{self.name} ({self.dome_size.upper()}: {self.capacity} seats)"


class ShowSession(models.Model):
    astronomy_show = models.ForeignKey(
        AstronomyShow,
        on_delete=models.CASCADE,
        related_name="sessions"
    )
    planetarium_dome = models.ForeignKey(
        PlanetariumDome,
        on_delete=models.CASCADE,
        related_name="sessions")
    show_time = models.DateTimeField()

    price = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=Decimal("10.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )

    class Meta:
        verbose_name_plural = "show sessions"
        ordering = ["show_time", "price"]
        constraints = [
            models.UniqueConstraint(
                fields=["planetarium_dome", "show_time"],
                name="unique_dome_show_time",
            )
        ]
        indexes = [
            models.Index(fields=["show_time"]),
            models.Index(fields=["astronomy_show", "show_time"]),
        ]

    def clean(self):
        super().clean()

        if not self.show_time or not self.astronomy_show or not self.planetarium_dome:
            return

        break_duration = timedelta(minutes=30)
        show_duration = timedelta(minutes=self.astronomy_show.duration)
        current_start = self.show_time
        current_end_with_break = current_start + show_duration + break_duration
        other_sessions = ShowSession.objects.filter(
            planetarium_dome=self.planetarium_dome
        ).select_related("astronomy_show")

        if self.pk:
            other_sessions = other_sessions.exclude(pk=self.pk)

        for session in other_sessions:
            existing_start = session.show_time
            existing_duration = timedelta(minutes=session.astronomy_show.duration)
            existing_end_with_break = existing_start + existing_duration + break_duration
            if current_start < existing_end_with_break and current_end_with_break > existing_start:
                raise ValidationError({
                    "show_time": (
                        f"Dome '{self.planetarium_dome.name}' is occupied. "
                        f"Session '{session.astronomy_show.title}' runs from "
                        f"{existing_start.strftime('%H:%M')} to {existing_end_with_break.strftime('%H:%M')} "
                        f"(including a 30-minute break)."
                    )
                })

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.astronomy_show.title} - {self.show_time.strftime('%Y-%m-%d %H:%M')} (${self.price})"


class Reservation(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reservations"
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Reservation {self.id} at {self.created_at.strftime('%Y-%m-%d %H:%M')}"


class Ticket(models.Model):
    row = models.PositiveIntegerField()
    seat_in_row = models.PositiveIntegerField()
    show_session = models.ForeignKey(
        ShowSession,
        on_delete=models.CASCADE,
        related_name="tickets")

    reservation = models.ForeignKey(
        Reservation,
        on_delete=models.CASCADE,
        related_name="tickets")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["show_session", "row", "seat_in_row"],
                name="unique_ticket_show_session_row_seat",
            )
        ]
        ordering = ["show_session", "row", "seat_in_row"]

    def __str__(self):
        if not hasattr(self, "show_session") or self.show_session is None:
            return f"Ticket (Row: {self.row}, Seat: {self.seat_in_row})"
        return (
            f"{self.show_session.astronomy_show.title} "
            f"(Row: {self.row}, Seat: {self.seat_in_row})"
        )

    @staticmethod
    def validate_ticket(
            row: int,
            seat_in_row: int,
            planetarium_dome,
            error_to_raise
    ):
        errors = {}

        if row is not None and not (1 <= row <= planetarium_dome.rows):
            errors["row"] = f"Row number must be in range [1, {planetarium_dome.rows}], not {row}."

        if seat_in_row is not None and not (1 <= seat_in_row <= planetarium_dome.seats_in_row):
            errors[
                "seat_in_row"] = f"Seat number must be in range [1, {planetarium_dome.seats_in_row}], not {seat_in_row}."

        if errors:
            raise error_to_raise(errors)

    def clean(self):
        super().clean()

        if not self.show_session or not hasattr(self.show_session, "planetarium_dome"):
            return

        Ticket.validate_ticket(
            row=self.row,
            seat_in_row=self.seat_in_row,
            planetarium_dome=self.show_session.planetarium_dome,
            error_to_raise=ValidationError,
        )

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)
