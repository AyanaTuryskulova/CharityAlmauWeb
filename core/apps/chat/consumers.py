from channels.generic.websocket import AsyncWebsocketConsumer
import json
from channels.db import database_sync_to_async
from .models import Chat, Message
from django.contrib.auth import get_user_model

User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.chat_id = self.scope['url_route']['kwargs']['chat_id']
        self.group_name = f'chat_{self.chat_id}'

        # Проверим, что пользователь аутентифицирован и является участником чата
        user = self.scope.get('user')
        if not user or user.is_anonymous:
            await self.close()
            return

        is_participant = await self._is_participant(user.id, self.chat_id)
        if not is_participant:
            await self.close()
            return

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    # Receive message from WebSocket
    async def receive(self, text_data=None, bytes_data=None):
        if text_data is None:
            return
        data = json.loads(text_data)
        text = data.get('text', '').strip()
        if not text:
            return

        user = self.scope['user']
        # create message in DB
        message = await self._create_message(user.id, self.chat_id, text)

        payload = {
            'type': 'chat.message',
            'id': message.id,
            'sender': user.username,
            'sender_id': user.id,
            'text': message.text,
            'status': message.status,
            'is_read': message.is_read,
            'created_at': message.created_at.isoformat(),
            'is_own': True,
        }

        # Broadcast to group
        await self.channel_layer.group_send(self.group_name, {
            'type': 'chat_message',
            'message': payload
        })

    # Called by group_send
    async def chat_message(self, event):
        message = event['message']
        # If message sender isn't this consumer's user, mark is_own False
        if message.get('sender') != (self.scope['user'].username if self.scope.get('user') else None):
            message['is_own'] = False
        await self.send(text_data=json.dumps(message))

    @database_sync_to_async
    def _is_participant(self, user_id, chat_id):
        try:
            chat = Chat.objects.get(id=chat_id)
            return chat.participants.filter(id=user_id).exists()
        except Chat.DoesNotExist:
            return False

    @database_sync_to_async
    def _create_message(self, user_id, chat_id, text):
        user = User.objects.get(id=user_id)
        chat = Chat.objects.get(id=chat_id)
        msg = Message.objects.create(chat=chat, sender=user, text=text)
        return msg
