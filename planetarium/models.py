import uuid
from pathlib import Path

from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils.text import slugify


class ShowTheme(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name_plural = "show themes"

    def __str__(self):
        return f"{self.id} -{self.name}"


def astronomy_show_image_path(instance: "AstronomyShow", filename: str) -> Path:
    ext = Path(filename).suffix
    filename = f"{slugify(instance.title)}--{uuid.uuid4()}{ext}"
    return Path("uploads/astronomy_shows/") / filename


class AstronomyShow(models.Model):
    title = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    description_themes = models.ManyToManyField(
        ShowTheme, related_name="astronomy_shows"
    )
    image = models.ImageField(
        upload_to=astronomy_show_image_path, null=True, blank=True
    )

    class Meta:
        verbose_name_plural = "astronomy shows"

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
        MaxValueValidator(15)])

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
