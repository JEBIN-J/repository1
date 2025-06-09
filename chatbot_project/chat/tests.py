from django.test import TestCase, Client
from django.urls import reverse
from channels.testing import WebsocketCommunicator
from unittest.mock import patch, AsyncMock # AsyncMock for async methods
from .models import ChatMessage
from .consumers import ChatConsumer
from chatbot_project.asgi import application # Adjusted import for ASGI application
import json

class ChatMessageModelTest(TestCase):
    def test_create_chat_message(self):
        message = ChatMessage.objects.create(user="testuser", message="Hello, world!")
        self.assertEqual(message.user, "testuser")
        self.assertEqual(message.message, "Hello, world!")
        self.assertIsNotNone(message.timestamp)
        self.assertEqual(str(message), "testuser: Hello, world!")

class ChatViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.chat_url = reverse('chat_view')

    def test_chat_view_get(self):
        response = self.client.get(self.chat_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'chat/chat.html')

    @patch('chat.views.get_channel_layer')
    def test_chat_view_post(self, mock_get_channel_layer):
        # Mock the channel layer and its group_send method
        mock_layer = AsyncMock()
        mock_get_channel_layer.return_value = mock_layer

        user = "postuser"
        message_text = "Posting a message"

        response = self.client.post(self.chat_url, {'user': user, 'message': message_text})

        # Check redirect
        self.assertEqual(response.status_code, 302) # Redirects after POST
        self.assertRedirects(response, self.chat_url)

        # Check that group_send was called correctly
        mock_layer.group_send.assert_called_once_with(
            'chat_room',
            {
                'type': 'chat_message',
                'message': message_text,
                'user': user,
            }
        )

class ChatConsumerTest(TestCase):
    async def test_chat_consumer_connect_disconnect(self):
        communicator = WebsocketCommunicator(application, "/ws/chat/")
        connected, subprotocol = await communicator.connect()
        self.assertTrue(connected)
        await communicator.disconnect()

    async def test_chat_consumer_receive_and_broadcast(self):
        communicator = WebsocketCommunicator(application, "/ws/chat/")
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        test_user = "consumer_user"
        test_message = "Hello from consumer test"

        # Send a message to the consumer
        await communicator.send_json_to({
            'user': test_user,
            'message': test_message
        })

        # Receive the broadcasted message
        response = await communicator.receive_json_from()

        self.assertEqual(response['user'], test_user)
        self.assertEqual(response['message'], test_message)
        self.assertIn('timestamp', response) # Timestamp is added by consumer

        # Verify message was saved to the database
        # Ensure this check happens after the consumer has processed and saved the message.
        # The consumer's save_message is async, so the broadcast happening implies saving is done.
        message_exists = await ChatMessage.objects.filter(user=test_user, message=test_message).aexists()
        self.assertTrue(message_exists)

        await communicator.disconnect()

    async def test_chat_consumer_receive_saves_message(self):
        communicator = WebsocketCommunicator(application, "/ws/chat/")
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        test_user = "db_user"
        test_message_db = "This message should be saved."

        await communicator.send_json_to({
            'user': test_user,
            'message': test_message_db
        })

        # Wait for the broadcast to ensure processing is complete
        await communicator.receive_json_from()

        # Check database
        saved_message = await ChatMessage.objects.aget(user=test_user, message=test_message_db)
        self.assertIsNotNone(saved_message)
        self.assertEqual(saved_message.user, test_user)
        self.assertEqual(saved_message.message, test_message_db)

        await communicator.disconnect()
