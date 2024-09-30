from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from dj_rest_auth.registration.views import SocialLoginView
from django.db.models import Q
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
from .serializers import (
    UserSerializer,
    LoginSerializer,
    FollowSerializer,
    ProfileSerializer,
    PasswordChangeSerializer,
    ProfileUpdateSerializer,
    PrivacySettingsSerializer,
    ProfileSearchSerializer,
)
from .models import Follow, PrivacySettings

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
    비활성화된 계정일 시, 재활성화 질문
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

    def post(self, request):
        logout(request)
        return Response({"detail": "로그아웃 성공"}, status=status.HTTP_200_OK)


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
    Google 로그인 URL API view
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


class RequestReactivationView(APIView):
    """
    재활성화 요청 처리 api view
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
    유저 활성화 api view
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


class ProfileDetailView(generics.RetrieveAPIView):
    """
    프로필 API view
    profileserializer 사용
    """

    queryset = User.objects.all()
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "username"

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({"request": self.request})
        return context


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


class PrivacySettingsView(generics.RetrieveUpdateAPIView):
    """
    프로필 보안 설정 API view
    privacysettingsserializer 사용
    """

    serializer_class = PrivacySettingsSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return PrivacySettings.objects.get_or_create(user=self.request.user)[0]

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)


class FollowView(generics.CreateAPIView):
    """
    팔로우 api view
    follow serializer 사용
    create 메서드로 팔로우 기능 구현
    get_or_create로 중복 제거
    """

    serializer_class = FollowSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        following_id = self.kwargs["pk"]
        following_user = User.objects.get(id=following_id)
        Follow.objects.get_or_create(
            follower=self.request.user, following=following_user
        )
        profile_serializer = ProfileSerializer(
            following_user, context={"request": request}
        )
        return Response(profile_serializer.data)


class UnfollowView(generics.DestroyAPIView):
    """
    언팔로우 api view
    destoryAPIView로 DELETE 요청 처리
    """

    queryset = Follow.objects.all()
    permission_classes = [IsAuthenticated]

    def destroy(self, request, *args, **kwargs):
        following_id = self.kwargs["pk"]
        following_user = User.objects.get(id=following_id)
        Follow.objects.filter(
            follower=self.request.user, following=following_user
        ).delete()
        profile_serializer = ProfileSerializer(
            following_user, context={"request": request}
        )
        return Response(profile_serializer.data)


class ProfileSearchView(generics.ListAPIView):
    """
    프로필 검색 api view
    """

    serializer_class = ProfileSearchSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        query = self.request.query_params.get("q", "")
        if query:
            return User.objects.filter(
                Q(username__icontains=query)
                | Q(nickname__icontains=query)
                | Q(email__icontains=query)
            ).distinct()
        return User.objects.none()
