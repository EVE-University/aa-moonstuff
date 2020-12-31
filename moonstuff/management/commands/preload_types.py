from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Preloads type data required for the Moonstuff plugin.'

    def handle(self, *args, **options):
        call_command(
            'eveuniverse_load_types',
            'moonstuff',
            '--category_id',
            '25',
            '--category_id',
            '65',
            '--group_id',
            '18',
            '--group_id',
            '423',
            '--group_id',
            '427',
        )
