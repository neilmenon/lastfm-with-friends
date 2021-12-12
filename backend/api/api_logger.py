import datetime
from flask import current_app

def info(message, app=None):
    if app:
        app.logger.info(message)
    else:
        current_app.logger.info(message)

def debug(message, app=None):
    if app:
        app.logger.debug(message)
    else:
        current_app.logger.debug(message)

def warn(message, app=None):
    if app:
        app.logger.warn(message)
    else:
        current_app.logger.warn(message)

def error(message, app=None):
    if app:
        app.logger.error(message)
    else:
        current_app.logger.error(message)
