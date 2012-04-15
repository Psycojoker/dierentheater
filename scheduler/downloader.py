#!/usr/bin/env python
import logging
logger = logging.getLogger('')

import pika

from django.conf import settings

from operations import operations

def run_downloader():
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    channel.queue_declare(queue='dierentheater')

    def callback(ch, method, properties, body):
        if body in operations.keys():
            logger.info(" [x] Received %r, processing..." % (body,))
            operations[body]()
            logger.info(" [x] End, waiting for next event")
        else:
            logger.warn(" /!\ unknow signal: %s" % body)

    channel.basic_consume(callback, queue='dierentheater', no_ack=True)

    settings.CACHE_SCRAPING = False

    logging.info(' [*] Waiting for events. To exit press CTRL+C')

    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    run_downloader()
