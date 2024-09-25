from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from dj_rest_auth.registration.views import SocialLoginView
from django.conf import settings
from django.contrib.auth import login, get_user_model, logout, authenticate
from .serializers import UserSerializer, LoginSerializer, ProfileSerializer

User = get_user_model()


class SignUpView(generics.CreateAPIView):
    """
    회원가입 API View
    userserializer 사용
    """

    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]


class LoginView(APIView):
    """
    로그인 API View
    """

    permission_classes = [AllowAny]
    serializer_class = LoginSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            username = serializer.validated_data["username"]
            password = serializer.validated_data["password"]
            user = authenticate(username=username, password=password)
            if user:
                if user.is_active:
                    login(request, user)
                    return Response(
                        {"detail": "로그인 성공"}, status=status.HTTP_200_OK
                    )
                else:
                    return Response(
                        {"detail": "계정이 비활성화되었습니다."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
            else:
                return Response(
                    {"detail": "잘못된 로그인 정보입니다."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GoogleLoginView(SocialLoginView):
    """
    google 로그인 담당 처리 view
    settings에 callbacks url 설정
    """

    adapter_class = GoogleOAuth2Adapter
    callback_url = settings.GOOGLE_CALLBACK_URI
    client_class = OAuth2Client


class GoogleLoginURLView(APIView):
    """
    Google login URL API view
    """

    permission_classes = [AllowAny]

    def get(self, request):
        adapter = GoogleOAuth2Adapter(request)
        provider = adapter.get_provider()
        app = provider.get_app(request)
        client = OAuth2Client(
            request,
            app.client_id,
            app.secret,
            adapter.access_token_method,
            adapter.access_token_url,
            callback_url=settings.GOOGLE_CALLBACK_URI,
        )
        authorize_url = client.get_redirect_url()
        return Response({"authorization_url": authorize_url}, status=status.HTTP_200_OK)


class GoogleCallbackView(APIView):
    """
    Google callback view
    """

    permission_classes = [AllowAny]

    def get(self, request):
        code = request.GET.get("code", None)
        if code:
            return Response({"code": code}, status=status.HTTP_200_OK)
        return Response(
            {"error": "Code not found."}, status=status.HTTP_400_BAD_REQUEST
        )


class LogoutView(APIView):
    """
    로그아웃 API View
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        logout(request)
        return Response({"detail": "로그아웃 성공"}, status=status.HTTP_200_OK)


class ProfileDetailView(generics.RetrieveAPIView):
    """
    프로필 API view
    profileserializer 사용
    """

    queryset = User.objects.all()
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "username"


class ProfileUpdateView(generics.UpdateAPIView):
    """
    프로필 수정 API view
    """

    queryset = User.objects.all()
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class UserDeactivateView(APIView):
    """
    계정 비활성화 API view
    user.is_active = False로 계정 로그인 불가
    이후 계정을 다시 활성화 가능
    비활성화 유저 로그아웃 처리
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        user.is_active = False
        user.save()
        logout(request)
        return Response(
            {"detail": "귀하의 계정이 비활성화되었으며 로그아웃되었습니다."},
            status=status.HTTP_200_OK,
        )


class UserDeleteView(APIView):
    """
    계정 삭제 API view
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        confirmation code를 받아서 DELETE request
        """
        user = request.user
        confirmation = request.data.get("confirmation", "")

        if confirmation != "DELETE":
            return Response(
                {"detail": "올바른 확인 코드를 입력해주세요."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.delete()
        return Response(
            {"detail": "귀하의 계정이 완전히 삭제되었습니다."},
            status=status.HTTP_200_OK,
        )
