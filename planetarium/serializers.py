from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
from django.db import transaction
from planetarium.models import (
    AstronomyShow,
    PlanetariumDome,
    ShowSession,
    ShowTheme,
    Reservation,
    Ticket
)


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
            "description_themes",
            "duration",
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
        show_time = attrs.get(
            "show_time", getattr(self.instance, "show_time", None)
        )
        astronomy_show = attrs.get(
            "astronomy_show", getattr(self.instance, "astronomy_show", None)
        )
        planetarium_dome = attrs.get(
            "planetarium_dome", getattr(self.instance, "planetarium_dome", None)
        )

        ShowSession.validate_show_session(
            show_time=show_time,
            astronomy_show=astronomy_show,
            planetarium_dome=planetarium_dome,
            error_to_raise=serializers.ValidationError,
            session_pk=self.instance.pk if self.instance else None,
        )

        return attrs


class ShowSessionListSerializer(ShowSessionSerializer):
    astronomy_show = serializers.SlugRelatedField(
        many=False, read_only=True, slug_field="title"
    )
    planetarium_dome = serializers.SlugRelatedField(
        many=False, read_only=True, slug_field="name"
    )
    price = serializers.SerializerMethodField()

    duration = serializers.IntegerField(
        source="astronomy_show.duration", read_only=True
    )

    tickets_available = serializers.IntegerField(read_only=True)

    class Meta:
        model = ShowSession
        fields = (
            "id",
            "show_time",
            "astronomy_show",
            "planetarium_dome",
            "price",
            "tickets_available",
            "duration",
        )

    def get_price(self, obj) -> str:
        return f"${obj.price}"


class TicketSeatsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = ("row", "seat_in_row")


class ShowSessionDetailSerializer(ShowSessionListSerializer):
    astronomy_show = AstronomyShowListSerializer(many=False, read_only=True)
    planetarium_dome = PlanetariumDomeSerializer(many=False, read_only=True)
    taken_places = TicketSeatsSerializer(
        source="tickets",
        many=True,
        read_only=True
    )

    class Meta:
        model = ShowSession
        fields = (
            "id",
            "show_time",
            "astronomy_show",
            "planetarium_dome",
            "price",
            "tickets_available",
            "taken_places",
        )


class TicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = ("id", "row", "seat_in_row", "show_session")
        validators = [
            UniqueTogetherValidator(
                queryset=Ticket.objects.all(),
                fields=["show_session", "row", "seat_in_row"]
            )
        ]

    def validate(self, attrs):
        Ticket.validate_ticket(
            row=attrs["row"],
            seat_in_row=attrs["seat_in_row"],
            planetarium_dome=attrs["show_session"].planetarium_dome,
            error_to_raise=serializers.ValidationError,
        )
        return attrs


class ReservationSerializer(serializers.ModelSerializer):
    tickets = TicketSerializer(many=True, read_only=False, allow_empty=False)

    class Meta:
        model = Reservation
        fields = ("id", "created_at", "tickets")

    def create(self, validated_data):
        with transaction.atomic():
            tickets_data = validated_data.pop("tickets")
            reservation = Reservation.objects.create(**validated_data)

            for ticket_data in tickets_data:
                Ticket.objects.create(reservation=reservation, **ticket_data)

            return reservation


class TicketListSerializer(TicketSerializer):
    show_session = ShowSessionListSerializer(read_only=True)


class ReservationListSerializer(ReservationSerializer):
    tickets = TicketListSerializer(many=True, read_only=True)
