from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenVerifyView,
)

from user.views import (
    CreateUserAPIView,
    CustomTokenRefreshView,
    ManageUserAPIView,
)

app_name = "user"

urlpatterns = [
    path("register/", CreateUserAPIView.as_view(), name="create"),
    path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", CustomTokenRefreshView.as_view(), name="token_refresh"),
    path("token/verify/", TokenVerifyView.as_view(), name="token_verify"),
    path("me/", ManageUserAPIView.as_view(), name="manage_user"),
]
