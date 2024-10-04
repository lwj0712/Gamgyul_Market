import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import async_to_sync


class AlarmConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user_id = self.scope["url_route"]["kwargs"]["user_id"]
        self.room_group_name = f"user_{self.user_id}_alarms"

        # 그룹에 사용자 추가
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

        await self.accept()

        async def disconnect(self, close_code):
            # 그룹에서 사용자 제거
            await self.channel_layer.group_discard(
                self.room_group_name, self.channel_name
            )

        # 알림 메시지 수신 시 실행
        async def send_alarm(self, event):
            alarm = event["alarm"]

            # 메시지를 WebSocket을 통해 클라이언트로 전송
            await self.send(text_data=json.dumps({"alarm": alarm}))
