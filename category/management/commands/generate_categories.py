import os
import random

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction

from ...models import Category


class Command(BaseCommand):
    help = 'Generate arbitrary number of categories'

    def add_arguments(self, parser):
        parser.add_argument('num_categories', type=int,
                            help='Number of categories to create')

    def handle(self, *args, **options):
        n = options['num_categories']
        names = self.generate_names(n)

        test_image_data = self.get_test_image_data()
        if not test_image_data:
            return

        self.stdout.write(f"Generating {n} categories")

        with transaction.atomic():
            categories = self.generate_categories(names, test_image_data)
            Category.objects.bulk_create(categories)
            categories = list(Category.objects.order_by('id').all())
            self.possibly_assign_parents(categories)

            self.stdout.write("Parents assigned")

        self.stdout.write(
            self.style.SUCCESS('Done generating categories'))

    @staticmethod
    def generate_names(n):
        def number_to_name(num):
            name = ''
            while num >= 0:
                name = chr(num % 26 + ord('A')) + name
                num = num // 26 - 1
            return name

        return [number_to_name(i) for i in range(n)]

    @staticmethod
    def generate_categories(names, test_image_data):
        categories = []
        for name in names:
            cat = Category(
                name=name,
                description=f'Description of {name}',
            )
            from django.core.files.base import ContentFile
            cat.image.save(f'{name}.png', ContentFile(test_image_data),
                           save=False)
            categories.append(cat)
        return categories

    @staticmethod
    def possibly_assign_parents(categories):
        for cat in categories:
            possible_parents = [c for c in categories if c.id < cat.id]
            if possible_parents:
                parent = random.choice(possible_parents + [
                    None] * len(possible_parents))
                if parent:
                    cat.parent = parent
                    cat.save()

    def get_test_image_data(self):
        test_image_path = os.path.join(settings.BASE_DIR, 'CategoryTree',
                                       'test_files', 'test_image.png')
        if not os.path.exists(test_image_path):
            self.stderr.write(f"Test image not found at {test_image_path}")
            return

        with open(test_image_path, 'rb') as img_file:
            return img_file.read()
