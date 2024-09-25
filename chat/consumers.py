import json
from channels.generic.websocket import AsyncWebsocketConsumer


class ChatConsumer(AsyncWebsocketConsumer):
    # 웹소켓 연결할 때 실행
    async def connect(self):
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group_name = f"chat_{self.room_name}"

        # 방 그룹에 참가
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

        await self.accept()

    # 웹소켓 끊을 때 실행
    async def disconnect(self, close_code):
        # 방 그룹에서 탈퇴
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    # 클라이언트로부터 웹소켓으로 메세지 받을 때 실행
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json["message"]

        # 그룹에 메시지 전송
        await self.channel_layer.group_send(
            self.room_group_name, {"type": "chat_message", "message": message}
        )

    # 그룹에서 메세지 받은 뒤 실행
    async def chat_message(self, event):
        message = event["message"]

        # 클라이언트에게 메시지 다시 전송
        await self.send(text_data=json.dumps({"message": message}))
