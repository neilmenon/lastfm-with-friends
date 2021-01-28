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
    if not result:
        return False
    user_data = result[0]
    cursor.execute("SELECT group_jc FROM user_groups WHERE username = '" + str(username) + "';")
    group_jcs = [k['group_jc'] for k in list(cursor)]
    user_data['groups'] = []
    for join_code in group_jcs:
        sql = "SELECT * from groups WHERE join_code = '{}';".format(join_code)
        cursor.execute(sql)
        result = list(cursor)
        sql = "SELECT username,joined from user_groups WHERE group_jc = '{}';".format(join_code)
        cursor.execute(sql)
        result1 = list(cursor)
        result[0]['members'] = result1
        user_data['groups'].append(result[0])
    mdb.close()
    return user_data

def get_users():
    mdb = mariadb.connect(**(cfg['sql']))
    cursor = mdb.cursor(dictionary=True)
    cursor.execute("SELECT username FROM users;")
    result = list(cursor)
    mdb.close()
    if result:
        return result
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
    sql = sql_helper.insert_into_where_not_exists("users", data, "username")
    cursor.execute(sql)
    mdb.commit()

def change_updated_date(username, clear_date=False, start_time=None):
    mdb = mariadb.connect(**(cfg['sql']))
    cursor = mdb.cursor(dictionary=True)
    if clear_date:
        sql = "UPDATE `users` SET `last_update` = NULL WHERE `users`.`username` = '"+ username + "';"
    elif start_time:
        sql = "UPDATE `users` SET `last_update` = '"+str(start_time)+"' WHERE `users`.`username` = '"+ username + "';"
    else:
        sql = "UPDATE `users` SET `last_update` = '"+str(datetime.datetime.utcnow())+"' WHERE `users`.`username` = '"+ username + "';"
    cursor.execute(sql)
    mdb.commit()
    mdb.close()

def get_updated_date(username):
    mdb = mariadb.connect(**(cfg['sql']))
    cursor = mdb.cursor(dictionary=True)
    cursor.execute("SELECT last_update FROM users WHERE `users`.`username` = '"+ username + "';")
    result = list(cursor)
    mdb.close()
    return result[0]['last_update']