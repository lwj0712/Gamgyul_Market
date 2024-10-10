from django.db.models.signals import post_save
from django.dispatch import receiver
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from accounts.models import Follow
from alarm.models import Alarm
from chat.models import Message, WebSocketConnection
from insta.models import Comment, Like


@receiver(post_save, sender=Alarm)
def send_alarm_via_websocket(sender, instance, created, **kwargs):
    if created:
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
            # 사용자의 마지막 WebSocket 연결 종료 시간을 가져옴
            last_connection = (
                WebSocketConnection.objects.filter(user=recipient, chat_room=chat_room)
                .order_by("-disconnected_at")
                .first()
            )

            # WebSocket 연결 기록이 없으면 (None) 알림 생성
            if not last_connection:
                # 연결 기록이 없으므로 알림 생성
                alarm = Alarm.objects.create(
                    recipient=recipient,
                    sender=instance.sender,
                    alarm_type="message",
                    message=f"{instance.sender.username}님이 새로운 메시지를 보냈습니다.",
                    related_object_id=instance.id,
                )
                send_alarm_via_websocket(Alarm, alarm, created=True)
                continue

            # 마지막 연결 종료 시간이 없는 경우(연결이 유지되고 있는 경우), 알림을 생성하지 않음
            if last_connection.disconnected_at is None:
                # 사용자가 여전히 연결 중이므로 알림을 생성하지 않음
                continue

            # 마지막 연결 종료 이후에 메시지가 생성된 경우, 알림을 생성함
            if last_connection.disconnected_at < instance.sent_at:
                alarm = Alarm.objects.create(
                    recipient=recipient,
                    sender=instance.sender,
                    alarm_type="message",
                    message=f"{instance.sender.username}님이 새로운 메시지를 보냈습니다.",
                    related_object_id=instance.id,
                )
                send_alarm_via_websocket(Alarm, alarm, created=True)


@receiver(post_save, sender=Follow)
def create_alarm_for_new_follower(sender, instance, created, **kwargs):
    """
    새로운 팔로우가 발생할 때 알림을 생성하는 신호
    """
    if created:
        recipient = instance.following
        sender = instance.follower

        Alarm.objects.create(
            recipient=recipient,
            sender=sender,
            alarm_type="follow",
            message=f"{sender.username}님이 당신을 팔로우했습니다.",
            related_object_id=None,  # 팔로우는 연결된 객체가 없으므로 None
        )


@receiver(post_save, sender=Comment)
def create_alarm_for_new_comment(sender, instance, created, **kwargs):
    """
    새로운 댓글이 달렸을 때 알림을 생성하는 신호
    """
    if created:
        recipient = instance.post.user
        sender = instance.user

        Alarm.objects.create(
            recipient=recipient,
            sender=sender,
            alarm_type="comment",
            message=f"{sender.username}님이 게시물에 댓글을 남겼습니다.",
            related_object_id=instance.post.id,
        )


@receiver(post_save, sender=Like)
def create_alarm_for_new_like(sender, instance, created, **kwargs):
    """
    좋아요가 눌렸을 때 알림을 생성하는 신호
    """
    if created:
        recipient = instance.post.user
        sender = instance.user

        Alarm.objects.create(
            recipient=recipient,
            sender=sender,
            alarm_type="like",
            message=f"{sender.username}님이 게시물을 좋아합니다.",
            related_object_id=instance.post.id,
        )
