from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('',                        views.dashboard,         name='home'),
    path('report/<slug:slug>/',     views.download_report,   name='report'),
    path('organizers/',             views.organizer_list,    name='organizer_list'),
    path('organizers/<int:user_id>/', views.organizer_detail, name='organizer_detail'),
]