from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from .models import Event, HeroVideo, SiteSettings
from apps.nominees.models import Nominee
from apps.categories.models import Category
import json

STEPS = [
    {'icon': '🎯', 'title': 'Choose an Event',   'desc': 'Browse active events and pick the one you want to vote in.'},
    {'icon': '👤', 'title': 'Pick a Nominee',    'desc': 'Browse nominees in each category and choose your favourite.'},
    {'icon': '🗳️', 'title': 'Select Your Votes', 'desc': 'Choose how many votes to cast. ₵1 = 1 vote. No limit!'},
    {'icon': '📱', 'title': 'Pay via MoMo',       'desc': 'Pay instantly with MTN MoMo, Telecel or AirtelTigo Money.'},
    {'icon': '⚡', 'title': 'Votes Added!',       'desc': 'Your votes are credited instantly. Watch the leaderboard update live!'},
]


def home(request):
    active_events = Event.objects.filter(status='active').order_by('-created_at')
    all_events    = Event.objects.exclude(status='draft').order_by('-created_at')
    settings_obj  = SiteSettings.get()

    db_videos = HeroVideo.objects.filter(is_active=True).order_by('order')

    if db_videos.exists():
        use_static = False
        videos     = [v.video.url for v in db_videos]
        slides     = [
            {
                'heading': v.hero_heading,
                'subtext': v.hero_subtext,
            }
            for v in db_videos
        ]
    else:
        use_static = True
        videos     = [
            'images/crownn.mp4',
            'images/crownn1.mp4',
            'images/crownn2.mp4',
        ]
        slides = [{'heading': '', 'subtext': ''}] * len(videos)

    slides_json = json.dumps(slides)

    return render(request, 'events/home.html', {
        'active_events':  active_events,
        'all_events':     all_events,
        'steps':          STEPS,
        'videos':         videos,
        'use_static':     use_static,
        'site_settings':  settings_obj,
        'slides_json':    slides_json,
    })


def event_list(request):
    events = Event.objects.exclude(status='draft').order_by('-created_at')
    return render(request, 'events/event_list.html', {'events': events})


def event_detail(request, slug):
    event      = get_object_or_404(Event, slug=slug)
    categories = event.categories.filter(is_active=True, is_visible=True)
    return render(request, 'events/event_detail.html', {
        'event':      event,
        'categories': categories,
    })


def search(request):
    query      = request.GET.get('q', '').strip()
    events     = []
    nominees   = []
    categories = []

    if query:
        events = Event.objects.exclude(status='draft').filter(
            Q(title__icontains=query) |
            Q(description__icontains=query)
        ).order_by('-created_at')

        categories = Category.objects.filter(
            Q(name__icontains=query),
            is_active=True
        ).select_related('event')

        nominees = Nominee.objects.filter(
            Q(name__icontains=query) |
            Q(bio__icontains=query) |
            Q(short_code__icontains=query),
            is_active=True
        ).select_related('category__event')

    total_results = len(events) + len(nominees) + len(categories)

    return render(request, 'events/search.html', {
        'query':         query,
        'events':        events,
        'nominees':      nominees,
        'categories':    categories,
        'total_results': total_results,
    })