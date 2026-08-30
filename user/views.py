from rest_framework import generics
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.views import TokenRefreshView
from user.serializers import UserSerializer, CustomTokenRefreshSerializer


class CreateUserAPIView(generics.CreateAPIView):
    serializer_class = UserSerializer
    permission_classes = (AllowAny,)
    authentication_classes = ()


class CustomTokenRefreshView(TokenRefreshView):
    """
    Token refresh view utilizing custom logic.
    """
    serializer_class = CustomTokenRefreshSerializer


class ManageUserAPIView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = (IsAuthenticated,)

    def get_object(self):
        return self.request.user
