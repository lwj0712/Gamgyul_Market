from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, SocialAccount, Follow, PrivacySettings


class PrivacySettingsInline(admin.StackedInline):
    """
    프로필 정보 administration
    """

    model = PrivacySettings
    can_delete = False
    verbose_name_plural = "Privacy Setting"


class CustomUserAdmin(UserAdmin):
    list_display = ("email", "username", "temperature")
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (
            "Personal info",
            {"fields": ("username", "profile_image", "temperature", "bio")},
        ),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "username",
                    "password1",
                    "password2",
                    "is_staff",
                    "is_active",
                ),
            },
        ),
    )
    search_fields = ("email", "username")
    ordering = ("email",)
    inlines = (PrivacySettingsInline,)


@admin.register(SocialAccount)
class SocialAccountAdmin(admin.ModelAdmin):
    list_display = ("user", "provider", "uid")
    search_fields = ("user__username", "provider")


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ("follower", "following", "created_at")
    search_fields = ("follower__username", "following__username")


@admin.register(PrivacySettings)
class PrivacySettingsAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "follower_can_see_email",
        "following_can_see_email",
        "others_can_see_email",
    )
    list_filter = (
        "follower_can_see_email",
        "following_can_see_email",
        "others_can_see_email",
    )
    search_fields = ("user__username", "user__email")
