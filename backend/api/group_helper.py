import mariadb
import datetime
from . import config
from . import sql_helper
from . import api_logger as logger
cfg = config.config

def join_group(username, join_code):
    mdb = mariadb.connect(**(cfg['sql']))
    cursor = mdb.cursor(dictionary=True)
    data = {
        "username": username, 
        "group_jc": join_code,
        "joined": str(datetime.datetime.utcnow())
    }
    sql = sql_helper.insert_into("user_groups", data)
    cursor.execute(sql)
    mdb.commit()
    mdb.close()

def leave_group_or_kick(username, join_code):
    mdb = mariadb.connect(**(cfg['sql']))
    cursor = mdb.cursor(dictionary=True)
    sql = "DELETE FROM `user_groups` WHERE `user_groups`.`username` = '"+username+"' AND `user_groups`.`group_jc` = '"+join_code+"'"
    cursor.execute(sql)
    mdb.commit()
    mdb.close()

def delete_group(join_code):
    mdb = mariadb.connect(**(cfg['sql']))
    cursor = mdb.cursor(dictionary=True)
    sql = "DELETE FROM `user_groups` WHERE `user_groups`.`group_jc` = '"+join_code+"'"
    cursor.execute(sql)
    mdb.commit()
    sql = "DELETE FROM `groups` WHERE `join_code` = '"+join_code+"'"
    cursor.execute(sql)
    mdb.commit()
    mdb.close()

def is_in_group(username, join_code):
    mdb = mariadb.connect(**(cfg['sql']))
    cursor = mdb.cursor(dictionary=True)
    sql = "SELECT joined from user_groups WHERE group_jc = '"+join_code+"' AND username = '"+username+"';"
    cursor.execute(sql)
    result = list(cursor)
    mdb.close()
    if result:
        return True
    return False


def get_group(join_code):
    mdb = mariadb.connect(**(cfg['sql']))
    cursor = mdb.cursor(dictionary=True)
    cursor.execute("SELECT * from groups WHERE join_code = '" + join_code + "';")
    result = list(cursor)
    if not result:
        mdb.close()
        return False
    cursor.execute("SELECT user_groups.username, user_groups.joined, users.profile_image, users.scrobbles FROM user_groups LEFT JOIN users ON users.username = user_groups.username WHERE user_groups.group_jc = '{}' ORDER BY user_groups.joined ASC".format(join_code))
    users = list(cursor)
    result[0]['users'] = users
    mdb.close()
    return result[0]

def edit_group(join_code, data):
    mdb = mariadb.connect(**(cfg['sql']))
    cursor = mdb.cursor(dictionary=True)
    sql = "UPDATE `groups` SET `name` = '{}', `description` = '{}', `owner` = '{}' WHERE `join_code` = '{}'".format(sql_helper.esc_db(data['name']), sql_helper.esc_db(data['description']), data['owner'], join_code)
    cursor.execute(sql)
    mdb.commit()
    mdb.close()