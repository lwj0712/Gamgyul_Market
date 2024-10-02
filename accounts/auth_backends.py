from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model


class CustomAuthBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        UserModel = get_user_model()
        try:
            user = UserModel.objects.get(username=username)
        except UserModel.DoesNotExist:
            return None

        # 활성화 프로세스를 위한 특별한 경우 추가
        if password is None and kwargs.get("activate", False):
            return user

        if user.check_password(password):
            return user
        return None
