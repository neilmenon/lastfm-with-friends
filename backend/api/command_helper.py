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
    users_list = ", ".join(str(u) for u in users)
    sql = 'SELECT users.username, COUNT(*) as scrobbles, users.scrobbles as total, CAST(ROUND((COUNT(*)/users.scrobbles)*100, 2) AS FLOAT) as percent FROM track_scrobbles LEFT JOIN users ON users.user_id = track_scrobbles.user_id WHERE track_scrobbles.user_id IN ({}) AND track_scrobbles.artist_id = {} GROUP BY users.username ORDER BY percent DESC'.format(users_list, artist['id'])
    cursor.execute(sql)
    result = list(cursor)
    total_scrobbles = sum([u['scrobbles'] for u in result])
    return {'artist': artist, 'users': result, 'total_scrobbles': total_scrobbles, 'total_users': len(users)}

def wk_album(query, users):
    mdb = mariadb.connect(**(cfg['sql']))
    cursor = mdb.cursor(dictionary=True)

    query = sql_helper.sanitize_query(query)
    artist_query = query.strip().split(" - ")[0].strip()
    album_query = query.strip().split(" - ")[1].strip()

    # find artist in the database
    sql = "SELECT * from artists WHERE {} LIKE '%{}%'".format(sql_helper.sanitize_db_field("name"), artist_query)
    cursor.execute(sql)
    result = list(cursor)
    if not result:
        sql = "SELECT * from artist_redirects WHERE {} LIKE '%{}%'".format(sql_helper.sanitize_db_field("artist_name"), sql_helper.esc_db(artist_query))
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

    # find album in the database
    sql = "SELECT * from albums WHERE artist_name = '{}' AND {} LIKE '%{}%'".format(artist['name'], sql_helper.sanitize_db_field("name"), album_query)
    cursor.execute(sql)
    result = list(cursor)
    if not result:
        return False
    album = result[0]

    # find users who have scrobbled this album
    users_list = ", ".join(str(u) for u in users)
    sql = 'SELECT users.username, COUNT(*) as scrobbles, users.scrobbles as total, CAST(ROUND((COUNT(*)/users.scrobbles)*100, 2) AS FLOAT) as percent FROM track_scrobbles LEFT JOIN users ON users.user_id = track_scrobbles.user_id WHERE track_scrobbles.user_id IN ({}) AND track_scrobbles.artist_id = {} AND track_scrobbles.album_id = {} GROUP BY users.username ORDER BY percent DESC'.format(users_list, artist['id'], album['id'])
    logger.log(sql)
    cursor.execute(sql)
    result = list(cursor)
    total_scrobbles = sum([u['scrobbles'] for u in result])
    return {'artist': artist, 'album': album, 'users': result, 'total_scrobbles': total_scrobbles, 'total_users': len(users)}