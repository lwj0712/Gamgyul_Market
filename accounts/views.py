from django.contrib.auth import login, logout, authenticate
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth import get_user_model
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
