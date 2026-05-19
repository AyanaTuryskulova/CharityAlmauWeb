# models.py

from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _

class Category(models.Model):
    name = models.CharField(max_length=100)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE)

    def __str__(self):
        return self.name


class Product(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=20)
    title = models.CharField(max_length=255)
    description = models.TextField()

     # Состояние
    CONDITION_CHOICES = (
        ('new', 'Новое'),
        ('good', 'Хорошее'),
        ('defects', 'Есть дефекты'),
    )
    condition = models.CharField(max_length=10, choices=CONDITION_CHOICES, blank=True)
    defects = models.TextField(blank=True)

    # Место передачи
    LOCATION_CHOICES = (
        ('atrium', 'Атриум'),
        ('kainar', 'Кайнар булак'),
        ('dorm', 'Общежитие'),
        ('other', 'Другое'),
    )
    meeting_place = models.CharField(max_length=20, choices=LOCATION_CHOICES, blank=True)
    meeting_place_text = models.CharField(max_length=255, blank=True)

    # Аренда
    price = models.IntegerField(null=True, blank=True)
    rent_period = models.CharField(max_length=10, blank=True)
    min_rent_time = models.CharField(max_length=50, blank=True)
    return_rules = models.TextField(blank=True)

    # Обмен
    exchange_categories = models.JSONField(default=list, blank=True)
    exchange_other = models.CharField(max_length=255, blank=True)

    STATUS_CHOICES = (
        ('available', 'Доступно'),
        ('requested', 'Запрошено'),
        ('exchanged', 'Обмен запрошен'),
        ('taken', 'В ожидании'),
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='available',
        verbose_name='Статус'
    )

    TYPE_CHOICES = (
        ('free', 'Отдаю даром'),
        ('exchange', 'Обмен'),
        ('rental', 'Аренда'),
    )
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)

    main_category = models.ForeignKey(
        'Category',
        related_name='main_products',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    subcategory = models.ForeignKey(
        'Category',
        related_name='sub_products',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    sub_subcategory = models.ForeignKey(
        'Category',
        related_name='subsub_products',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    image = models.ImageField(upload_to='product_images/')
    created_at = models.DateTimeField(auto_now_add=True)

    is_approved = models.BooleanField(default=False, verbose_name='Одобрено модератором')

    def extra_images_list(self):
        """Дополнительные фото (2–5), первое — product.image."""
        return list(self.extra_images.order_by('order', 'id'))

    def __str__(self):
        return self.title


class ProductImage(models.Model):
    """Дополнительные фото объявления (до 5 всего: 1 основное + до 4 здесь)."""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='extra_images')
    image = models.ImageField(upload_to='product_images/')
    order = models.PositiveSmallIntegerField(default=0)

    def __str__(self):
        return f"Фото #{self.order + 2} — {self.product.title}"


class PushSubscription(models.Model):
    """Браузерная push-подписка пользователя."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='push_subscriptions')
    endpoint = models.URLField(max_length=500, unique=True)
    p256dh = models.TextField()
    auth = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'chat_pushsubscription'

    def __str__(self):
        return f'{self.user.username} — {self.endpoint[:60]}'


class ChatParticipant(models.Model):
    chat = models.ForeignKey('Chat', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        db_table = 'chat_chat_participants'
        unique_together = ('chat', 'user')


class Chat(models.Model):
    """Модель чата между пользователями"""
    participants = models.ManyToManyField(User, related_name='chats', through='ChatParticipant')
    product = models.ForeignKey('core.Product', on_delete=models.SET_NULL, null=True, blank=True, related_name='chats', verbose_name='Товар')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'chat_chat'
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
    STATUS_CHOICES = (
        ('sent', 'Отправлено'),
        ('read', 'Прочитано'),
    )
    
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    text = models.TextField(blank=True)
    image = models.ImageField(upload_to='chat_images/', blank=True, null=True)
    is_read = models.BooleanField(default=False)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='sent')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'chat_message'
        ordering = ['created_at']

    def __str__(self):
        return f"{self.sender.username}: {self.text[:50]}"


class UserProfile(models.Model):
    """Профиль пользователя"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    bio = models.TextField(blank=True, null=True, verbose_name='О себе')
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    dark_mode = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'tenant_profile_userprofile'
        verbose_name = 'Профиль пользователя'
        verbose_name_plural = 'Профили пользователей'
    
    def __str__(self):
        return f"Профиль {self.user.username}"


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Автоматически создавать профиль при создании пользователя"""
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Автоматически сохранять профиль при сохранении пользователя"""
    if hasattr(instance, 'profile'):
        instance.profile.save()


class TradeRequest(models.Model):
    ACTION_CHOICES = (
        ('take', _('Забрать')),
        ('rent', _('Аренда')),
        ('exchange', _('Обмен')),
    )
    STATUS_CHOICES = (
        ('pending', _('Ожидает')),
        ('accepted', _('Подтверждено')),
        ('in_progress', _('В аренде')),
        ('rejected', _('Отклонена')),
        ('completed', _('Завершена')),
        ('cancelled', _('Отменена')),
    )

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='requests')
    requester = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_requests')
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_requests')
    desired_categories = models.CharField(max_length=255, blank=True, default='')
    offered_item = models.CharField(max_length=255, blank=True, default='')
    action = models.CharField(_("Действие"), max_length=10, choices=ACTION_CHOICES)
    status = models.CharField(_("Статус"), max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.requester} → {self.product.title} ({self.get_action_display()})"


class Favorite(models.Model):
    """Избранные товары пользователя."""
    user = models.ForeignKey(
        'auth.User',
        on_delete=models.CASCADE,
        related_name='favorites'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='favorited_by'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [['user', 'product']]
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} ♥ {self.product.title}"
