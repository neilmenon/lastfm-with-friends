import datetime
from flask import current_app

def log(message):
    current_app.logger.debug(message)
