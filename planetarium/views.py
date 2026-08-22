from rest_framework.viewsets import ModelViewSet
from rest_framework import status
from planetarium.models import ShowTheme, AstronomyShow, PlanetariumDome, ShowSession
from rest_framework.response import Response
from rest_framework.decorators import action
from planetarium.serializers import (
    AstronomyShowDetailSerializer,
    AstronomyShowImageSerializer,
    AstronomyShowListSerializer,
    AstronomyShowSerializer,
    ShowThemeDetailSerializer,
    ShowThemeSerializer,
    PlanetariumDomeSerializer,
    ShowSessionListSerializer,
    ShowSessionDetailSerializer,
    ShowSessionSerializer
)


class ShowThemeViewSet(ModelViewSet):
    queryset = ShowTheme.objects.all().order_by("id")

    def get_serializer_class(self):
        if self.action == "retrieve":
            return ShowThemeDetailSerializer
        return ShowThemeSerializer

    def get_queryset(self):
        queryset = self.queryset
        if self.action == "retrieve":
            return queryset.prefetch_related("astronomy_shows")
        return queryset


class AstronomyShowViewSet(ModelViewSet):
    queryset = AstronomyShow.objects.all()

    @staticmethod
    def _params_to_ints(query_string):
        """Converts a string of format '1,2,3' to a list of integers [1, 2, 3]."""
        return [int(str_id) for str_id in query_string.split(",")]

    def get_serializer_class(self):
        if self.action == "list":
            return AstronomyShowListSerializer
        if self.action == "retrieve":
            return AstronomyShowDetailSerializer
        if self.action == "upload_image":
            return AstronomyShowImageSerializer

        return AstronomyShowSerializer

    def get_queryset(self):
        queryset = self.queryset

        themes = self.request.query_params.get("description_themes")
        if themes:
            theme_ids = self._params_to_ints(themes)
            queryset = queryset.filter(description_themes__id__in=theme_ids)

        title = self.request.query_params.get("title")
        if title:
            queryset = queryset.filter(title__icontains=title)

        if self.action in ("list", "retrieve"):
            return queryset.prefetch_related("description_themes").distinct()

        return queryset.distinct()

    @action(
        methods=["POST"],
        detail=True,
        url_path="upload-image",
    )
    def upload_image(self, request, pk=None):
        astronomy_show = self.get_object()
        serializer = self.get_serializer(astronomy_show, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)


class PlanetariumViewSet(ModelViewSet):
    queryset = PlanetariumDome.objects.all().order_by("id")
    serializer_class = PlanetariumDomeSerializer


class ShowSessionViewSet(ModelViewSet):
    queryset = ShowSession.objects.all()

    def get_serializer_class(self):
        if self.action == "list":
            return ShowSessionListSerializer

        if self.action == "retrieve":
            return ShowSessionDetailSerializer

        return ShowSessionSerializer

    def get_queryset(self):
        queryset = self.queryset
        if self.action in ("list", "retrieve"):
            queryset = queryset.select_related("astronomy_show", "planetarium_dome")
        return queryset
