import csv

from django.core.management.base import BaseCommand
from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'Import data from csv-file.'

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str)

    def handle(self, *args, **options):
        answer = input(
            'Do you want to clean up the Ingredients database? [Y/N]: '
        ).lower()
        if answer == 'y':
            Ingredient.objects.all().delete()
        elif answer == 'n':
            self.stdout.write('The operation is skipped.')
        else:
            return 'Invalid value.'
        with open(
            options['file_path'], 'r', encoding='utf-8'
        ) as csv_file:
            reader = csv.DictReader(csv_file)
            Ingredient.objects.bulk_create(
                Ingredient(**data) for data in reader
            )
            self.stdout.write(
                'Выполнен импорт данных для таблицы Ingredient.'
            )
        return 'Выполнен импорт данных для таблицы Ingredient.'
