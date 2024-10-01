from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib.auth import get_user_model

User = get_user_model()


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def save_user(self, request, sociallogin, form=None):
        user = super().save_user(request, sociallogin, form)
        if not user.nickname:
            self.set_nickname(user)
        return user

    def set_nickname(self, user):
        base_nickname = user.email.split("@")[0]
        nickname = base_nickname
        count = 1

        while User.objects.filter(nickname=nickname).exists():
            nickname = f"{base_nickname}{count}"
            count += 1

        user.nickname = nickname
        user.save(update_fields=["nickname"])
