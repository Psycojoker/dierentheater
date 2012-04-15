#!/usr/bin/env python
import logging
logger = logging.getLogger('')

import pika

def send(message):
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    channel.queue_declare(queue='dierentheater')

    channel.basic_publish(exchange='', routing_key='dierentheater', body=message)
    logging.info(" [x] Sent '%s'" % message)

    connection.close()
