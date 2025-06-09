import json
from channels.generic.websocket import AsyncWebsocketConsumer
from .models import ChatMessage
from django.utils.dateformat import DateFormat
from django.utils.timezone import localtime

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_group_name = 'chat_room' # Static group name for simplicity

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message_text = text_data_json['message']
        user = text_data_json.get('user', 'Anonymous') # Get user, default to Anonymous

        # Create and save ChatMessage model instance
        # Note: Database operations in async consumers should be run in a synchronous context
        chat_message_obj = await self.save_message(user, message_text)

        formatted_timestamp = DateFormat(localtime(chat_message_obj.timestamp)).format("P M d, Y")


        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': chat_message_obj.message,
                'user': chat_message_obj.user,
                'timestamp': formatted_timestamp
            }
        )

    # Receive message from room group
    async def chat_message(self, event):
        message = event['message']
        user = event['user']
        timestamp = event['timestamp']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': message,
            'user': user,
            'timestamp': timestamp
        }))

    # Helper to run sync DB operations
    async def save_message(self, user, message_text):
        # Import ChatMessage here or ensure apps are ready if at module level
        # from .models import ChatMessage
        # For simplicity, assuming ChatMessage is available or use full path
        return await ChatMessage.objects.acreate(user=user, message=message_text)
