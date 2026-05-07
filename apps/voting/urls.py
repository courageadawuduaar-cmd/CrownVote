from django.urls import path
from . import views

app_name = 'voting'

urlpatterns = [
    path('<str:encoded_id>/vote/',              views.vote,             name='vote'),
    path('verify/<str:reference>/',             views.verify_vote,      name='verify'),
    path('success/<str:reference>/',            views.vote_success,     name='success'),
    path('campaign/<slug:slug>-<str:encoded_id>/', views.campaign,     name='campaign'),
    path('webhook/paystack/',                   views.paystack_webhook, name='paystack_webhook'),
    path('status/<str:reference>/',             views.payment_status,   name='status'),
    path('pending/<str:reference>/',            views.payment_pending,  name='pending'),
]