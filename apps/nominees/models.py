from django.db import models
from django.utils.crypto import get_random_string


def generate_short_code():
    """Generate unique 6-char alphanumeric code e.g. CV7K2X"""
    while True:
        code = 'CV' + get_random_string(4, 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789')
        if not Nominee.objects.filter(short_code=code).exists():
            return code


class Nominee(models.Model):
    category    = models.ForeignKey('categories.Category', on_delete=models.CASCADE, related_name='nominees')
    name        = models.CharField(max_length=150)
    slug        = models.SlugField()
    short_code = models.CharField(max_length=10, unique=True, blank=True)
    photo       = models.ImageField(upload_to='nominees/', blank=True, null=True)
    bio         = models.TextField(blank=True)
    is_active   = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering        = ['-is_featured', 'name']
        unique_together = ('category', 'slug')

    def __str__(self):
        return f"{self.name} ({self.category.name})"

    def save(self, *args, **kwargs):
        # Auto-generate short code on first save
        if not self.short_code:
            self.short_code = generate_short_code()
        super().save(*args, **kwargs)

    @property
    def total_votes(self):
        from apps.voting.models import Vote
        return Vote.objects.filter(nominee=self).aggregate(
            total=models.Sum('quantity')
        )['total'] or 0

    @property
    def vote_percentage(self):
        category_total = self.category.total_votes
        if category_total == 0:
            return 0
        return round((self.total_votes / category_total) * 100, 1)