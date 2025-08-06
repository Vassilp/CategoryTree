import os
import shutil

from django.conf import settings
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = 'Flush the database and create a superuser with preset credentials'

    def add_arguments(self, parser):
        parser.add_argument(
            '-c', '--categories', type=int, default=0,
            help='If set, generate this many categories after resetting'
        )
        parser.add_argument(
            '-s', '--similarities', type=int, default=0,
            help='If set, generate this many similarities after resetting'
        )

    def handle(self, *args, **options):
        categories = options['categories']
        similarities = options['similarities']
        max_similarities = int((categories * (categories - 1)) / 2)
        if similarities > max_similarities:
            self.stdout.write(self.style.WARNING(
                f'More than the maximum amount of similarities. '
                f'will create the maximum: {max_similarities}'))
            similarities = max_similarities

        self.stdout.write(self.style.WARNING('Flushing the database...'))
        call_command('flush', interactive=False)

        media_root = settings.MEDIA_ROOT
        if os.path.exists(media_root):
            self.stdout.write(self.style.WARNING(
                f"Deleting media folder at {media_root}..."))
            for filename in os.listdir(media_root):
                file_path = os.path.join(media_root, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    self.stderr.write(
                        f'Failed to delete {file_path}. Reason: {e}')
            self.stdout.write(self.style.SUCCESS("Media folder cleared."))
        else:
            self.stdout.write(self.style.WARNING("MEDIA_ROOT does not exist."))

        User = get_user_model()

        if not User.objects.filter(username='superuser').exists():
            self.stdout.write(self.style.WARNING('Creating superuser...'))
            User.objects.create_superuser(
                username='superuser',
                email='email@address.com',
                password='password'
            )
            self.stdout.write(
                self.style.SUCCESS('Superuser created: superuser'))
        else:
            self.stdout.write(self.style.WARNING('Superuser already exists.'))
        if categories:
            call_command('generate_categories', categories)
        if similarities:
            call_command('generate_similarities', similarities)
