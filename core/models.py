# models.py

from django.db import models
from django.contrib.auth.models import User

class Category(models.Model):
    name = models.CharField(max_length=100)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE)

    def __str__(self):
        return self.name


class Product(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20)
    title = models.CharField(max_length=255)
    description = models.TextField()

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


class TradeRequest(models.Model):
    ACTION_CHOICES = (
        ('take', 'Забрать'),
        ('rent', 'Аренда'),
        ('exchange', 'Обмен'),
    )
    STATUS_CHOICES = (
        ('pending', 'Ожидает'),
        ('accepted', 'Подтверждена'),
        ('rejected', 'Отклонена'),
        ('completed', 'Завершена'),
        ('cancelled', 'Отменена'),
    )

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='requests')
    requester = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_requests')
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_requests')
    action = models.CharField("Действие", max_length=10, choices=ACTION_CHOICES)
    status = models.CharField("Статус", max_length=10, choices=STATUS_CHOICES, default='pending')
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
