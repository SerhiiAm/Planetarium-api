from rest_framework.viewsets import ModelViewSet

from planetarium.models import ShowTheme
from planetarium.serializers import ShowThemeSerializer


class ShowThemeViewSet(ModelViewSet):
    queryset = ShowTheme.objects.all().order_by("id")
    serializer_class = ShowThemeSerializer
