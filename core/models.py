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
    
    TYPE_CHOICES = (
        ('free', 'Отдаю даром'),
        ('exchange', 'Обмен'),
    )
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)

    main_category = models.ForeignKey('Category', related_name='main_products', on_delete=models.SET_NULL, null=True, blank=True)
    subcategory = models.ForeignKey('Category', related_name='sub_products', on_delete=models.SET_NULL, null=True, blank=True)
    sub_subcategory = models.ForeignKey('Category', related_name='subsub_products', on_delete=models.SET_NULL, null=True, blank=True)

    image = models.ImageField(upload_to='product_images/')
    
    created_at = models.DateTimeField(auto_now_add=True)  # Добавлено поле

    def __str__(self):
        return self.title
