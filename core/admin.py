from django.contrib import admin
from django.contrib import messages
from .models import Category, Product
from .populate_categories import create_categories

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'main_category', 'subcategory', 'sub_subcategory', 'created_at')

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent')
    actions = ['load_default_categories']

    def load_default_categories(self, request, queryset):
        create_categories()
        self.message_user(request, "Категории успешно загружены!", level=messages.SUCCESS)

    load_default_categories.short_description = "Загрузить стандартные категории"
