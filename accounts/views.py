from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from dj_rest_auth.registration.views import SocialLoginView
from django.conf import settings
from django.contrib.auth import login, get_user_model, logout, authenticate
from .serializers import (
    UserSerializer,
    LoginSerializer,
    ProfileSerializer,
    PasswordChangeSerializer,
    ProfileUpdateSerializer,
)

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
            {"error": "코드를 찾을 수 없습니다."}, status=status.HTTP_400_BAD_REQUEST
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

    serializer_class = ProfileUpdateSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        # patch, put 요청 모두 처리
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        # serializer의 save() 메서드를 호출하여 데이터베이스에 변경사항을 저장
        self.perform_update(serializer)

        # 관련 객체들을 미리 가져왔을 때 쓰는 캐시, update되면 cache 비움(최적화)
        if getattr(instance, "_prefetched_objects_cache", None):
            instance._prefetched_objects_cache = {}

        return Response(serializer.data)

    def partial_update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return self.update(request, *args, **kwargs)


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


class PasswordChangeView(generics.UpdateAPIView):
    """
    비밀번호 변경 api view
    serializer 유효성 검사 후 저장
    저장 후 로그아웃 기능
    """

    serializer_class = PasswordChangeSerializer
    permission_classes = [IsAuthenticated]

    def update(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        logout(request)
        return Response(
            {"detail": "패스워드가 올바르게 변경되었습니다. 다시 로그인해주세요."},
            status=status.HTTP_200_OK,
        )
