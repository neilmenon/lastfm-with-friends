import mariadb
import datetime
import requests
from operator import itemgetter
from . import config
from . import sql_helper
from . import api_logger as logger

cfg = config.config

def find_artist(query):
    mdb = mariadb.connect(**(cfg['sql']))
    cursor = mdb.cursor(dictionary=True)
    fallback = False
    # find artist in the database
    sanitized_query = sql_helper.sanitize_query(query)
    sql = "SELECT * from artists WHERE UPPER({}) = UPPER('{}')".format(sql_helper.sanitize_db_field("name"), sanitized_query)
    cursor.execute(sql)
    result = list(cursor)
    if not result:
        # fallback to LIKE
        sql = "SELECT * from artists WHERE {} LIKE '%{}%'".format(sql_helper.sanitize_db_field("name"), sanitized_query)
        cursor.execute(sql)
        result = list(cursor)
        if not result:
            # check artist redirects
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
        fallback = True
    artist = result[0]
    artist['fallback'] = fallback
    mdb.close()
    return artist

def wk_artist(query, users):
    artist = find_artist(query)
    if not artist:
        return None

    mdb = mariadb.connect(**(cfg['sql']))
    cursor = mdb.cursor(dictionary=True)

    # find users who have scrobbled this artist
    users_list = ", ".join(str(u) for u in users)
    sql = 'SELECT users.user_id as id, users.username, COUNT(*) as scrobbles, users.scrobbles as total, CAST(ROUND((COUNT(*)/users.scrobbles)*100, 2) AS FLOAT) as percent FROM track_scrobbles LEFT JOIN users ON users.user_id = track_scrobbles.user_id WHERE track_scrobbles.user_id IN ({}) AND track_scrobbles.artist_id = {} GROUP BY users.username order by scrobbles DESC'.format(users_list, artist['id'])
    cursor.execute(sql)
    result = list(cursor)
    total_scrobbles = sum([u['scrobbles'] for u in result])
    mdb.close()
    return {'artist': artist, 'users': result, 'total_scrobbles': total_scrobbles, 'total_users': len(users)}

def wk_album(query, users):
    query = sql_helper.sanitize_query(query)
    try:
        artist_query = query.strip().split(" - ", 1)[0].strip()
        album_query = query.strip().split(" - ", 1)[1].strip()
    except IndexError:
        return False

    artist = find_artist(artist_query)
    if not artist:
        return None

    mdb = mariadb.connect(**(cfg['sql']))
    cursor = mdb.cursor(dictionary=True)

    # find album in the database
    sql = "SELECT * from albums WHERE artist_name = '{}' AND UPPER({}) = UPPER('{}')".format(sql_helper.esc_db(artist['name']), sql_helper.sanitize_db_field("name"), sql_helper.esc_db(album_query))
    cursor.execute(sql)
    result = list(cursor)
    if not result:
        sql = "SELECT * from albums WHERE artist_name = '{}' AND {} LIKE '%{}%'".format(sql_helper.esc_db(artist['name']), sql_helper.sanitize_db_field("name"), sql_helper.esc_db(album_query))
        cursor.execute(sql)
        result = list(cursor)
        if not result:
            mdb.close()
            return None
    album = result[0]

    # find users who have scrobbled this album
    users_list = ", ".join(str(u) for u in users)
    sql = 'SELECT users.user_id as id, users.username, COUNT(*) as scrobbles, users.scrobbles as total, CAST(ROUND((COUNT(*)/users.scrobbles)*100, 2) AS FLOAT) as percent FROM track_scrobbles LEFT JOIN users ON users.user_id = track_scrobbles.user_id WHERE track_scrobbles.user_id IN ({}) AND track_scrobbles.artist_id = {} AND track_scrobbles.album_id = {} GROUP BY users.username order by scrobbles DESC'.format(users_list, artist['id'], album['id'])
    cursor.execute(sql)
    result = list(cursor)
    total_scrobbles = sum([u['scrobbles'] for u in result])
    mdb.close()
    return {'artist': artist, 'album': album, 'users': result, 'total_scrobbles': total_scrobbles, 'total_users': len(users)}

