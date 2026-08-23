import re
from django.db import models
from django.utils.crypto import get_random_string
from cloudinary.models import CloudinaryField

STOPWORDS = {'AND', 'OF', 'THE', 'FOR', 'IN', 'A', 'AN', 'TO', 'AT', 'ON'}


def generate_short_code(event):
    """
    Generate a code like PDAN01 — initials from the event title
    (skipping small words like AND/OF/THE) followed by a sequential number.
    """
    words = re.findall(r"[A-Za-z]+", event.title.replace("'", ""))
    initials = ''.join(w[0].upper() for w in words if w.upper() not in STOPWORDS)
    if not initials:
        initials = 'EV'
    initials = initials[:6]

    n = 1
    while True:
        code = f"{initials}{n:02d}"
        if not Nominee.objects.filter(short_code=code).exists():
            return code
        n += 1

class Nominee(models.Model):
    category    = models.ForeignKey('categories.Category', on_delete=models.CASCADE, related_name='nominees')
    name        = models.CharField(max_length=150)
    slug        = models.SlugField()
    short_code  = models.CharField(max_length=10, unique=True, blank=True)
    photo       = CloudinaryField('image', blank=True, null=True)
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
        if not self.short_code:
            self.short_code = generate_short_code(self.category.event)
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