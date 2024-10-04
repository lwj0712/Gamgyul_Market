from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib.auth import get_user_model

User = get_user_model()


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    """
    소셜 계정 커스텀
    nickname 필드 필수라 자동 생성
    nickname을 email로부터 자동으로 설정
    """

    def save_user(self, request, sociallogin, form=None):
        """
        save_user() 호출 시 nickname이 없으면 nickname을 email로부터 자동으로 설정
        """
        user = super().save_user(request, sociallogin, form)
        if not user.nickname:
            self.set_nickname(user)
        return user

    def set_nickname(self, user):
        """
        @ 앞 부분으로 nickname 설정
        닉네임 겹치면 숫자 앞에 붙임
        """
        base_nickname = user.email.split("@")[0]
        nickname = base_nickname
        count = 1

        while User.objects.filter(nickname=nickname).exists():
            nickname = f"{base_nickname}{count}"
            count += 1

        user.nickname = nickname
        user.save(update_fields=["nickname"])
