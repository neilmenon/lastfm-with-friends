import mariadb
import datetime
import requests
from operator import itemgetter
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
            mdb.close()
            return None
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
    mdb.close()
    return {'artist': artist, 'users': result, 'total_scrobbles': total_scrobbles, 'total_users': len(users)}

def wk_album(query, users):
    mdb = mariadb.connect(**(cfg['sql']))
    cursor = mdb.cursor(dictionary=True)

    query = sql_helper.sanitize_query(query)
    try:
        artist_query = query.strip().split(" - ", 1)[0].strip()
        album_query = query.strip().split(" - ", 1)[1].strip()
    except IndexError:
        return False

    # find artist in the database
    sql = "SELECT * from artists WHERE {} LIKE '%{}%'".format(sql_helper.sanitize_db_field("name"), sql_helper.esc_db(artist_query))
    cursor.execute(sql)
    result = list(cursor)
    if not result:
        sql = "SELECT * from artist_redirects WHERE {} LIKE '%{}%'".format(sql_helper.sanitize_db_field("artist_name"), sql_helper.esc_db(artist_query))
        cursor.execute(sql)
        result = list(cursor)
        if not result:
            return None
        redirected_name = result[0]['redirected_name']
        sql = "SELECT * from artists WHERE name = '{}'".format(sql_helper.esc_db(redirected_name))
        cursor.execute(sql)
        result = list(cursor)
        artist = result[0]
    artist = result[0]

    # find album in the database
    sql = "SELECT * from albums WHERE artist_name = '{}' AND {} LIKE '%{}%'".format(sql_helper.esc_db(artist['name']), sql_helper.sanitize_db_field("name"), sql_helper.esc_db(album_query))
    cursor.execute(sql)
    result = list(cursor)
    if not result:
        return None
    album = result[0]

    # find users who have scrobbled this album
    users_list = ", ".join(str(u) for u in users)
    sql = 'SELECT users.username, COUNT(*) as scrobbles, users.scrobbles as total, CAST(ROUND((COUNT(*)/users.scrobbles)*100, 2) AS FLOAT) as percent FROM track_scrobbles LEFT JOIN users ON users.user_id = track_scrobbles.user_id WHERE track_scrobbles.user_id IN ({}) AND track_scrobbles.artist_id = {} AND track_scrobbles.album_id = {} GROUP BY users.username ORDER BY percent DESC'.format(users_list, artist['id'], album['id'])
    cursor.execute(sql)
    result = list(cursor)
    total_scrobbles = sum([u['scrobbles'] for u in result])
    mdb.close()
    return {'artist': artist, 'album': album, 'users': result, 'total_scrobbles': total_scrobbles, 'total_users': len(users)}

def wk_track(query, users):
    mdb = mariadb.connect(**(cfg['sql']))
    cursor = mdb.cursor(dictionary=True)

    query = sql_helper.sanitize_query(query)
    try:
        artist_query = query.strip().split(" - ", 1)[0].strip()
        track_query = query.strip().split(" - " , 1)[1].strip()
    except IndexError:
        return False

    # find artist in the database
    sql = "SELECT * from artists WHERE {} LIKE '%{}%'".format(sql_helper.sanitize_db_field("name"), sql_helper.esc_db(artist_query))
    cursor.execute(sql)
    result = list(cursor)
    if not result:
        sql = "SELECT * from artist_redirects WHERE {} LIKE '%{}%'".format(sql_helper.sanitize_db_field("artist_name"), sql_helper.esc_db(artist_query))
        cursor.execute(sql)
        result = list(cursor)
        if not result:
            return None
        redirected_name = result[0]['redirected_name']
        sql = "SELECT * from artists WHERE name = '{}'".format(sql_helper.esc_db(redirected_name))
        cursor.execute(sql)
        result = list(cursor)
        artist = result[0]
    artist = result[0]

    # find track in the database
    sql = "SELECT DISTINCT track as name, albums.image_url, albums.name as album_name from track_scrobbles LEFT JOIN albums ON track_scrobbles.album_id = albums.id WHERE artist_id = {} AND {} LIKE '%{}%'".format(artist['id'], sql_helper.sanitize_db_field("track"), sql_helper.esc_db(track_query))
    cursor.execute(sql)
    result = list(cursor)
    if not result:
        return None
    track = result[0]
    track['url'] = artist['url'] + "/" + track['album_name'].replace(" ", "+") + "/" + track['name'].replace(" ", "+")

    # find users who have scrobbled this album
    users_list = ", ".join(str(u) for u in users)
    sql = "SELECT users.username, COUNT(*) as scrobbles, users.scrobbles as total, CAST(ROUND((COUNT(*)/users.scrobbles)*100, 2) AS FLOAT) as percent FROM track_scrobbles LEFT JOIN users ON users.user_id = track_scrobbles.user_id WHERE track_scrobbles.user_id IN ({}) AND track_scrobbles.artist_id = {} AND track_scrobbles.track = '{}' GROUP BY users.username ORDER BY percent DESC".format(users_list, artist['id'], sql_helper.esc_db(track['name']))
    cursor.execute(sql)
    result = list(cursor)
    total_scrobbles = sum([u['scrobbles'] for u in result])
    return {'artist': artist, 'track': track, 'users': result, 'total_scrobbles': total_scrobbles, 'total_users': len(users)}

def nowplaying(join_code):
    mdb = mariadb.connect(**(cfg['sql']))
    cursor = mdb.cursor(dictionary=True)
    sql = "SELECT users.username, users.profile_image FROM user_groups LEFT JOIN users ON users.username = user_groups.username WHERE user_groups.group_jc = '{}' ORDER BY user_groups.joined ASC".format(join_code)
    cursor.execute(sql)
    users = list(cursor)
    mdb.close()
    now_playing_users = []
    played_users = []
    for user in users:
        req_url = 'http://ws.audioscrobbler.com/2.0/?method=user.getrecenttracks&user={}&api_key={}&limit=1&format=json'.format(user['username'], cfg['api']['key'])
        try:
            req = requests.get(req_url).json()
            track = req['recenttracks']['track'][0]
        except IndexError:
            continue
        except Exception as e:
            logger.log("Error getting most recently played track for {}: {}".format(user['username'], e))
            return False
        
        tmp_user = user
        tmp_user['artist'] = track['artist']['#text']
        tmp_user['track'] = track['name']
        tmp_user['album'] = track['album']['#text']
        tmp_user['url'] = track['url']
        tmp_user['image_url'] = track['image'][2]['#text']

        try:
            if track['@attr']['nowplaying'] == "true":
                tmp_user['timestamp'] = 0
        except KeyError:
            tmp_user['timestamp'] = int(track['date']['uts'])

        if tmp_user['timestamp']:
            played_users.append(tmp_user)
        else:
            now_playing_users.append(tmp_user)
    
    played_users = sorted(played_users, key=itemgetter('timestamp'), reverse=True)
    now_playing_users.extend(played_users)
    return now_playing_users