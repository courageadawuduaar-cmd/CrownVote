from django.contrib import admin
from .models import ContactEnquiry


@admin.register(ContactEnquiry)
class ContactEnquiryAdmin(admin.ModelAdmin):
    list_display  = ('name', 'organization', 'email', 'phone', 'created_at', 'is_read')
    list_filter   = ('is_read', 'created_at')
    search_fields = ('name', 'email', 'organization', 'message')