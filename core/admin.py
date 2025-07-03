# core/admin.py
from django.contrib import admin, messages
from .models import Category, Product, TradeRequest
from .populate_categories import create_categories

class TradeRequestInline(admin.TabularInline):
    model = TradeRequest
    extra = 0
    fields = ('action', 'requester', 'status', 'created_at')
    readonly_fields = ('created_at', 'updated_at')
    can_delete = False
    verbose_name = "Заявка"
    verbose_name_plural = "Заявки по этому товару"

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'user',             # ник пользователя
        'phone',            # телефон
        'type',             # тип (free/exchange)
        'main_category',    # основная категория
        'subcategory',      # подкатегория
        'sub_subcategory',  # под-подкатегория
        'title',            # заголовок
        'description',      # описание
        'status',           # статус заявки
        'created_at',       # дата создания
    )
    list_filter = ('type', 'status', 'main_category')
    search_fields = ('title', 'description', 'user__username', 'phone')
    inlines = [TradeRequestInline]

@admin.register(TradeRequest)
class TradeRequestAdmin(admin.ModelAdmin):
    list_display = ('product', 'action', 'requester', 'owner', 'status', 'created_at')
    list_filter = ('action', 'status')
    search_fields = ('product__title', 'requester__username', 'owner__username')

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent')
    actions = ['load_default_categories']

    def load_default_categories(self, request, queryset):
        create_categories()
        self.message_user(request, "Категории успешно загружены!", level=messages.SUCCESS)
    load_default_categories.short_description = "Загрузить стандартные категории"
