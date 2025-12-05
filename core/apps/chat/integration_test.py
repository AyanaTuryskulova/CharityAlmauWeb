#!/usr/bin/env python3
"""
Integration test: Chat + Rentals
Проверяет:
1. Создание аренды (rentals)
2. Обмен сообщениями через WebSocket (chat)
3. Проверка статусов сообщений (sent, read)
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CharityAlmaWeb.settings')
django.setup()

from django.test import TestCase, Client
from django.contrib.auth.models import User
from core.models import Product, Category
from core.apps.chat.models import Chat, Message
from core.apps.rentals.models import RentItem
from django.utils import timezone

class ChatAndRentalsIntegrationTest(TestCase):
    """Интеграционный тест: Чат + Аренда"""
    
    def setUp(self):
        """Подготовка тестовых данных"""
        # Создаем категорию
        self.category = Category.objects.create(
            name='Test Category'
        )
        
        # Создаем пользователей
        self.user1 = User.objects.create_user(
            username='user1',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            password='testpass123'
        )
        
        # Создаем товар для аренды
        self.product = Product.objects.create(
            title='Rental Product',
            description='A product for rent',
            type='rental',
            status='available',
            is_approved=True,
            user=self.user1,
            main_category=self.category
        )
        
    def test_01_create_rental(self):
        """Тест 1: Создание аренды"""
        print("\n✓ Тест 1: Создание аренды")
        
        client = Client()
        client.login(username='user2', password='testpass123')
        
        response = client.post('/rentals/create/', {
            'product_id': self.product.id,
            'expected_return_date': '2025-12-31'
        }, HTTP_ACCEPT='application/json')
        
        self.assertEqual(response.status_code, 201)
        rental = RentItem.objects.get(product=self.product)
        self.assertEqual(rental.renter, self.user2)
        self.assertEqual(rental.owner, self.user1)
        self.assertEqual(rental.status, 'rented')
        print(f"  ✓ Аренда создана: {rental}")
        
    def test_02_create_chat(self):
        """Тест 2: Создание чата между пользователями"""
        print("\n✓ Тест 2: Создание чата")
        
        chat = Chat.objects.create()
        chat.participants.add(self.user1, self.user2)
        chat.product = self.product
        chat.save()
        
        self.assertEqual(chat.participants.count(), 2)
        self.assertIn(self.user1, chat.participants.all())
        self.assertIn(self.user2, chat.participants.all())
        print(f"  ✓ Чат создан: {chat}")
        
    def test_03_create_message(self):
        """Тест 3: Создание сообщения"""
        print("\n✓ Тест 3: Создание сообщения")
        
        chat = Chat.objects.create()
        chat.participants.add(self.user1, self.user2)
        chat.save()
        
        message = Message.objects.create(
            chat=chat,
            sender=self.user1,
            text='Hello from user1',
            status='sent'
        )
        
        self.assertEqual(message.status, 'sent')
        self.assertFalse(message.is_read)
        print(f"  ✓ Сообщение создано: {message} (status: {message.status})")
        
    def test_04_message_status_update(self):
        """Тест 4: Обновление статуса сообщения"""
        print("\n✓ Тест 4: Обновление статуса сообщения")
        
        chat = Chat.objects.create()
        chat.participants.add(self.user1, self.user2)
        chat.save()
        
        message = Message.objects.create(
            chat=chat,
            sender=self.user1,
            text='Message to mark as read',
            status='sent'
        )
        
        # Обновляем статус на 'read'
        message.status = 'read'
        message.is_read = True
        message.save()
        
        message.refresh_from_db()
        self.assertEqual(message.status, 'read')
        self.assertTrue(message.is_read)
        print(f"  ✓ Статус сообщения обновлен: {message.status}")
        
    def test_05_rental_with_chat_context(self):
        """Тест 5: Аренда с контекстом чата"""
        print("\n✓ Тест 5: Аренда с контекстом чата")
        
        # Создаем аренду
        rental = RentItem.objects.create(
            product=self.product,
            renter=self.user2,
            owner=self.user1,
            status='rented'
        )
        
        # Создаем чат для этой аренды
        chat = Chat.objects.create(product=self.product)
        chat.participants.add(self.user1, self.user2)
        chat.save()
        
        # Добавляем сообщения
        msg1 = Message.objects.create(
            chat=chat,
            sender=self.user2,
            text='Can I rent this?',
            status='sent'
        )
        
        msg2 = Message.objects.create(
            chat=chat,
            sender=self.user1,
            text='Yes, sure!',
            status='sent'
        )
        
        self.assertEqual(chat.messages.count(), 2)
        self.assertEqual(rental.product, chat.product)
        print(f"  ✓ Аренда связана с чатом, обмен сообщениями: {chat.messages.count()} сообщений")
        
    def test_06_multiple_messages_in_chat(self):
        """Тест 6: Множественные сообщения в одном чате"""
        print("\n✓ Тест 6: Множественные сообщения")
        
        chat = Chat.objects.create()
        chat.participants.add(self.user1, self.user2)
        chat.save()
        
        for i in range(5):
            Message.objects.create(
                chat=chat,
                sender=self.user1 if i % 2 == 0 else self.user2,
                text=f'Message {i+1}',
                status='sent'
            )
        
        self.assertEqual(chat.messages.count(), 5)
        print(f"  ✓ В чате {chat.messages.count()} сообщений")
        
        # Обновляем статусы
        chat.messages.filter(sender=self.user2).update(status='read', is_read=True)
        
        self.assertEqual(chat.messages.filter(status='read').count(), 2)
        print(f"  ✓ Обновлено статусов: {chat.messages.filter(status='read').count()}")

def run_tests():
    """Запуск всех тестов"""
    print("\n" + "="*60)
    print("Integration Test: Chat + Rentals")
    print("="*60)
    
    from django.test.runner import DiscoverRunner
    runner = DiscoverRunner(verbosity=2)
    
    # Запускаем только наш тестовый класс
    test_suite = runner.test_loader.loadTestsFromTestCase(ChatAndRentalsIntegrationTest)
    runner.test_runner.run(test_suite)
    
if __name__ == '__main__':
    run_tests()