def wk_track(query, users):
    query = sql_helper.sanitize_query(query)
    try:
        artist_query = query.strip().split(" - ", 1)[0].strip()
        track_query = query.strip().split(" - " , 1)[1].strip()
    except IndexError:
        return False

    artist = find_artist(artist_query)
    if not artist:
        return None

    mdb = mariadb.connect(**(cfg['sql']))
    cursor = mdb.cursor(dictionary=True)

    # find track in the database
    sql = "SELECT DISTINCT track as name, albums.image_url, albums.name as album_name from track_scrobbles LEFT JOIN albums ON track_scrobbles.album_id = albums.id WHERE artist_id = {} AND UPPER({}) = UPPER('{}')".format(artist['id'], sql_helper.sanitize_db_field("track"), sql_helper.esc_db(track_query))
    cursor.execute(sql)
    result = list(cursor)
    if not result:
        sql = "SELECT DISTINCT track as name, albums.image_url, albums.name as album_name from track_scrobbles LEFT JOIN albums ON track_scrobbles.album_id = albums.id WHERE artist_id = {} AND {} LIKE '%{}%'".format(artist['id'], sql_helper.sanitize_db_field("track"), sql_helper.esc_db(track_query))
        cursor.execute(sql)
        result = list(cursor)
        if not result:
            mdb.close()
            return None
        track = result[0]
    track = result[0]
    track['url'] = artist['url'] + "/" + track['album_name'].replace(" ", "+") + "/" + track['name'].replace(" ", "+")

    # find users who have scrobbled this album
    users_list = ", ".join(str(u) for u in users)
    sql = "SELECT users.user_id as id, users.username, COUNT(*) as scrobbles, users.scrobbles as total, CAST(ROUND((COUNT(*)/users.scrobbles)*100, 2) AS FLOAT) as percent FROM track_scrobbles LEFT JOIN users ON users.user_id = track_scrobbles.user_id WHERE track_scrobbles.user_id IN ({}) AND track_scrobbles.artist_id = {} AND track_scrobbles.track = '{}' GROUP BY users.username order by scrobbles DESC".format(users_list, artist['id'], sql_helper.esc_db(track['name']))
    cursor.execute(sql)
    result = list(cursor)
    total_scrobbles = sum([u['scrobbles'] for u in result])
    mdb.close()
    return {'artist': artist, 'track': track, 'users': result, 'total_scrobbles': total_scrobbles, 'total_users': len(users)}

def nowplaying(join_code=None, database=False):
    mdb = mariadb.connect(**(cfg['sql']))
    cursor = mdb.cursor(dictionary=True)
    if join_code:
        sql = "SELECT users.username FROM user_groups LEFT JOIN users ON users.username = user_groups.username WHERE user_groups.group_jc = '{}' ORDER BY user_groups.joined ASC;".format(join_code)
    else:
        logger.log("Checking now playing activity for all users...")
        sql = "SELECT username FROM users;"
    cursor.execute(sql)
    users = list(cursor)
    now_playing_users = []
    played_users = []
    for user in users:
        req_url = 'http://ws.audioscrobbler.com/2.0/?method=user.getrecenttracks&user={}&api_key={}&limit=1&format=json'.format(user['username'], cfg['api']['key'])
        try:
            req = requests.get(req_url).json()
            track = req['recenttracks']['track'][0]
        except (IndexError, KeyError, requests.exceptions.RequestException) as e:
            logger.log("Error getting most recently played track for {}: {}. Continuing...".format(user['username'], e))
            continue
        except Exception as e:
            logger.log("[FATAL] Error getting most recently played track for {}: {}".format(user['username'], e))
            mdb.close()
            return False
        
        tmp_user = user
        tmp_user['artist'] = sql_helper.esc_db(track['artist']['#text'])
        tmp_user['track'] = sql_helper.esc_db(track['name'])
        tmp_user['album'] = sql_helper.esc_db(track['album']['#text'])
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

        if database:
            sql = sql_helper.replace_into("now_playing", tmp_user)
            cursor.execute(sql)
            mdb.commit()
    
    played_users = sorted(played_users, key=itemgetter('timestamp'), reverse=True)
    now_playing_users.extend(played_users)
    mdb.close()
    if database:
        return True
    else:
        return now_playing_users

