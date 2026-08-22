from django.urls import include, path
from rest_framework.routers import DefaultRouter
from planetarium.views import ShowThemeViewSet, AstronomyShowViewSet, PlanetariumViewSet, ShowSessionViewSet

app_name = "planetarium"

router = DefaultRouter()
router.register("show-themes", ShowThemeViewSet)
router.register("astronomy-shows", AstronomyShowViewSet)
router.register("planetarium-domes", PlanetariumViewSet)
router.register("show-sessions", ShowSessionViewSet)
urlpatterns = [
    path("", include(router.urls)),
]
