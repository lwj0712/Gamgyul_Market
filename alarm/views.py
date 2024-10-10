from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiResponse
from alarm.models import Alarm
from alarm.serializers import AlarmSerializer


class AlarmListView(generics.ListAPIView):
    serializer_class = AlarmSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="사용자의 알림 목록 조회",
        description="로그인한 사용자가 받은 모든 알림 목록을 조회합니다.",
        responses={
            200: AlarmSerializer(many=True),
            401: OpenApiResponse(
                description="인증되지 않은 사용자입니다.",
                examples=[{"detail": "인증 자격 증명이 제공되지 않았습니다."}],
            ),
        },
        tags=["alarm"],
    )
    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Alarm.objects.none()
        return Alarm.objects.filter(recipient=self.request.user)


class AlarmDeleteView(generics.DestroyAPIView):
    serializer_class = AlarmSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="특정 알림 삭제",
        description="특정 ID를 가진 알림을 삭제합니다.",
        responses={
            204: OpenApiResponse(
                description="알림이 성공적으로 삭제되었습니다.",
                examples=[{"message": "알림이 삭제되었습니다."}],
            ),
            404: OpenApiResponse(
                description="알림을 찾을 수 없습니다.",
                examples=[{"detail": "알림을 찾을 수 없습니다."}],
            ),
            401: OpenApiResponse(
                description="인증되지 않은 사용자입니다.",
                examples=[{"detail": "인증 자격 증명이 제공되지 않았습니다."}],
            ),
        },
        tags=["alarm"],
    )
    def delete(self, request, *args, **kwargs):
        alarm = get_object_or_404(
            Alarm, id=self.kwargs["alarm_id"], recipient=request.user
        )
        alarm.delete()
        return Response(
            {"message": "알림이 삭제되었습니다."}, status=status.HTTP_204_NO_CONTENT
        )


class AlarmBulkDeleteView(generics.DestroyAPIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="모든 알림 삭제",
        description="로그인한 사용자의 모든 알림을 삭제합니다.",
        responses={
            204: OpenApiResponse(
                description="모든 알림이 성공적으로 삭제되었습니다.",
                examples=[{"message": "모든 알림이 삭제되었습니다."}],
            ),
            401: OpenApiResponse(
                description="인증되지 않은 사용자입니다.",
                examples=[{"detail": "인증 자격 증명이 제공되지 않았습니다."}],
            ),
        },
        tags=["alarm"],
    )
    def delete(self, request, *args, **kwargs):
        alarms_deleted, _ = Alarm.objects.filter(recipient=request.user).delete()
        return Response(
            {"message": f"{alarms_deleted}개의 알림이 삭제되었습니다."},
            status=status.HTTP_204_NO_CONTENT,
        )
