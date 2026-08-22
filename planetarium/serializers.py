from rest_framework import serializers
from django.core.exceptions import ValidationError as DjangoValidationError
from planetarium.models import ShowTheme, AstronomyShow, PlanetariumDome, ShowSession


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


class PlanetariumDomeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlanetariumDome
        fields = (
            "id",
            "name",
            "rows",
            "seats_in_row",
            "capacity",
            "dome_size",
        )
        read_only_fields = ("id", "capacity", "dome_size")


class ShowSessionSerializer(serializers.ModelSerializer):
    astronomy_show = serializers.PrimaryKeyRelatedField(
        queryset=AstronomyShow.objects.all()
    )
    planetarium_dome = serializers.PrimaryKeyRelatedField(
        queryset=PlanetariumDome.objects.all()
    )

    class Meta:
        model = ShowSession
        fields = (
            "id", "astronomy_show", "planetarium_dome", "show_time", "price"
        )
        read_only_fields = ("id",)

    def validate(self, attrs):

        tmp_instance = ShowSession(**attrs)

        if self.instance:

            tmp_instance.pk = self.instance.pk

            for field in self.instance._meta.fields:
                if field.name not in attrs and not field.primary_key:
                    old_value = getattr(self.instance, field.name)
                    setattr(tmp_instance, field.name, old_value)

        try:
            tmp_instance.full_clean()
        except DjangoValidationError as error:
            raise serializers.ValidationError(error.message_dict)

        return attrs


class ShowSessionListSerializer(ShowSessionSerializer):
    astronomy_show = serializers.SlugRelatedField(
        many=False, read_only=True, slug_field="title"
    )
    planetarium_dome = serializers.SlugRelatedField(
        many=False, read_only=True, slug_field="name"
    )
    price = serializers.SerializerMethodField()

    def get_price(self, obj) -> str:
        return f"${obj.price}"


class ShowSessionDetailSerializer(ShowSessionListSerializer):
    astronomy_show = AstronomyShowListSerializer(many=False, read_only=True)
    planetarium_dome = PlanetariumDomeSerializer(many=False, read_only=True)
