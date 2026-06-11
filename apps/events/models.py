from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal
from cloudinary.models import CloudinaryField


class Event(models.Model):
    STATUS_CHOICES = [
        ('draft',  'Draft'),
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('ended',  'Ended'),
    ]
    title           = models.CharField(max_length=200)
    slug            = models.SlugField(unique=True)
    description     = models.TextField(blank=True)
    banner          = CloudinaryField('image', blank=True, null=True)
    status          = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')
    start_date      = models.DateTimeField()
    end_date        = models.DateTimeField()
    show_results    = models.BooleanField(default=True)
    commission_rate = models.DecimalField(
                        max_digits=5,
                        decimal_places=2,
                        default=Decimal('11.00'),
                        help_text='Commission percentage deducted from revenue (e.g. 11.00 = 11%)'
                      )
    organizer       = models.ForeignKey(
                        User, on_delete=models.SET_NULL,
                        null=True, blank=True,
                        related_name='events',
                        help_text='The organizer account assigned to this event'
                      )
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    @property
    def is_active(self):
        now = timezone.now()
        return self.status == 'active' and self.start_date <= now <= self.end_date

    @property
    def total_votes(self):
        return sum(cat.total_votes for cat in self.categories.all())

    @property
    def total_revenue(self):
        return Decimal(self.total_votes)

    @property
    def commission_amount(self):
        return round(self.total_revenue * (self.commission_rate / Decimal('100')), 2)

    @property
    def net_revenue(self):
        return round(self.total_revenue - self.commission_amount, 2)


class HeroVideo(models.Model):
    title         = models.CharField(
                      max_length=100,
                      help_text='Label for this video e.g. "Awards Night 2024"'
                    )
    video         = CloudinaryField(
                      'video',
                      resource_type='video',
                      help_text='Upload MP4 video file'
                    )
    hero_heading  = models.CharField(
                      max_length=200,
                      blank=True,
                      help_text='Main heading shown on homepage hero when this video plays'
                    )
    hero_subtext  = models.TextField(
                      blank=True,
                      help_text='Supporting text shown below the heading when this video plays.'
                    )
    order         = models.PositiveIntegerField(
                      default=0,
                      help_text='Display order — lower numbers show first'
                    )
    is_active     = models.BooleanField(
                      default=True,
                      help_text='Uncheck to hide this video from the homepage'
                    )
    created_at    = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'created_at']

    def __str__(self):
        return self.title


class SiteSettings(models.Model):
    hero_title    = models.CharField(
                      max_length=200,
                      default='Vote for Your Favourite Personality',
                      help_text='Main heading on the homepage hero'
                    )
    hero_subtitle = models.TextField(
                      default='Real-time results. Instant MoMo payments. Transparent voting for schools, brands & communities across Ghana.',
                      help_text='Subtext shown below the hero heading'
                    )
    hero_badge    = models.CharField(
                      max_length=100,
                      default='NobleVote',
                      help_text='Small badge text above the hero heading'
                    )

    class Meta:
        verbose_name        = 'Site Settings'
        verbose_name_plural = 'Site Settings'

    def __str__(self):
        return 'Site Settings'

    @classmethod
    def get(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj