from django.core.management.base import BaseCommand
from core.populate_categories import create_categories


class Command(BaseCommand):
    help = 'Populate the database with product categories'

    def handle(self, *args, **options):
        self.stdout.write('Creating categories...')
        create_categories()
        self.stdout.write(self.style.SUCCESS('Successfully populated categories'))
