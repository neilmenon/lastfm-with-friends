import mariadb
import datetime
from . import config
from . import sql_helper
from . import api_logger as logger
cfg = config.config

def link_user_to_group(username, join_code):
    mdb = mariadb.connect(**(cfg['sql']))
    cursor = mdb.cursor(dictionary=True)
    cursor.execute("SELECT id from groups WHERE join_code = '" + join_code + "';")
    result = list(cursor)
    if not result:
        raise Exception("Error while trying to create entry in user_groups table: No group with join code " + join_code + " found.")
    data = {
        "username": username, 
        "group_id": result[0]['id'],
        "joined": str(datetime.datetime.utcnow())
    }
    sql = sql_helper.replace_into("user_groups", data)
    cursor.execute(sql)
    mdb.commit()
    mdb.close()
