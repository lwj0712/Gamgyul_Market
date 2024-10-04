from django.db.models.signals import post_save
from django.dispatch import receiver
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from .models import Alarm
from chat.models import Message
from accounts.models import Follow


@receiver(post_save, sender=Alarm)
def send_alarm_via_websocket(sender, instance, created, **kwargs):
    if created:
        # WebSocket을 통해 실시간 알림 전송
        channel_layer = get_channel_layer()
        recipient_id = str(instance.recipient.id)

        async_to_sync(channel_layer.group_send)(
            f"user_{recipient_id}_alarms",
            {"type": "send_alarm", "alarm": instance.message},
        )


@receiver(post_save, sender=Message)
def create_alarm_for_new_message(sender, instance, created, **kwargs):
    if created:
        # 메시지가 생성될 때 메시지를 보낸 사람을 제외한 모든 참여자에게 알림을 생성
        chat_room = instance.chat_room
        recipients = chat_room.participants.exclude(id=instance.sender.id)

        for recipient in recipients:
            Alarm.objects.create(
                recipient=recipient,  # 메시지를 받는 대상 (참여자)
                sender=instance.sender,  # 메시지를 보낸 사람
                alarm_type="message",
                message=f"{instance.sender.username}님이 새로운 메시지를 보냈습니다.",
                related_object_id=instance.id,
            )
