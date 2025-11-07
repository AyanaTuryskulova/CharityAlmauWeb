from django.db import models
from django.contrib.auth.models import User


class Chat(models.Model):
    """Модель чата между пользователями"""
    participants = models.ManyToManyField(User, related_name='chats')
    product = models.ForeignKey('core.Product', on_delete=models.SET_NULL, null=True, blank=True, related_name='chats', verbose_name='Товар')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        participants_list = self.participants.all()[:2]
        names = [p.username for p in participants_list]
        return f"Chat: {', '.join(names)}"

    def get_other_participant(self, user):
        """Получить другого участника чата"""
        return self.participants.exclude(id=user.id).first()


class Message(models.Model):
    """Модель сообщения в чате"""
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    text = models.TextField(blank=True)
    image = models.ImageField(upload_to='chat_images/', blank=True, null=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.sender.username}: {self.text[:50]}"

