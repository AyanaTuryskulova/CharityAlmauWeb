#!/usr/bin/env python3
"""
Integration test: Chat + trade requests (rent via product_action).
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CharityAlmaWeb.settings')
django.setup()

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from core.models import Product, Category, Chat, Message, TradeRequest


class ChatAndTradeIntegrationTest(TestCase):
    """Интеграционный тест: чат и заявки на аренду."""

    def setUp(self):
        self.category = Category.objects.create(name='Test Category')
        self.user1 = User.objects.create_user(
            username='user1',
            password='testpass123',
        )
        self.user2 = User.objects.create_user(
            username='user2',
            password='testpass123',
        )
        self.product = Product.objects.create(
            title='Rental Product',
            description='A product for rent',
            type='rental',
            status='available',
            is_approved=True,
            user=self.user1,
            main_category=self.category,
            phone='+70000000000',
            image=SimpleUploadedFile('test.jpg', b'test', content_type='image/jpeg'),
        )

    def test_01_create_rent_trade_request(self):
        client = Client()
        client.login(username='user2', password='testpass123')
        response = client.get(f'/product/{self.product.id}/rent/')
        self.assertEqual(response.status_code, 302)
        tr = TradeRequest.objects.get(product=self.product, requester=self.user2)
        self.assertEqual(tr.action, 'rent')
        self.assertEqual(tr.status, 'pending')

    def test_02_create_chat(self):
        chat = Chat.objects.create(product=self.product)
        chat.participants.add(self.user1, self.user2)
        self.assertEqual(chat.participants.count(), 2)

    def test_03_create_message(self):
        chat = Chat.objects.create()
        chat.participants.add(self.user1, self.user2)
        message = Message.objects.create(
            chat=chat,
            sender=self.user1,
            text='Hello from user1',
            status='sent',
        )
        self.assertEqual(message.status, 'sent')
        self.assertFalse(message.is_read)

    def test_04_message_status_update(self):
        chat = Chat.objects.create()
        chat.participants.add(self.user1, self.user2)
        message = Message.objects.create(
            chat=chat,
            sender=self.user1,
            text='Message to mark as read',
            status='sent',
        )
        message.status = 'read'
        message.is_read = True
        message.save()
        message.refresh_from_db()
        self.assertEqual(message.status, 'read')
        self.assertTrue(message.is_read)

    def test_05_rent_request_with_chat(self):
        TradeRequest.objects.create(
            product=self.product,
            requester=self.user2,
            owner=self.user1,
            action='rent',
            status='pending',
        )
        chat = Chat.objects.create(product=self.product)
        chat.participants.add(self.user1, self.user2)
        Message.objects.create(
            chat=chat,
            sender=self.user2,
            text='Can I rent this?',
            status='sent',
        )
        Message.objects.create(
            chat=chat,
            sender=self.user1,
            text='Yes, sure!',
            status='sent',
        )
        self.assertEqual(chat.messages.count(), 2)

    def test_06_multiple_messages_in_chat(self):
        chat = Chat.objects.create()
        chat.participants.add(self.user1, self.user2)
        for i in range(5):
            Message.objects.create(
                chat=chat,
                sender=self.user1 if i % 2 == 0 else self.user2,
                text=f'Message {i + 1}',
                status='sent',
            )
        self.assertEqual(chat.messages.count(), 5)
        chat.messages.filter(sender=self.user2).update(status='read', is_read=True)
        self.assertEqual(chat.messages.filter(status='read').count(), 2)


def run_tests():
    from django.test.runner import DiscoverRunner
    runner = DiscoverRunner(verbosity=2)
    test_suite = runner.test_loader.loadTestsFromTestCase(ChatAndTradeIntegrationTest)
    runner.test_runner.run(test_suite)


if __name__ == '__main__':
    run_tests()
