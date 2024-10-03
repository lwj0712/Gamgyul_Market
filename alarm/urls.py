from django.urls import path
from . import views

app_name = "alarm"

urlpatterns = [
    path("", views.AlarmListView.as_view(), name="alarm_list"),
    path(
        "<uuid:alarm_id>/read/",
        views.AlarmReadView.as_view(),
        name="alarm_read",
    ),  # 특정 알림을 읽음 상태로 바꾸는 url
]
