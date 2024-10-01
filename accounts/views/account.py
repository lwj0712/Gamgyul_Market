from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from dj_rest_auth.registration.views import SocialLoginView
from drf_spectacular.utils import (
    extend_schema,
    OpenApiParameter,
    OpenApiExample,
    OpenApiResponse,
)
from drf_spectacular.types import OpenApiTypes
from django.views.generic import TemplateView
from django.conf import settings
from django.contrib.auth import login, get_user_model, logout, authenticate
from django.contrib.auth.tokens import (
    default_token_generator,
)  # Django에서 제공하는 토큰 생성기, 보안 관련 작업에 사용, 토큰은 시간이 지나면 만료
from django.utils.http import (
    urlsafe_base64_encode,  # base64_문자열로 인코딩
    urlsafe_base64_decode,  # 문자열을 원래 데이터로 디코팅
)
from django.utils.encoding import (
    force_bytes,  # 주어진 문자열을 바이트 문자열로 변환
    force_str,  # 바이트 문자열을 일반 문자열로 변환
)
from django.core.mail import send_mail  # 이메일 전송 기능
from django.urls import reverse
from accounts.serializers import (
    UserSerializer,
    LoginSerializer,
    PasswordChangeSerializer,
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

    @extend_schema(
        summary="사용자 회원가입",
        description="새로운 사용자 계정을 생성합니다.",
        request=UserSerializer,
        responses={201: UserSerializer},
        examples=[
            OpenApiExample(
                "회원가입 예시",
                summary="기본 회원가입",
                description="사용자 이름, 이메일, 비밀번호, 닉네임을 사용한 기본 회원가입 예시",
                value={
                    "username": "newuser",
                    "email": "newuser@example.com",
                    "password": "securepassword123",
                    "nickname": "New User",
                    "bio": "안녕하세요, 새로운 사용자입니다.",
                },
                request_only=True,
            ),
        ],
        tags=["account"],
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class LoginView(APIView):
    """
    로그인 API View
    비활성화된 계정일 시, 재활성화 질문
    """

    permission_classes = [AllowAny]
    serializer_class = LoginSerializer

    @extend_schema(
        summary="사용자 로그인",
        description="사용자 이름과 비밀번호를 사용하여 로그인합니다. 비활성화된 계정의 경우 재활성화 옵션을 제공합니다.",
        request=LoginSerializer,
        responses={
            200: OpenApiResponse(
                description="로그인 성공",
                response={
                    "type": "object",
                    "properties": {"detail": {"type": "string"}},
                },
            ),
            400: OpenApiResponse(
                description="잘못된 로그인 정보",
                response={
                    "type": "object",
                    "properties": {"detail": {"type": "string"}},
                },
            ),
            403: OpenApiResponse(
                description="비활성화된 계정",
                response={
                    "type": "object",
                    "properties": {
                        "detail": {"type": "string"},
                        "inactive_account": {"type": "boolean"},
                        "email": {"type": "string"},
                    },
                },
            ),
        },
        tags=["account"],
    )
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            username = serializer.validated_data["username"]
            password = serializer.validated_data["password"]
            user = authenticate(username=username, password=password)
            if user is not None:
                if user.is_active:
                    login(request, user)
                    return Response(
                        {"detail": "로그인 성공"}, status=status.HTTP_200_OK
                    )
                else:
                    return Response(
                        {
                            "detail": "계정이 비활성화되어 있습니다. 재활성화하시겠습니까?",
                            "inactive_account": True,
                            "email": user.email,
                        },
                        status=status.HTTP_403_FORBIDDEN,
                    )
            else:
                return Response(
                    {"detail": "잘못된 로그인 정보입니다."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    """
    로그아웃 API View
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="로그아웃",
        description="현재 인증된 사용자의 로그아웃을 처리합니다.",
        request=None,
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="로그아웃 성공",
                response={
                    "type": "object",
                    "properties": {"detail": {"type": "string"}},
                },
            ),
            status.HTTP_401_UNAUTHORIZED: OpenApiResponse(
                description="인증되지 않은 사용자",
            ),
        },
        tags=["account"],
    )
    def post(self, request):
        logout(request)
        return Response({"detail": "로그아웃 성공"}, status=status.HTTP_200_OK)


class PasswordChangeView(APIView):
    """
    비밀번호 변경 API View
    serializer 유효성 검사 후 저장
    저장 후 로그아웃 기능
    """

    serializer_class = PasswordChangeSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="비밀번호 변경",
        description="현재 인증된 사용자의 비밀번호를 변경합니다. 변경 후 자동으로 로그아웃됩니다.",
        request=PasswordChangeSerializer,
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="비밀번호 변경 성공",
                response={
                    "type": "object",
                    "properties": {"detail": {"type": "string"}},
                },
            ),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                description="잘못된 요청 (유효하지 않은 데이터)",
                response={
                    "type": "object",
                    "properties": {
                        "old_password": {"type": "array", "items": {"type": "string"}},
                        "new_password": {"type": "array", "items": {"type": "string"}},
                    },
                },
            ),
            status.HTTP_401_UNAUTHORIZED: OpenApiResponse(
                description="인증되지 않은 사용자",
            ),
        },
        examples=[
            OpenApiExample(
                "Valid Input",
                value={
                    "old_password": "current_password123",
                    "new_password": "securepassword456",
                },
                request_only=True,
            ),
            OpenApiExample(
                "Success Response",
                value={
                    "detail": "패스워드가 올바르게 변경되었습니다. 다시 로그인해주세요."
                },
                response_only=True,
            ),
        ],
        tags=["account"],
    )
    def put(self, request, *args, **kwargs):
        serializer = self.serializer_class(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        logout(request)
        return Response(
            {"detail": "패스워드가 올바르게 변경되었습니다. 다시 로그인해주세요."},
            status=status.HTTP_200_OK,
        )


class UserDeactivateView(APIView):
    """
    계정 비활성화 API View
    user.is_active = False로 계정 로그인 불가
    이후 계정을 다시 활성화 가능
    비활성화 유저 로그아웃 처리
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="사용자 계정 비활성화",
        description="현재 로그인된 사용자의 계정을 비활성화하고 로그아웃합니다. 비활성화된 계정은 나중에 다시 활성화할 수 있습니다.",
        responses={
            200: OpenApiResponse(
                description="계정 비활성화 성공",
                response={
                    "type": "object",
                    "properties": {
                        "detail": {
                            "type": "string",
                            "example": "귀하의 계정이 비활성화되었으며 로그아웃되었습니다.",
                        }
                    },
                },
            ),
            401: OpenApiResponse(description="인증되지 않은 사용자"),
        },
        tags=["account"],
    )
    def post(self, request):
        user = request.user
        user.is_active = False
        user.save()
        logout(request)
        return Response(
            {"detail": "귀하의 계정이 비활성화되었으며 로그아웃되었습니다."},
            status=status.HTTP_200_OK,
        )


class RequestReactivationView(APIView):
    """
    재활성화 요청 처리 API View
    """

    def post(self, request):
        email = request.data.get("email")  # email get으로 받아오기
        try:
            user = User.objects.get(
                email=email, is_active=False
            )  # 비활성화 유저의 메일이라면 받아옴
        except User.DoesNotExist:
            return Response(
                {"detail": "해당 이메일의 비활성화된 계정을 찾을 수 없습니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        token = default_token_generator.make_token(user)  # 토큰 발행
        uid = urlsafe_base64_encode(force_bytes(user.pk))  # 인코딩
        activation_link = request.build_absolute_uri(
            reverse(
                "activate_account", kwargs={"uidb64": uid, "token": token}
            )  # activate account에 해당하는 url 패턴에 uid, token 전달
        )
        # 이메일 보냄
        send_mail(
            "계정 재활성화",
            f"계정을 재활성화하려면 다음 링크를 클릭하세요: {activation_link}",
            settings.DEFAULT_FROM_EMAIL,  # 발신자
            [email],  # 수신자
            fail_silently=False,
        )

        return Response(
            {"detail": "재활성화 링크가 이메일로 전송되었습니다."},
            status=status.HTTP_200_OK,
        )


class ActivateAccountView(APIView):
    """
    유저 활성화 API View
    전달받은 uid 디코딩
    토큰 유효성 검사 이후 활성화 True로 바꿈
    """

    def get(self, request, uidb64, token):

        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user is not None and default_token_generator.check_token(user, token):
            user.is_active = True
            user.save()
            login(request, user)  # 바로 로그인
            return Response(
                {"detail": "계정이 성공적으로 재활성화되었습니다."},
                status=status.HTTP_200_OK,
            )
        else:
            return Response(
                {"detail": "유효하지 않은 활성화 링크입니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )


class UserDeleteView(APIView):
    """
    계정 삭제 API View
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


class GoogleLoginTestView(TemplateView):
    template_name = "accounts/google_login_test.html"
