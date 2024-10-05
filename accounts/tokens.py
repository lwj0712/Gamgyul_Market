from rest_framework_simplejwt.tokens import AccessToken
from rest_framework.exceptions import AuthenticationFailed


class CustomAccessToken(AccessToken):
    @classmethod
    def for_user(cls, user):
        """
        주어진 사용자에 대한 액세스 토큰을 생성
        """
        if not user.is_active:
            raise AuthenticationFailed("사용자 계정이 비활성화되었습니다.")

        token = super().for_user(user)

        # 커스텀 클레임 추가
        token["is_active"] = user.is_active

        return token

    def verify(self):
        """
        토큰 검증 시 추가 검사를 수행
        """
        super().verify()

        # 사용자가 여전히 활성 상태인지 확인
        if not self.payload.get("is_active", True):
            raise AuthenticationFailed("사용자 계정이 비활성화되었습니다.")
