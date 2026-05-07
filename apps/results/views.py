from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from apps.events.models import Event


def results_home(request):
    events = Event.objects.exclude(status='draft').order_by('-created_at')
    return render(request, 'results/results_home.html', {'events': events})


def event_results(request, slug):
    event      = get_object_or_404(Event, slug=slug)
    categories = event.categories.filter(is_active=True, is_visible=True)
    return render(request, 'results/event_results.html', {
        'event':      event,
        'categories': categories,
    })


def results_api(request, slug):
    """JSON endpoint — polled every 10s for live updates"""
    event      = get_object_or_404(Event, slug=slug)
    categories = event.categories.filter(is_active=True, is_visible=True)

    data = []
    for category in categories:
        nominees = []
        for nominee in category.nominees.filter(is_active=True).order_by('-votes__quantity'):
            nominees.append({
                'id':         nominee.id,
                'name':       nominee.name,
                'photo':      nominee.photo.url if nominee.photo else None,
                'votes':      nominee.total_votes,
                'percentage': nominee.vote_percentage,
                'featured':   nominee.is_featured,
            })
        # Sort by votes descending
        nominees.sort(key=lambda x: x['votes'], reverse=True)
        data.append({
            'id':          category.id,
            'name':        category.name,
            'total_votes': category.total_votes,
            'nominees':    nominees,
        })

    return JsonResponse({
        'event_title':   event.title,
        'total_votes':   event.total_votes,
        'is_active':     event.is_active,
        'categories':    data,
    })