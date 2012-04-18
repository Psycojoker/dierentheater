from django.core.management.base import BaseCommand
from scheduler.scheduler import run_scheduler

class Command(BaseCommand):
    help = 'Run the parsing jobs scheduler'

    def handle(self, *args, **options):
        run_scheduler()
