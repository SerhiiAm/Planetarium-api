import uuid
from pathlib import Path
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
