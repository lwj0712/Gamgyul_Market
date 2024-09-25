from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, SocialAccount, Follow


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


admin.site.register(User, CustomUserAdmin)


@admin.register(SocialAccount)
class SocialAccountAdmin(admin.ModelAdmin):
    list_display = ("user", "provider", "uid")
    search_fields = ("user__username", "provider")


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ("follower", "following", "created_at")
    search_fields = ("follower__username", "following__username")
