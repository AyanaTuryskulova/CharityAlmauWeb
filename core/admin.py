from django.contrib import admin, messages
from .models import Category, Product, TradeRequest
from .populate_categories import create_categories

# Показываем заявки прямо в карточке товара
class TradeRequestInline(admin.TabularInline):
    model = TradeRequest
    extra = 0
    fields = ('action', 'requester', 'status', 'created_at')
    readonly_fields = ('created_at', 'updated_at')
    can_delete = False
    verbose_name = "Заявка"
    verbose_name_plural = "Заявки по этому товару"

# Админка товаров с возможностью модерации
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'title',
        'user',
        'type',
        'status',
        'is_approved',       # Показываем модерацию
        'main_category',
        'created_at',
    )
    list_filter = ('type', 'status', 'main_category', 'is_approved', 'created_at')  # Фильтр по модерации
    search_fields = ('title', 'description', 'user__username', 'phone')
    list_editable = ('is_approved',)  # Можно редактировать прямо в списке
    inlines = [TradeRequestInline]
    actions = ['approve_selected_products', 'disapprove_selected_products']  # Действия на модерацию
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('user', 'title', 'description', 'type', 'status', 'is_approved')
        }),
        ('Категории', {
            'fields': ('main_category', 'subcategory', 'sub_subcategory')
        }),
        ('Контакты', {
            'fields': ('name', 'phone')
        }),
        ('Медиа', {
            'fields': ('image',)
        }),
        ('Даты', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_at',)

    @admin.action(description="✅ Одобрить выбранные товары")
    def approve_selected_products(self, request, queryset):
        updated = queryset.update(is_approved=True)
        self.message_user(
            request,
            f"✅ {updated} объявлений успешно одобрено.",
            level=messages.SUCCESS
        )
    
    @admin.action(description="❌ Отклонить выбранные товары")
    def disapprove_selected_products(self, request, queryset):
        updated = queryset.update(is_approved=False)
        self.message_user(
            request,
            f"❌ {updated} объявлений отклонено.",
            level=messages.SUCCESS
        )

# Админка заявок
@admin.register(TradeRequest)
class TradeRequestAdmin(admin.ModelAdmin):
    list_display = ('product', 'action', 'requester', 'owner', 'status', 'created_at')
    list_filter = ('action', 'status')
    search_fields = ('product__title', 'requester__username', 'owner__username')

# Админка категорий
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent')
    actions = ['load_default_categories']

    def load_default_categories(self, request, queryset):
        create_categories()
        self.message_user(request, "Категории успешно загружены!", level=messages.SUCCESS)
    load_default_categories.short_description = "Загрузить стандартные категории"
