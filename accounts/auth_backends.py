from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model


class CustomAuthBackend(ModelBackend):
    """
    authenticate 메서드는 is_active=False면 user 인식 불가
    is_active = False여도 check_password 하고 user 인식
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        UserModel = get_user_model()
        try:
            user = UserModel.objects.get(username=username)
        except UserModel.DoesNotExist:
            return None

        if password is None and kwargs.get("activate", False):
            return user

        if user.check_password(password):
            return user
        return None
