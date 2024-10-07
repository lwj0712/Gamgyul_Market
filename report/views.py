from rest_framework import generics, permissions
from .models import Report
from .serializers import ReportCreateSerializer


class ReportCreateView(generics.CreateAPIView):
    """신고 생성 뷰"""

    queryset = Report.objects.all()
    serializer_class = ReportCreateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(reporter=self.request.user)
