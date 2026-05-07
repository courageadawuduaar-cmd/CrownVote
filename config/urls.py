from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/',     admin.site.urls),
    path('',           include('apps.events.urls')),
    path('search/',    include('apps.events.urls')),
    path('voting/',    include('apps.voting.urls')),
    path('results/',   include('apps.results.urls')),
    path('accounts/',  include('apps.accounts.urls')),
    path('dashboard/', include('apps.dashboard.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