def get_nowplaying(join_code):
    mdb = mariadb.connect(**(cfg['sql']))
    cursor = mdb.cursor(dictionary=True)
    sql = "SELECT now_playing.* FROM user_groups LEFT JOIN now_playing ON now_playing.username = user_groups.username WHERE user_groups.group_jc = '{}' ORDER BY IF(now_playing.timestamp = 0, 9999999999, now_playing.timestamp) DESC, user_groups.joined ASC".format(join_code)
    cursor.execute(sql)
    result = list(cursor)
    mdb.close()
    return result

def play_history(wk_mode, artist_id, users, track=None, album_id=None, sort_by="track_scrobbles.timestamp", sort_order="DESC", limit=50, offset=0):
    mdb = mariadb.connect(**(cfg['sql']))
    cursor = mdb.cursor(dictionary=True)
    users_list = ", ".join(str(u) for u in users)
    
    if wk_mode == "track":
        sql = "SELECT users.username, artists.name as artist, artists.url as artist_url, albums.url as album_url, track_scrobbles.track, albums.name as album, track_scrobbles.timestamp, COUNT(*) OVER() as total FROM `track_scrobbles` LEFT JOIN users ON users.user_id = track_scrobbles.user_id LEFT JOIN artists ON artists.id = track_scrobbles.artist_id LEFT JOIN albums ON albums.id = track_scrobbles.album_id WHERE track_scrobbles.user_id IN ({}) AND artists.id = {} AND track_scrobbles.track = '{}' ORDER BY {} {}, track_scrobbles.timestamp DESC LIMIT {} OFFSET {}".format(users_list, artist_id, sql_helper.esc_db(track), sort_by, sort_order, limit, offset)
    elif wk_mode == "album":
        sql = "SELECT users.username, artists.name as artist, artists.url as artist_url, albums.url as album_url, track_scrobbles.track, albums.name as album, track_scrobbles.timestamp, COUNT(*) OVER() as total FROM `track_scrobbles` LEFT JOIN users ON users.user_id = track_scrobbles.user_id LEFT JOIN artists ON artists.id = track_scrobbles.artist_id LEFT JOIN albums ON albums.id = track_scrobbles.album_id WHERE track_scrobbles.user_id IN ({}) AND artists.id = {} AND track_scrobbles.album_id = {} ORDER BY {} {}, track_scrobbles.timestamp DESC LIMIT {} OFFSET {}".format(users_list, artist_id, album_id, sort_by, sort_order, limit, offset)
    elif wk_mode == "artist":
        sql = "SELECT users.username, artists.name as artist, artists.url as artist_url, albums.url as album_url, track_scrobbles.track, albums.name as album, track_scrobbles.timestamp, COUNT(*) OVER() as total FROM `track_scrobbles` LEFT JOIN users ON users.user_id = track_scrobbles.user_id LEFT JOIN artists ON artists.id = track_scrobbles.artist_id LEFT JOIN albums ON albums.id = track_scrobbles.album_id WHERE track_scrobbles.user_id IN ({}) AND artists.id = {} ORDER BY {} {}, track_scrobbles.timestamp DESC LIMIT {} OFFSET {}".format(users_list, artist_id, sort_by, sort_order, limit, offset)
    elif wk_mode == "overall":
        sql = "SELECT users.username, artists.name as artist, artists.url as artist_url, albums.url as album_url, track_scrobbles.track, albums.name as album, track_scrobbles.timestamp, COUNT(*) OVER() as total FROM `track_scrobbles` LEFT JOIN users ON users.user_id = track_scrobbles.user_id LEFT JOIN artists ON artists.id = track_scrobbles.artist_id LEFT JOIN albums ON albums.id = track_scrobbles.album_id WHERE track_scrobbles.user_id IN ({}) ORDER BY {} {}, track_scrobbles.timestamp DESC LIMIT {} OFFSET {}".format(users_list, sort_by, sort_order, limit, offset)
    else:
        return False
    cursor.execute(sql)
    records = list(cursor)
    if not records:
        return None
    total = records[0]['total']
    for r in records:
        r.pop("total")
        r['track_url'] = r['artist_url'] + "/" + r['album'].replace(" ", "+") + "/" + r['track'].replace(" ", "+")
    data = {
        'records': records,
        'total': total,
        'limit': limit,
        'offset': offset
    }
    mdb.close()
    return data