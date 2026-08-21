from django.db import models


class ContactEnquiry(models.Model):
    name         = models.CharField(max_length=150)
    email        = models.EmailField()
    phone        = models.CharField(max_length=20, blank=True)
    organization = models.CharField(max_length=150, blank=True)
    event_type   = models.CharField(max_length=100, blank=True)
    message      = models.TextField()
    created_at   = models.DateTimeField(auto_now_add=True)
    is_read      = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.name} — {self.organization or "No org"} ({self.created_at:%Y-%m-%d})'