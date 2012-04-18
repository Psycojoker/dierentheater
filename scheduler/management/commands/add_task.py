import sys
from django.core.management.base import BaseCommand, CommandError
from scheduler import send
from scheduler.operations import operations

def run():
    if len(sys.argv) == 3:
        print >>sys.stderr, "You need to give me an operation as first parameters"
        print >>sys.stderr
        print >>sys.stderr, "Available operations:"
        for operation in operations.keys():
            print >>sys.stderr, "    *", operation
        print >>sys.stderr
        sys.exit(1)
    send(sys.argv[3])

class Command(BaseCommand):
    args = '<message message ...>'
    help = 'Add new task to the scheduler'

    def handle(self, *args, **options):
        if not args:
            pass
            sys.stdout.write("You need to give me an operation as first parameters\n\n")
            sys.stdout.write("Available operations:\n")
            for operation in operations.keys():
                sys.stdout.write("    * %s\n" % operation)
            sys.stdout.write("\n")

        for full_message in args:
            message = full_message.split(";")[0]
            message_args = full_message.split(";")[1:]
            if message in operations.keys():
                send(message, message_args)
            else:
                raise CommandError("This message doesn\'t exist: %s" % message)
