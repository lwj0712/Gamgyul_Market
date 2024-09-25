from django.urls import path
from . import views

urlpatterns = [
    path("signup/", views.SignUpView.as_view(), name="signup"),
    path("login/", views.LoginView.as_view(), name="login"),
    path("logout/", views.LogoutView.as_view(), name="logout"),
    path(
        "profile/<str:username>/",
        views.ProfileDetailView.as_view(),
        name="profile_detail",
    ),
    path("profile/update/", views.ProfileUpdateView.as_view(), name="profile_update"),
    path("deactivate/", views.UserDeactivateView.as_view(), name="user_deactivate"),
    path("delete/", views.UserDeleteView.as_view(), name="user_delete"),
]
