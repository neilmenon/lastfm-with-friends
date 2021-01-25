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

def leave_group(username, join_code):
    mdb = mariadb.connect(**(cfg['sql']))
    cursor = mdb.cursor(dictionary=True)
    sql = "DELETE FROM `user_groups` WHERE `user_groups`.`username` = '"+username+"' AND `user_groups`.`group_jc` = '"+join_code+"'"
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
        return False
    mdb.close()
    return result[0]
