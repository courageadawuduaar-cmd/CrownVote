from django.contrib import admin
from .models import Transaction


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display  = ('reference', 'nominee', 'phone_number', 'network', 'amount', 'vote_quantity', 'status', 'created_at')
    list_filter   = ('status', 'network', 'nominee__category__event')
    search_fields = ('reference', 'phone_number', 'nominee__name')
    readonly_fields = ('reference', 'phone_number', 'network', 'amount', 'vote_quantity', 'provider_ref', 'created_at', 'verified_at')
    ordering      = ('-created_at',)

    def has_add_permission(self, request):
        return False  # Transactions only created via payment flow