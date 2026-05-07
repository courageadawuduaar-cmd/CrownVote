from django.urls import path
from . import views

app_name = 'results'

urlpatterns = [
    path('',                      views.results_home,  name='home'),
    path('<slug:slug>/',          views.event_results, name='event'),
    path('<slug:slug>/api/',      views.results_api,   name='api'),
]