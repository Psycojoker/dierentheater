from django.conf import settings


def irc(message):
    open(settings.PROJECT_PATH + "/log/irc", "a").write(message.strip() + "\n")
