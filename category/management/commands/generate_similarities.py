import random

from django.core.management.base import BaseCommand
from django.db import transaction

from ...models import Category, Similarity


class Command(BaseCommand):
    help = 'Generate arbitrary number of similarities'

    def add_arguments(self, parser):
        parser.add_argument('num_similarities', type=int,
                            help='Number of similarities to create')

    def handle(self, *args, **options):
        similarity_count = options['num_similarities']
        with transaction.atomic():
            self.stdout.write(
                f"Creating {similarity_count} similarity relationships")
            categories = list(Category.objects.order_by('id').all())
            self.create_similarities(categories, similarity_count)

        self.stdout.write(
            self.style.SUCCESS('Done generating similarities'))

    def create_similarities(self, categories, similarity_count):
        existing_pairs = set()
        for sim in Similarity.objects.values_list('category_a_id',
                                                  'category_b_id'):
            existing_pairs.add(tuple(sorted(sim)))

        created = 0
        attempts = 0
        # This can loop infinitely, so prevent it.
        max_attempts = similarity_count * 10
        while created < similarity_count and attempts < max_attempts:
            a, b = random.sample(categories, 2)
            pair = tuple(sorted([a.id, b.id]))
            if pair not in existing_pairs:
                Similarity.objects.create(category_a_id=pair[0],
                                          category_b_id=pair[1])
                existing_pairs.add(pair)
                created += 1
            attempts += 1

        self.stdout.write(f"Created {created} similarities")
