from django.urls import path
from . import views

app_name = "accounts"

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
    path("follow/<int:pk>/", views.FollowView.as_view(), name="follow"),
    path("unfollow/<int:pk>/", views.UnfollowView.as_view(), name="unfollow"),
    path("deactivate/", views.UserDeactivateView.as_view(), name="user_deactivate"),
    path("delete/", views.UserDeleteView.as_view(), name="user_delete"),
    path("google/", views.GoogleLoginView.as_view(), name="google_login"),
    path("google/url/", views.GoogleLoginURLView.as_view(), name="google_login_url"),
    path(
        "google/callback/", views.GoogleCallbackView.as_view(), name="google_callback"
    ),
    path(
        "change-password/", views.PasswordChangeView.as_view(), name="change_password"
    ),
    path(
        "request-reactivation/",
        views.RequestReactivationView.as_view(),
        name="request_reactivation",
    ),
    path(
        "activate/<uidb64>/<token>/",
        views.ActivateAccountView.as_view(),
        name="activate_account",
    ),
]
