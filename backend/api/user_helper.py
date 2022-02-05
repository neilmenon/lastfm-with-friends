import datetime
import json
import time
import requests
import hashlib
from . import config
from . import sql_helper
from . import api_logger as logger
from . import group_session_helper

cfg = config.config

def get_user(username, extended=True, get_session=False, get_stats=False):
    result = sql_helper.execute_db("SELECT * FROM users WHERE username = '" + str(username) + "';")
    if not result:
        return False
    user_data = result[0]
    if not extended and not get_session:
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
    if get_stats:
        user_data['stats'] = get_personal_stats(username)
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
            data['joined_date'] = datetime.datetime.utcnow() # date user joins the app.
            sql = sql_helper.insert_into_where_not_exists("users", data, "username")
        sql_helper.execute_db(sql, commit=True)
        if update:
            return data
    except Exception as e:
        logger.error("Error while creating or updating {}: {}".format(username, e))

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

def wipe_scrobbles(username, user_id):
    # we have to do this in a chunked approach otherwise it will time out
    # first, get total count of scrobbles to delete
    scrobbles = sql_helper.execute_db("SELECT COUNT(*) as scrobbles FROM track_scrobbles WHERE user_id = {}".format(user_id))[0]['scrobbles']
    rows_to_delete = scrobbles
    while rows_to_delete > 0:
        logger.info("Wiping scrobbles for {} in chunks ({} left)".format(username, rows_to_delete))
        sql_helper.execute_db("DELETE FROM track_scrobbles WHERE user_id = {} LIMIT 5000".format(user_id), commit=True)
        time.sleep(0.25)
        rows_to_delete = rows_to_delete - 5000
    scrobbles = sql_helper.execute_db("SELECT COUNT(*) as scrobbles FROM track_scrobbles WHERE user_id = {}".format(user_id))[0]['scrobbles']
    logger.debug("New scrobble count from DB for {}: {} (expected: 0)".format(username, scrobbles))

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

def fire_and_forget_user_update(username, session_key, user_id, url):
    data = {
        "username": username,
        "session_key": session_key,
        "full_scrape": True,
        "user_id": user_id
    }
    requests.post(url, json=data)

def get_personal_stats(username):
    stats = sql_helper.execute_db("SELECT * FROM personal_stats WHERE username = '{}'".format(username))
    if not len(stats):
        return None
    else:
        stats: dict = stats[0]
        for k in stats.keys():
            stats[k] = json.loads(stats[k]) if stats[k] and k in ["cant_get_enough", "scrobble_compare", "top_genre", "top_rising"] else stats[k]
        return stats
