from optparse import make_option
from django.core.management.base import BaseCommand
from scheduler.scheduler import run_scheduler


class Command(BaseCommand):
    help = 'Run the parsing jobs scheduler'
    option_list = BaseCommand.option_list + (
        make_option('--continue',
            action='store_true',
            dest='continue',
            default=False,
            help='Don\'t wipe the task list at startup'),
        )

    def handle(self, *args, **options):
        run_scheduler(options["continue"])
