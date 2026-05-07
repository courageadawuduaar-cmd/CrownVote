from django.contrib import admin
from .models import Category


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display  = ('name', 'event', 'order', 'is_active', 'is_visible', 'total_votes')
    list_filter   = ('is_active', 'event')
    search_fields = ('name',)
    list_editable = ('order', 'is_active', 'is_visible')
    ordering      = ('event', 'order')