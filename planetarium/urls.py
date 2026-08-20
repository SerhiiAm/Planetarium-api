from django.urls import include, path
from rest_framework.routers import DefaultRouter
from planetarium.views import ShowThemeViewSet

app_name = "planetarium"

router = DefaultRouter()
router.register("show-themes", ShowThemeViewSet)

urlpatterns = [
    path("", include(router.urls)),
]