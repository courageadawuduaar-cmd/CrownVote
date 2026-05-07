from django.db import models
from apps.nominees.models import Nominee


class Transaction(models.Model):
    NETWORK_CHOICES = [
        ('mtn',     'MTN MoMo'),
        ('telecel', 'Telecel Cash'),
        ('airtel',  'AirtelTigo Money'),
    ]
    STATUS_CHOICES = [
        ('pending',  'Pending'),
        ('success',  'Success'),
        ('failed',   'Failed'),
        ('reversed', 'Reversed'),
    ]

    nominee         = models.ForeignKey(Nominee, on_delete=models.CASCADE, related_name='transactions')
    reference       = models.CharField(max_length=100, unique=True)
    phone_number    = models.CharField(max_length=15)
    network         = models.CharField(max_length=10, choices=NETWORK_CHOICES)
    amount          = models.DecimalField(max_digits=10, decimal_places=2)
    vote_quantity   = models.PositiveIntegerField()
    status          = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    provider_ref    = models.CharField(max_length=200, blank=True)  # MoMo transaction ID
    failure_reason  = models.TextField(blank=True)
    created_at      = models.DateTimeField(auto_now_add=True)
    verified_at     = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.reference} | {self.get_status_display()} | ₵{self.amount}"