from django.urls import include, path
from rest_framework.routers import DefaultRouter
from planetarium.views import ShowThemeViewSet, AstronomyShowViewSet

app_name = "planetarium"

router = DefaultRouter()
router.register("show-themes", ShowThemeViewSet)
router.register("astronomy-shows", AstronomyShowViewSet)

urlpatterns = [
    path("", include(router.urls)),
]