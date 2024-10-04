from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Alarm
from .serializers import AlarmSerializer


class AlarmListView(generics.ListAPIView):
    """
    현재 로그인한 사용자의 알림 목록을 반환
    """

    serializer_class = AlarmSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Alarm.objects.filter(recipient=self.request.user)


class AlarmDeleteView(generics.DestroyAPIView):
    """
    특정 알림을 삭제
    """

    serializer_class = AlarmSerializer
    permission_classes = [IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        alarm = get_object_or_404(
            Alarm, id=self.kwargs["alarm_id"], recipient=request.user
        )
        alarm.delete()
        return Response({"message": "알림이 삭제되었습니다."}, status=204)


class AlarmBulkDeleteView(generics.DestroyAPIView):
    """
    사용자의 모든 알림을 삭제
    """

    permission_classes = [IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        alarms = Alarm.objects.filter(recipient=request.user)
        alarms_count = alarms.count()
        alarms.delete()
        return Response(
            {"message": f"{alarms_count}개의 알림이 삭제되었습니다."}, status=204
        )
