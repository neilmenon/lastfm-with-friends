import mariadb
import datetime
from . import config
from . import sql_helper
from . import api_logger as logger
cfg = config.config

def join_group(username, join_code):
    data = {
        "username": username, 
        "group_jc": join_code,
        "joined": str(datetime.datetime.utcnow())
    }
    sql = sql_helper.insert_into("user_groups", data)
    sql_helper.execute_db(sql, commit=True)

def leave_group_or_kick(username, join_code):
    sql = "DELETE FROM `user_groups` WHERE `user_groups`.`username` = '"+username+"' AND `user_groups`.`group_jc` = '"+join_code+"'"
    sql_helper.execute_db(sql, commit=True)

def delete_group(join_code):
    sql = "DELETE FROM `user_groups` WHERE `user_groups`.`group_jc` = '"+join_code+"'"
    sql_helper.execute_db(sql, commit=True)
    sql = "DELETE FROM `groups` WHERE `join_code` = '"+join_code+"'"
    sql_helper.execute_db(sql, commit=True)

def is_in_group(username, join_code):
    sql = "SELECT joined from user_groups WHERE group_jc = '"+join_code+"' AND username = '"+username+"';"
    result = sql_helper.execute_db(sql)
    if result:
        return True
    return False


def get_group(join_code, short=False):
    result = sql_helper.execute_db("SELECT * from groups WHERE join_code = '" + join_code + "';")
    if not result:
        return False
    if short:
        sql = "SELECT users.user_id,users.username FROM user_groups LEFT JOIN users ON users.username = user_groups.username WHERE user_groups.group_jc = '{}' ORDER BY user_groups.joined ASC".format(join_code)
    else:
        sql = "SELECT user_groups.username, user_groups.joined, users.profile_image, users.scrobbles, users.registered, users.user_id FROM user_groups LEFT JOIN users ON users.username = user_groups.username WHERE user_groups.group_jc = '{}' ORDER BY user_groups.joined ASC".format(join_code)
    users = sql_helper.execute_db(sql)
    result[0]['users'] = users
    return result[0]

def edit_group(join_code, data):
    sql = "UPDATE `groups` SET `name` = '{}', `description` = '{}', `owner` = '{}' WHERE `join_code` = '{}'".format(sql_helper.esc_db(data['name']), sql_helper.esc_db(data['description']), data['owner'], join_code)
    sql_helper.execute_db(sql, commit=True)