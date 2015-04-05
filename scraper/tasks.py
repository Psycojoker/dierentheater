from urllib2 import urlopen

from dierentheater.celery import app


@app.task
def async_http(url):
    return urlopen(url).read()
