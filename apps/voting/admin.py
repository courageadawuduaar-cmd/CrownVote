from django.contrib import admin
from .models import Vote


@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    list_display  = ('nominee', 'quantity', 'amount_paid', 'ip_address', 'voted_at')
    list_filter   = ('nominee__category__event',)
    search_fields = ('nominee__name',)
    readonly_fields = ('nominee', 'quantity', 'amount_paid', 'ip_address', 'voted_at')
    ordering      = ('-voted_at',)

    def has_add_permission(self, request):
        return False  # Votes only created via payment