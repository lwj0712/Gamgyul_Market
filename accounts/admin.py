from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, SocialAccount, Follow, PrivacySettings


class PrivacySettingsInline(admin.StackedInline):
    model = PrivacySettings
    can_delete = False
    verbose_name_plural = "Privacy Settings"


class CustomUserAdmin(UserAdmin):
    list_display = ("username", "email", "is_staff")
    list_filter = ("is_staff", "is_superuser", "is_active", "groups")
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("Personal info", {"fields": ("email", "profile_image", "bio")}),
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
                "fields": ("username", "email", "password1", "password2"),
            },
        ),
    )
    search_fields = ("username", "email")
    ordering = ("username",)
    inlines = (PrivacySettingsInline,)


@admin.register(SocialAccount)
class SocialAccountAdmin(admin.ModelAdmin):
    list_display = ("user", "provider", "uid")
    search_fields = ("user__username", "user__email", "provider")


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ("follower", "following", "created_at")
    search_fields = ("follower__username", "following__username")


admin.site.register(User, CustomUserAdmin)
