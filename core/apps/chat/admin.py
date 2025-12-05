from django.contrib import admin
from .models import Chat, Message


@admin.register(Chat)
class ChatAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_participants', 'product', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at', 'product')
    search_fields = ('participants__username', 'product__title')
    filter_horizontal = ('participants',)
    readonly_fields = ('created_at', 'updated_at')
    
    def get_participants(self, obj):
        return ", ".join([p.username for p in obj.participants.all()])
    get_participants.short_description = 'Участники'


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'chat', 'sender', 'text_preview', 'has_image', 'is_read', 'created_at')
    list_filter = ('is_read', 'created_at', 'chat')
    search_fields = ('text', 'sender__username')
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'
    
    def text_preview(self, obj):
        return obj.text[:50] + "..." if obj.text and len(obj.text) > 50 else (obj.text if obj.text else "(изображение)")
    text_preview.short_description = 'Текст'
    
    def has_image(self, obj):
        return "Да" if obj.image else "Нет"
    has_image.short_description = 'Есть изображение'

