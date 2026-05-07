from django.db import models
from apps.nominees.models import Nominee


class Vote(models.Model):
    nominee     = models.ForeignKey(Nominee, on_delete=models.CASCADE, related_name='votes')
    quantity    = models.PositiveIntegerField(default=1)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)  # quantity × ₵1
    ip_address  = models.GenericIPAddressField(blank=True, null=True)
    voted_at    = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-voted_at']

    def __str__(self):
        return f"{self.quantity} vote(s) → {self.nominee.name}"

    def save(self, *args, **kwargs):
        self.amount_paid = self.quantity * 1  # ₵1 per vote
        super().save(*args, **kwargs)