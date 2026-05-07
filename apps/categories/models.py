from django.db import models
from apps.events.models import Event


class Category(models.Model):
    event       = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='categories')
    name        = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    order       = models.PositiveIntegerField(default=0)
    is_active   = models.BooleanField(default=True)
    is_visible  = models.BooleanField(default=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering        = ['order', 'name']
        verbose_name_plural = 'Categories'

    def __str__(self):
        return f"{self.event.title} — {self.name}"

    @property
    def total_votes(self):
        return sum(n.total_votes for n in self.nominees.all())