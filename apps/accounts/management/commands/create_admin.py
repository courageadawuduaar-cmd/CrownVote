from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
import os


class Command(BaseCommand):
    help = 'Create superuser from environment variables'

    def handle(self, *args, **kwargs):
        username = os.environ.get('ADMIN_USERNAME', 'admin')
        email    = os.environ.get('ADMIN_EMAIL', 'admin@crownvote.gh')
        password = os.environ.get('ADMIN_PASSWORD', '')

        if not password:
            self.stdout.write('ADMIN_PASSWORD not set — skipping')
            return

        if User.objects.filter(username=username).exists():
            self.stdout.write(f'Admin "{username}" already exists — skipping')
            return

        User.objects.create_superuser(
            username=username,
            email=email,
            password=password
        )
        self.stdout.write(f'✅ Superuser "{username}" created successfully')