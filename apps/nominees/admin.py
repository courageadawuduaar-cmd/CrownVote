from django.contrib import admin
from .models import Nominee


@admin.register(Nominee)
class NomineeAdmin(admin.ModelAdmin):
    list_display  = ('name', 'category', 'total_votes', 'vote_percentage', 'is_featured', 'is_active')
    list_filter   = ('is_active', 'is_featured', 'category__event')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ('is_featured', 'is_active')
    ordering      = ('category', '-is_featured')