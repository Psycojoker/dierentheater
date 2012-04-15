#!/usr/bin/env python
import sys
import pika
from operations import operations

def run_downloader():
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    channel.queue_declare(queue='dierentheater')

    def callback(ch, method, properties, body):
        if body in operations.keys():
            print " [x] Received %r, processing..." % (body,)
            operations[body]()
            print " [x] End, waiting for next event"
        else:
            print >>sys.stderr, " /!\ unknow signal: %s" % body

    channel.basic_consume(callback, queue='dierentheater', no_ack=True)

    print ' [*] Waiting for events. To exit press CTRL+C'

    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    run_downloader()
