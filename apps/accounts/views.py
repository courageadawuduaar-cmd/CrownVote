from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages


def login_view(request):
    if request.user.is_authenticated:
        return redirect('/dashboard/')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        user     = authenticate(request, username=username, password=password)

        if user is not None:
            if user.is_active:
                login(request, user)
                messages.success(request, f'Welcome back, {user.username}! 👑')
                next_url = request.GET.get('next', '/dashboard/')
                return redirect(next_url)
            else:
                messages.error(request, 'Your account has been disabled. Contact support.')
        else:
            messages.error(request, 'Invalid username or password.')

    return render(request, 'accounts/login.html')


def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('/')


def contact_view(request):
    submitted = False
    features  = [
        'Custom event page with your branding',
        'Unlimited categories and nominees',
        'MTN MoMo, Telecel & AirtelTigo payments',
        'Real-time live results leaderboard',
        'Organizer dashboard with analytics',
        'WhatsApp sharing links for nominees',
        'Vote audit trail and transaction logs',
        'Event active/pause/end controls',
    ]

    if request.method == 'POST':
        name         = request.POST.get('name', '').strip()
        email        = request.POST.get('email', '').strip()
        phone        = request.POST.get('phone', '').strip()
        organization = request.POST.get('organization', '').strip()
        event_type   = request.POST.get('event_type', '').strip()
        message      = request.POST.get('message', '').strip()

        if name and email and message:
            submitted = True
        else:
            messages.error(request, 'Please fill in all required fields.')

    return render(request, 'accounts/contact.html', {
        'submitted': submitted,
        'features':  features,
    })