from django.urls import path
from . import views

app_name = "alarm"

urlpatterns = [
    path("", views.AlarmListView.as_view(), name="alarm_list"),
    path(
        "<uuid:alarm_id>/delete/", views.AlarmDeleteView.as_view(), name="alarm_delete"
    ),
    path("delete-all/", views.AlarmBulkDeleteView.as_view(), name="alarm_bulk_delete"),
]
