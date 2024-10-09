from django.conf import settings
from django.contrib.auth import login, get_user_model, logout, authenticate
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.urls import reverse
from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from drf_spectacular.utils import (
    extend_schema,
    OpenApiParameter,
    OpenApiExample,
    OpenApiResponse,
)
from drf_spectacular.types import OpenApiTypes
from accounts.serializers import (
    UserSerializer,
    CustomLoginSerializer,
    CustomPasswordChangeSerializer,
)
from accounts.auth_backends import CustomAuthBackend

User = get_user_model()


class SignUpView(generics.CreateAPIView):

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
                description="사용자 이름, 이메일, 비밀번호를 사용한 기본 회원가입 예시",
                value={
                    "username": "newuser",
                    "email": "newuser@example.com",
                    "password": "securepassword123",
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

    permission_classes = [AllowAny]
    serializer_class = CustomLoginSerializer

    @extend_schema(
        summary="사용자 로그인",
        description="사용자 이름과 비밀번호를 사용하여 로그인합니다. 비활성화된 계정의 경우 재활성화 옵션을 제공합니다.",
        request=CustomLoginSerializer,
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
        """
        serializer 값 받아 유효성 검사
        비활성화 유저 로그인 시 재활성화 질문
        """
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data["email"]
            password = serializer.validated_data["password"]
            user = authenticate(request, email=email, password=password)
            if user is not None:
                if user.is_active:
                    login(request, user)
                    return Response(
                        {"detail": "로그인 성공", "username": user.username},
                        status=status.HTTP_200_OK,
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


class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)


class LogoutView(APIView):

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

    serializer_class = CustomPasswordChangeSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="비밀번호 변경",
        description="현재 인증된 사용자의 비밀번호를 변경합니다. 변경 후 자동으로 로그아웃됩니다.",
        request=CustomPasswordChangeSerializer,
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
                        "non_field_errors": {
                            "type": "array",
                            "items": {"type": "string"},
                        },  # 이전과 새 비밀번호가 동일할 때 특정 필드에 속하지 X
                    },
                },
            ),
            status.HTTP_401_UNAUTHORIZED: OpenApiResponse(
                description="인증되지 않은 사용자",
            ),
        },
        examples=[
            OpenApiExample(
                "유효한 입력",
                value={
                    "old_password": "current_password123",
                    "new_password": "securepassword456",
                },
                request_only=True,
            ),
            OpenApiExample(
                "성공 응답",
                value={
                    "detail": "패스워드가 올바르게 변경되었습니다. 다시 로그인해주세요."
                },
                response_only=True,
            ),
            OpenApiExample(
                "오류: 동일한 비밀번호",
                value={
                    "non_field_errors": "새 비밀번호는 이전 비밀번호와 달라야 합니다."
                },
                response_only=True,
            ),
            OpenApiExample(
                "오류: 이전 비밀번호가 올바르지 않음",
                value={"old_password": "이전 비밀번호가 올바르지 않습니다."},
                response_only=True,
            ),
        ],
        tags=["account"],
    )
    def put(self, request, *args, **kwargs):
        """
        serializer 유효성 검사 통과 시 비밀번호 업데이트
        업데이트 후 로그아웃
        """
        serializer = self.serializer_class(
            data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            serializer.save()
            logout(request)
            return Response(
                {"detail": "패스워드가 올바르게 변경되었습니다. 다시 로그인해주세요."},
                status=status.HTTP_200_OK,
            )
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserDeactivateView(APIView):

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="사용자 계정 비활성화",
        description="현재 로그인된 사용자의 계정을 비활성화하고 로그아웃합니다. 비활성화된 계정은 나중에 다시 활성화할 수 있습니다.",
        request=None,
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
        """
        user.is_active = False로 계정 로그인 불가
        비활성화 유저 로그아웃 처리
        """
        user = request.user
        user.is_active = False
        user.save()
        logout(request)
        return Response(
            {"detail": "귀하의 계정이 비활성화되었으며 로그아웃되었습니다."},
            status=status.HTTP_200_OK,
        )


class RequestReactivationView(APIView):

    @extend_schema(
        summary="계정 재활성화 요청",
        description="비활성화된 계정(일반 및 소셜 로그인)에 대해 재활성화 링크를 이메일로 전송합니다.",
        request={
            "application/json": {
                "type": "object",
                "properties": {"email": {"type": "string", "format": "email"}},
                "required": ["email"],
            }
        },
        responses={
            200: OpenApiTypes.OBJECT,
            400: OpenApiTypes.OBJECT,
        },
        examples=[
            OpenApiExample(
                "유효한 요청",
                summary="유효한 요청 예시",
                description="비활성화된 계정의 이메일 주소",
                value={"email": "user@example.com"},
                request_only=True,
            ),
            OpenApiExample(
                "성공 응답",
                summary="성공 응답 예시",
                description="재활성화 링크 전송 성공",
                value={"detail": "재활성화 링크가 이메일로 전송되었습니다."},
                response_only=True,
                status_codes=["200"],
            ),
            OpenApiExample(
                "계정 없음",
                summary="에러 응답 예시",
                description="계정을 찾을 수 없는 경우",
                value={"detail": "해당 이메일의 비활성화된 계정을 찾을 수 없습니다."},
                response_only=True,
                status_codes=["400"],
            ),
        ],
        tags=["account"],
    )
    def post(self, request):
        """
        비활성화 유저의 메일 정보 받아옴
        토큰 발행으로 인증 구현
        인코딩으로 데이터 압축
        """
        email = request.data.get("email")
        try:
            user = User.objects.get(email=email, is_active=False)
        except User.DoesNotExist:
            return Response(
                {"detail": "해당 이메일의 비활성화된 계정을 찾을 수 없습니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        activation_link = request.build_absolute_uri(
            reverse("accounts:activate_account", kwargs={"uidb64": uid, "token": token})
        )
        send_mail(
            "계정 재활성화",
            f"계정을 재활성화하려면 다음 링크를 클릭하세요: {activation_link}",
            settings.DEFAULT_FROM_EMAIL,
            [email],
            fail_silently=False,
        )

        return Response(
            {"detail": "재활성화 링크가 이메일로 전송되었습니다."},
            status=status.HTTP_200_OK,
        )


class ActivateAccountView(APIView):

    @extend_schema(
        summary="계정 활성화",
        description="이메일로 전송된 링크를 통해 비활성화된 계정을 활성화합니다.",
        parameters=[
            OpenApiParameter(
                name="uidb64",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.PATH,
                description="Base64로 인코딩된 사용자 ID",
            ),
            OpenApiParameter(
                name="token",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.PATH,
                description="계정 활성화를 위한 토큰",
            ),
        ],
        responses={
            200: OpenApiTypes.OBJECT,
            400: OpenApiTypes.OBJECT,
        },
        examples=[
            OpenApiExample(
                "성공 응답",
                value={"detail": "계정이 성공적으로 재활성화되었습니다."},
                response_only=True,
                status_codes=["200"],
            ),
            OpenApiExample(
                "활성화 실패 응답",
                value={"detail": "유효하지 않은 활성화 링크입니다."},
                response_only=True,
                status_codes=["400"],
            ),
        ],
        tags=["account"],
    )
    def get(self, request, uidb64, token):
        """
        유저 활성화 API View
        전달 받은 uid 디코딩으로 원래 형태로 저장
        토큰 유효성 검사 이후 활성화 True로 바꿈
        값을 받아올 때 CustomAuth로 백엔드 지정해서 백엔드 중복 문제 해결
        비밀번호 확인 뛰어넘기, 이미 로그인할 때 확인했음
        """

        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user is not None and default_token_generator.check_token(user, token):
            user.is_active = True
            user.save()
            backend = CustomAuthBackend()
            authenticated_user = backend.authenticate(
                request, email=user.email, password=None, activate=True
            )

            if authenticated_user:
                login(
                    request,
                    authenticated_user,
                    backend="accounts.auth_backends.CustomAuthBackend",
                )
                return Response(
                    {"detail": "계정이 성공적으로 재활성화되었습니다."},
                    status=status.HTTP_200_OK,
                )
            else:
                return Response(
                    {"detail": "계정은 활성화되었지만 로그인에 실패했습니다."},
                    status=status.HTTP_200_OK,
                )
        else:
            return Response(
                {"detail": "유효하지 않은 활성화 링크입니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )


class UserDeleteView(APIView):

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="계정 삭제",
        description="사용자 계정을 완전히 삭제합니다. 삭제를 확인하기 위해 'DELETE'라는 확인 코드가 필요합니다.",
        request={
            "application/json": {
                "type": "object",
                "properties": {
                    "confirmation": {
                        "type": "string",
                        "description": "계정 삭제 확인 코드. 'DELETE'여야 합니다.",
                    }
                },
                "required": ["confirmation"],
            }
        },
        responses={
            200: OpenApiTypes.OBJECT,
            400: OpenApiTypes.OBJECT,
        },
        examples=[
            OpenApiExample(
                "유효한 입력",
                value={"confirmation": "DELETE"},
                request_only=True,
            ),
            OpenApiExample(
                "성공 응답",
                value={"detail": "귀하의 계정이 완전히 삭제되었습니다."},
                response_only=True,
                status_codes=["200"],
            ),
            OpenApiExample(
                "잘못된 확인 코드",
                value={"detail": "올바른 확인 코드를 입력해주세요."},
                response_only=True,
                status_codes=["400"],
            ),
        ],
        tags=["account"],
    )
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
