from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, SocialAccount, Follow, PrivacySettings


class PrivacySettingsInline(admin.StackedInline):
    model = PrivacySettings
    can_delete = False
    verbose_name_plural = "Privacy Settings"


class CustomUserAdmin(UserAdmin):
    list_display = ("username", "email", "nickname", "temperature")
    fieldsets = UserAdmin.fieldsets + (
        (
            "Custom fields",
            {
                "fields": (
                    "profile_image",
                    "temperature",
                    "nickname",
                    "bio",
                    "latitude",
                    "longitude",
                )
            },
        ),
    )
    inlines = (PrivacySettingsInline,)


admin.site.register(User, CustomUserAdmin)


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
