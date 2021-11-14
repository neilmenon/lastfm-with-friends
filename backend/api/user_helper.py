import datetime
import requests
import hashlib
from . import config
from . import sql_helper
from . import api_logger as logger
from . import group_session_helper

cfg = config.config

def get_user(username, extended=True, get_session=False):
    result = sql_helper.execute_db("SELECT * FROM users WHERE username = '" + str(username) + "';")
    if not result:
        return False
    user_data = result[0]
    if not extended or not get_session:
        return user_data
    if extended:
        result = sql_helper.execute_db("SELECT group_jc FROM user_groups WHERE username = '" + str(username) + "' ORDER BY joined ASC;")
        group_jcs = [k['group_jc'] for k in result]
        user_data['groups'] = []
        for join_code in group_jcs:
            sql = "SELECT * from groups WHERE join_code = '{}';".format(join_code)
            result = sql_helper.execute_db(sql)
            sql = "SELECT users.user_id as id, users.username FROM user_groups LEFT JOIN users ON users.username = user_groups.username WHERE user_groups.group_jc = '{}' ORDER BY user_groups.joined ASC".format(join_code)
            result1 = sql_helper.execute_db(sql)
            result[0]['members'] = result1
            user_data['groups'].append(result[0])
    if get_session:
        current_session = group_session_helper.get_current_session(username=username, with_members=True)
        user_data['group_session'] = None if not current_session else current_session
    return user_data

def get_users():
    result = sql_helper.execute_db("SELECT username FROM users;")
    if result:
        return result
    else:
        return False

def get_user_account(username, update=False):
    try:
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
        data['profile_image'] = user_info['user']['image'][3]['#text'] if user_info['user']['image'][3]['#text'] else "https://lastfm.freetls.fastly.net/i/u/avatar170s/818148bf682d429dc215c1705eb27b98.webp"
        data['scrobbles'] = user_info['user']['playcount']
        data['progress'] = 0
        if update:
            sql = "UPDATE `users` SET `display_name` = '{}', `profile_image` = '{}', `scrobbles` = {}, registered = '{}' WHERE `username` = '{}'".format(data['display_name'], data['profile_image'], data['scrobbles'], data['registered'], username)
        else:
            sql = sql_helper.insert_into_where_not_exists("users", data, "username")
        sql_helper.execute_db(sql, commit=True)
        if update:
            return data
    except Exception as e:
        logger.log("Error while creating or updating {}: {}".format(username, e))

def change_updated_date(username, clear_date=False, start_time=None):
    if clear_date:
        sql = "UPDATE `users` SET `last_update` = NULL WHERE `users`.`username` = '"+ username + "';"
    elif start_time:
        sql = "UPDATE `users` SET `last_update` = '"+str(start_time)+"' WHERE `users`.`username` = '"+ username + "';"
    else:
        sql = "UPDATE `users` SET `last_update` = '"+str(datetime.datetime.utcnow())+"' WHERE `users`.`username` = '"+ username + "';"
    sql_helper.execute_db(sql, commit=True)

def change_update_progress(username, progress, clear_progress=False):
    if clear_progress:
        sql = "UPDATE `users` SET `progress` = 0 WHERE `users`.`username` = '"+ username + "';"
    else:
        sql = "UPDATE `users` SET `progress` = "+str(progress)+" WHERE `users`.`username` = '"+ username + "';"
    sql_helper.execute_db(sql, commit=True)

def get_updated_date(username):
    result = sql_helper.execute_db("SELECT last_update FROM users WHERE `users`.`username` = '"+ username + "';")
    return result[0]['last_update']

def wipe_scrobbles(user_id):
    sql = "DELETE FROM track_scrobbles WHERE user_id = {};".format(user_id)
    sql_helper.execute_db(sql, commit=True)

def delete_user(user_id, username):
    result = sql_helper.execute_db("SELECT * FROM user_groups WHERE username = '{}';".format(username))
    if result: # user needs to have manually left all groups first
        return False
    sql_helper.execute_db("DELETE FROM track_scrobbles WHERE user_id = {};".format(user_id), commit=True)
    sql_helper.execute_db("DELETE FROM now_playing WHERE username = '{}';".format(username), commit=True)
    sql_helper.execute_db("DELETE FROM sessions WHERE username = '{}';".format(user_id), commit=True)
    sql_helper.execute_db("DELETE FROM users WHERE user_id = {};".format(user_id), commit=True)
    return True

def get_settings(username):
    result = sql_helper.execute_db("SELECT settings FROM users WHERE username = '{}'".format(username))
    if result:
        return result[0]['settings']
    return False

def set_settings(username, settings):
    sql_helper.execute_db("UPDATE users SET settings = '{}' WHERE username = '{}'".format(settings, username), commit=True)

def get_demo_user():
    sql = "SELECT username, session_key FROM sessions where username = '{}'".format(cfg['demo_user'])
    result = sql_helper.execute_db(sql)
    if result:
        return result[0]
    return