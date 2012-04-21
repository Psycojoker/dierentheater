#!/usr/bin/env python
import sys
import traceback
import logging
logger = logging.getLogger('')

from time import sleep

from django.conf import settings

from history.utils import irc

from operations import operations
from models import Task

def run_scheduler():
    settings.CACHE_SCRAPING = False

    # clean task list before starting
    Task.objects.all().delete()

    logging.info('[*] Waiting for events. To exit press CTRL+C')

    try:
        loop()
    except KeyboardInterrupt:
        pass


def loop():
    while True:
        for task in Task.objects.all():
            if task.function in operations.keys():
                logger.info("[x] Received %r, processing..." % task)
                try:
                    operations[task.function](*task.args)
                    logger.info("[x] End, waiting for next event")
                except Exception, e:
                    traceback.print_exc(file=sys.stdout)
                    logger.error("/!\ %s didn't succed! Error: %s" % (task, e))
                    irc("\x034%s didn't succed! Error: %s\x03" % (task, e))
                    irc("Bram: entering ipdb shell")
                    e, m, tb = sys.exc_info()
                    from ipdb import post_mortem; post_mortem(tb)

            else:
                logger.warn("/!\ unknow signal: %s" % task)
            task.delete()
        sleep(3)


if __name__ == "__main__":
    run_scheduler()
