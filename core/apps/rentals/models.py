from django.db import models
from django.contrib.auth.models import User
from core.models import Product


class RentItem(models.Model):
    """Модель аренды товара"""
    STATUS_CHOICES = (
        ('rented', 'Арендуется'),
        ('returned', 'Возвращено'),
        ('cancelled', 'Отменено'),
    )
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='rentals')
    renter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='rented_items')
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_rentals')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='rented')
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField(null=True, blank=True)
    expected_return_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Аренда'
        verbose_name_plural = 'Аренды'
    
    def __str__(self):
        return f"{self.renter.username} арендует {self.product.title} ({self.get_status_display()})"

