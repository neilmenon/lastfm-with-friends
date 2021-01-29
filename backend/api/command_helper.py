import mariadb
import datetime
from . import config
from . import sql_helper
from . import api_logger as logger

cfg = config.config

def wk_artist(query, users):
    mdb = mariadb.connect(**(cfg['sql']))
    cursor = mdb.cursor(dictionary=True)

    # find artist in the database
    sql = "SELECT * from artists WHERE {} LIKE '%{}%'".format(sql_helper.sanitize_db_field("name"), sql_helper.esc_db(query))
    cursor.execute(sql)
    result = list(cursor)
    if not result:
        sql = "SELECT * from artist_redirects WHERE {} LIKE '%{}%'".format(sql_helper.sanitize_db_field("artist_name"), sql_helper.esc_db(query))
        cursor.execute(sql)
        result = list(cursor)
        if not result:
            return False
        redirected_name = result[0]['redirected_name']
        sql = "SELECT * from artists WHERE name = '{}'".format(sql_helper.esc_db(redirected_name))
        cursor.execute(sql)
        result = list(cursor)
        artist = result[0]
    artist = result[0]

    # find users who have scrobbled this artist
    users_list = ", ".join('"' + u + '"' for u in users)
    sql = 'SELECT username,scrobbles FROM artist_scrobbles WHERE artist_id = {} AND username IN ({}) ORDER BY scrobbles DESC;'.format(artist['id'], users_list)
    cursor.execute(sql)
    result = list(cursor)
    if not result:
        return False

    return {'artist': artist, 'users': result}
