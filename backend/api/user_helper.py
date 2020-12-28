import mariadb
import datetime
import requests
import hashlib
from . import config
from . import sql_helper
from . import api_logger as logger

cfg = config.config

def get_user(username):
    mdb = mariadb.connect(**(cfg['sql']))
    cursor = mdb.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE username = '" + str(username) + "';")
    result = list(cursor)
    mdb.close()
    if result:
        return result[0]
    else:
        return False

def create_user(username):
    mdb = mariadb.connect(**(cfg['sql']))
    cursor = mdb.cursor(dictionary=True)
    data = {
        "method": "user.getinfo", 
        "user": username, 
        "api_key": cfg['api']['key'],
        "format": "json"
    }
    user_info = requests.post("http://ws.audioscrobbler.com/2.0", data=data).json()
    data = {}
    data['username'] = username
    data['display_name'] = user_info['user']['realname']
    data['registered'] = user_info['user']['registered']['unixtime']
    data['profile_image'] = user_info['user']['image'][3]['#text']
    logger.log(data['profile_image'])
    sql = sql_helper.insert_into_where_not_exists("users", data, "username")
    cursor.execute(sql)
    mdb.commit()