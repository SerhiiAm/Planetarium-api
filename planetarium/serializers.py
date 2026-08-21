from rest_framework import serializers
from planetarium.models import ShowTheme, AstronomyShow


class ShowThemeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShowTheme
        fields = ("id", "name",)
        read_only_fields = ("id",)


class AstronomyShowSerializer(serializers.ModelSerializer):
    description_themes = serializers.PrimaryKeyRelatedField(
        queryset=ShowTheme.objects.all(),
        many=True
    )

    class Meta:
        model = AstronomyShow
        fields = (
            "id",
            "title",
            "description",
            "duration",
            "description_themes",
            "image",
        )
        read_only_fields = ("id", "image")


class AstronomyShowListSerializer(AstronomyShowSerializer):
    description_themes = serializers.SlugRelatedField(
        many=True,
        read_only=True,
        slug_field="name"
    )


class AstronomyShowDetailSerializer(AstronomyShowSerializer):
    description_themes = ShowThemeSerializer(many=True, read_only=True)


class AstronomyShowImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = AstronomyShow
        fields = ("id", "image")


class ShowThemeDetailSerializer(serializers.ModelSerializer):
    astronomy_shows = serializers.SlugRelatedField(
        many=True,
        read_only=True,
        slug_field="title"
    )

    class Meta:
        model = ShowTheme
        fields = ("id", "name", "astronomy_shows")
