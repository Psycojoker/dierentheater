#!/usr/bin/env python
import logging
logger = logging.getLogger('')

from models import Task

def send(function, args=None):
    if args is None:
        args = []
    Task.objects.create(function=function, args=args)
    logging.info("[x] Sent %s(%s)" % (function, ", ".join(map(lambda x: "%s" % x, args))))
