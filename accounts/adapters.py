from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib.auth import get_user_model
import uuid

User = get_user_model()


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def populate_user(self, request, sociallogin, data):
        user = super().populate_user(request, sociallogin, data)

        if not user.nickname:
            # Google 이메일의 @ 앞부분을 기본 nickname으로 사용
            base_nickname = data.get("email", "").split("@")[0]
            nickname = base_nickname

            # nickname이 이미 존재하면 유니크한 값이 될 때까지 숫자를 붙임
            counter = 1
            while User.objects.filter(nickname=nickname).exists():
                nickname = f"{base_nickname}{counter}"
                counter += 1

            user.nickname = nickname

        return user
