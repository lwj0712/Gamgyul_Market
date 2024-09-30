from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [
    # 계정 생성 및 인증
    path("signup/", views.SignUpView.as_view(), name="signup"),
    path("login/", views.LoginView.as_view(), name="login"),
    path("logout/", views.LogoutView.as_view(), name="logout"),
    path(
        "change-password/", views.PasswordChangeView.as_view(), name="change_password"
    ),
    # 소셜 로그인 (Google)
    path("google/", views.GoogleLoginView.as_view(), name="google_login"),
    path("google/url/", views.GoogleLoginURLView.as_view(), name="google_login_url"),
    path(
        "google/callback/", views.GoogleCallbackView.as_view(), name="google_callback"
    ),
    # 계정 관리
    path("deactivate/", views.UserDeactivateView.as_view(), name="user_deactivate"),
    path("delete/", views.UserDeleteView.as_view(), name="user_delete"),
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
    # 프로필 관련
    path(
        "profile/<str:username>/",
        views.ProfileDetailView.as_view(),
        name="profile_detail",
    ),
    path("profile/update/", views.ProfileUpdateView.as_view(), name="profile_update"),
    path(
        "privacy-settings/",
        views.PrivacySettingsView.as_view(),
        name="privacy_settings",
    ),
    path("follow/<int:pk>/", views.FollowView.as_view(), name="follow"),
    path("unfollow/<int:pk>/", views.UnfollowView.as_view(), name="unfollow"),
    # 프로필 검색
    path("search/", views.ProfileSearchView.as_view(), name="profile_search"),
]
