from django.contrib import admin
from django.utils.html import format_html
from .models import Event, HeroVideo, SiteSettings

# ─────────────────────────────────────────
# Customize Django Admin Branding
# ─────────────────────────────────────────
admin.site.site_header  = '♛ NobleVote Control Panel'
admin.site.site_title   = 'NobleVote Admin'
admin.site.index_title  = 'Welcome to NobleVote Control Panel'


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display  = (
        'title', 'status', 'organizer',
        'commission_rate', 'total_votes',
        'total_revenue', 'net_revenue',
        'show_results'
    )
    list_filter   = ('status',)
    search_fields = ('title', 'organizer__username')
    prepopulated_fields = {'slug': ('title',)}
    list_editable = ('status', 'show_results', 'commission_rate')
    ordering      = ('-created_at',)

    fieldsets = (
        ('Event Info', {
            'fields': ('title', 'slug', 'description', 'banner', 'status', 'show_results')
        }),
        ('Schedule', {
            'fields': ('start_date', 'end_date')
        }),
        ('Organizer & Commission', {
            'fields': ('organizer', 'commission_rate'),
            'description': 'Set the organizer account and commission rate for this event.'
        }),
    )


@admin.register(HeroVideo)
class HeroVideoAdmin(admin.ModelAdmin):
    list_display  = ('title', 'order', 'is_active', 'hero_heading', 'video_preview', 'created_at')
    list_editable = ('order', 'is_active')
    ordering      = ('order',)

    fieldsets = (
        ('Video Info', {
            'fields': ('title', 'video', 'order', 'is_active'),
        }),
        ('Hero Text for this Video', {
            'fields': ('hero_heading', 'hero_subtext'),
            'description': '⚠️ Both fields are required. This text shows on the homepage when this video plays.',
        }),
    )

    def video_preview(self, obj):
        if obj.video:
            from django.utils.html import format_html
            return format_html(
                '<video width="120" height="70" controls style="border-radius:6px;">'
                '<source src="{}" type="video/mp4"></video>',
                obj.video.url
            )
        return '—'
    video_preview.short_description = 'Preview'

    def save_model(self, request, obj, form, change):
        if not obj.hero_heading:
            obj.hero_heading = obj.title
        super().save_model(request, obj, form, change)


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Hero Section', {
            'fields': ('hero_badge', 'hero_title', 'hero_subtitle'),
            'description': 'These control the text shown on the homepage hero section.'
        }),
    )

    def has_add_permission(self, request):
        # Only allow one instance
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False