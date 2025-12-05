from django.contrib import admin
from .models import RentItem


@admin.register(RentItem)
class RentItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'product', 'renter', 'owner', 'status', 'start_date', 'end_date', 'expected_return_date')
    list_filter = ('status', 'start_date', 'end_date')
    search_fields = ('product__title', 'renter__username', 'owner__username')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'start_date'
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('product', 'renter', 'owner', 'status')
        }),
        ('Даты', {
            'fields': ('start_date', 'end_date', 'expected_return_date')
        }),
        ('Системная информация', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

