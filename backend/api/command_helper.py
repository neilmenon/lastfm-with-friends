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
    sanitized_query = sql_helper.sanitize_query(query)
    sql = "SELECT * from artists WHERE {} LIKE '%{}%'".format(sql_helper.sanitize_db_field("name"), sanitized_query)
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
    sql = 'SELECT artist_scrobbles.username, artist_scrobbles.scrobbles, users.scrobbles as total, CAST(ROUND((artist_scrobbles.scrobbles/users.scrobbles)*100, 2) AS FLOAT) as percent FROM artist_scrobbles LEFT JOIN users ON users.username = artist_scrobbles.username WHERE artist_scrobbles.username IN ({}) AND artist_scrobbles.artist_id = {} ORDER BY percent DESC'.format(users_list, artist['id'])
    cursor.execute(sql)
    result = list(cursor)
    if not result:
        return False
    total_scrobbles = sum([u['scrobbles'] for u in result])
    return {'artist': artist, 'users': result, 'total_scrobbles': total_scrobbles, 'total_users': len(users)}
