import mariadb
import datetime
import requests
import dateutil.parser
import math
from operator import itemgetter
from . import config
from . import sql_helper
from . import api_logger as logger

cfg = config.config

def find_artist(query, skip_sanitize=False):
    mdb = mariadb.connect(**(cfg['sql']))
    cursor = mdb.cursor(dictionary=True)
    fallback = False
    redirect = False
    # find artist in the database
    if not skip_sanitize:
        sanitized_query = sql_helper.sanitize_query(query)
    else:
        sanitized_query = query
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
            sql = "SELECT * from artist_redirects WHERE UPPER({}) = UPPER('{}')".format(sql_helper.sanitize_db_field("artist_name"), sql_helper.esc_db(sanitized_query))
            cursor.execute(sql)
            result = list(cursor)
            if not result:
                mdb.close()
                return None
            redirect = True
            redirected_name = result[0]['redirected_name']
            sql = "SELECT * from artists WHERE name = '{}'".format(sql_helper.esc_db(redirected_name))
            cursor.execute(sql)
            result = list(cursor)
        fallback = True
    artist = result[0]
    artist['fallback'] = fallback
    artist['redirect'] = redirect
    mdb.close()
    return artist

def find_album_tracks(album_id):
    # find the tracks that are associated with this album
    # need to do this because, technically, tracks can appear in several albums, but Last.fm still counts them all towards
    # the album being viewed
    mdb = mariadb.connect(**(cfg['sql']))
    cursor = mdb.cursor(dictionary=True)
    sql = "SELECT track from track_scrobbles WHERE album_id = {} GROUP BY track".format(album_id)
    cursor.execute(sql)
    result = list(cursor)
    album_tracks_list = ', '.join('"' + str(sql_helper.esc_db(track)).replace('"', '\\"') + '"' for track in [r['track'] for r in result])
    mdb.close()
    return album_tracks_list

def wk_artist(query, users):
    if not query:
        return None
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

    # find album tracks from this album
    album_tracks_list = find_album_tracks(album['id'])

    if album_tracks_list:
        # find users who have scrobbled this album
        users_list = ", ".join(str(u) for u in users)
        sql = 'SELECT users.user_id as id, users.username, COUNT(*) as scrobbles, users.scrobbles as total, CAST(ROUND((COUNT(*)/users.scrobbles)*100, 2) AS FLOAT) as percent FROM track_scrobbles LEFT JOIN users ON users.user_id = track_scrobbles.user_id WHERE track_scrobbles.user_id IN ({}) AND track_scrobbles.artist_id = {} AND track_scrobbles.track IN ({}) GROUP BY users.username order by scrobbles DESC'.format(users_list, artist['id'], album_tracks_list)
        cursor.execute(sql)
        result = list(cursor)
        total_scrobbles = sum([u['scrobbles'] for u in result])
    else:
        result = []
        total_scrobbles = 0
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
    track['url'] = artist['url'] + "/" + track['album_name'].replace(" ", "+").replace("/", "%2F") + "/" + track['name'].replace(" ", "+").replace("/", "%2F")
    # find users who have scrobbled this album
    users_list = ", ".join(str(u) for u in users)
    sql = "SELECT users.user_id as id, users.username, COUNT(*) as scrobbles, users.scrobbles as total, CAST(ROUND((COUNT(*)/users.scrobbles)*100, 2) AS FLOAT) as percent FROM track_scrobbles LEFT JOIN users ON users.user_id = track_scrobbles.user_id WHERE track_scrobbles.user_id IN ({}) AND track_scrobbles.artist_id = {} AND track_scrobbles.track = '{}' GROUP BY users.username order by scrobbles DESC".format(users_list, artist['id'], sql_helper.esc_db(track['name']))
    cursor.execute(sql)
    result = list(cursor)
    total_scrobbles = sum([u['scrobbles'] for u in result])
    mdb.close()
    return {'artist': artist, 'track': track, 'users': result, 'total_scrobbles': total_scrobbles, 'total_users': len(users)}

def nowplaying(join_code=None, database=False, single_user=None):
    mdb = mariadb.connect(**(cfg['sql']))
    cursor = mdb.cursor(dictionary=True)
    if not single_user:
        if join_code:
            sql = "SELECT users.username FROM user_groups LEFT JOIN users ON users.username = user_groups.username WHERE user_groups.group_jc = '{}' ORDER BY user_groups.joined ASC;".format(join_code)
        else:
            logger.log("Checking now playing activity for all users...")
            sql = "SELECT username FROM users;"
        cursor.execute(sql)
        users = list(cursor)
    else:
        logger.log("Checking now playing for individual user {}".format(single_user))
        users = [{'username': single_user}]
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
    sql = "SELECT now_playing.* FROM user_groups LEFT JOIN now_playing ON now_playing.username = user_groups.username WHERE user_groups.group_jc = '{}' AND now_playing.username IS NOT NULL ORDER BY IF(now_playing.timestamp = 0, 9999999999, now_playing.timestamp) DESC, user_groups.joined ASC".format(join_code)
    cursor.execute(sql)
    result = list(cursor)
    mdb.close()
    return result

def play_history(wk_mode, artist_id, users, track=None, album_id=None, sort_by="track_scrobbles.timestamp", sort_order="DESC", limit=50, offset=0):
    mdb = mariadb.connect(**(cfg['sql']))
    cursor = mdb.cursor(dictionary=True)
    users_list = ", ".join(str(u) for u in users)
    
    if wk_mode == "track":
        sql = "SELECT users.user_id ,users.username, artists.name as artist, artists.url as artist_url, albums.url as album_url, track_scrobbles.track, albums.name as album, track_scrobbles.timestamp, COUNT(*) OVER() as total FROM `track_scrobbles` LEFT JOIN users ON users.user_id = track_scrobbles.user_id LEFT JOIN artists ON artists.id = track_scrobbles.artist_id LEFT JOIN albums ON albums.id = track_scrobbles.album_id WHERE track_scrobbles.user_id IN ({}) AND artists.id = {} AND track_scrobbles.track = '{}' ORDER BY {} {}, track_scrobbles.timestamp DESC LIMIT {} OFFSET {}".format(users_list, artist_id, sql_helper.esc_db(track), sort_by, sort_order, limit, offset)
    elif wk_mode == "album":
        album_tracks_list = find_album_tracks(album_id)
        sql = "SELECT users.user_id ,users.username, artists.name as artist, artists.url as artist_url, albums.url as album_url, track_scrobbles.track, albums.name as album, track_scrobbles.timestamp, COUNT(*) OVER() as total FROM `track_scrobbles` LEFT JOIN users ON users.user_id = track_scrobbles.user_id LEFT JOIN artists ON artists.id = track_scrobbles.artist_id LEFT JOIN albums ON albums.id = track_scrobbles.album_id WHERE track_scrobbles.user_id IN ({}) AND artists.id = {} AND track_scrobbles.track IN ({}) ORDER BY {} {}, track_scrobbles.timestamp DESC LIMIT {} OFFSET {}".format(users_list, artist_id, album_tracks_list, sort_by, sort_order, limit, offset)
    elif wk_mode == "artist":
        sql = "SELECT users.user_id ,users.username, artists.name as artist, artists.url as artist_url, albums.url as album_url, track_scrobbles.track, albums.name as album, track_scrobbles.timestamp, COUNT(*) OVER() as total FROM `track_scrobbles` LEFT JOIN users ON users.user_id = track_scrobbles.user_id LEFT JOIN artists ON artists.id = track_scrobbles.artist_id LEFT JOIN albums ON albums.id = track_scrobbles.album_id WHERE track_scrobbles.user_id IN ({}) AND artists.id = {} ORDER BY {} {}, track_scrobbles.timestamp DESC LIMIT {} OFFSET {}".format(users_list, artist_id, sort_by, sort_order, limit, offset)
    elif wk_mode == "overall":
        sql = "SELECT users.user_id ,users.username, artists.name as artist, artists.url as artist_url, albums.url as album_url, track_scrobbles.track, albums.name as album, track_scrobbles.timestamp, COUNT(*) OVER() as total FROM `track_scrobbles` LEFT JOIN users ON users.user_id = track_scrobbles.user_id LEFT JOIN artists ON artists.id = track_scrobbles.artist_id LEFT JOIN albums ON albums.id = track_scrobbles.album_id WHERE track_scrobbles.user_id IN ({}) ORDER BY {} {}, track_scrobbles.timestamp DESC LIMIT {} OFFSET {}".format(users_list, sort_by, sort_order, limit, offset)
    else:
        return False
    cursor.execute(sql)
    records = list(cursor)
    if not records:
        return None
    total = records[0]['total']
    for r in records:
        r.pop("total")
        r['track_url'] = r['artist_url'] + "/" + r['album'].replace(" ", "+").replace("/", "%2F") + "/" + r['track'].replace(" ", "+").replace("/", "%2F")
    data = {
        'records': records,
        'total': total,
        'limit': limit,
        'offset': offset
    }
    mdb.close()
    return data

def wk_top(wk_mode, users, artist_id, album_id=None, track_mode=False):
    mdb = mariadb.connect(**(cfg['sql']))
    cursor = mdb.cursor(dictionary=True)
    users_list = ", ".join(str(u) for u in users)

    if wk_mode == "artist":
        if track_mode:
            sql = "SELECT track_scrobbles.track, albums.name as album, albums.id as album_id, albums.url as album_url, albums.image_url, COUNT(*) as scrobbles FROM track_scrobbles LEFT JOIN artists on artists.id = track_scrobbles.artist_id LEFT JOIN albums on albums.id = track_scrobbles.album_id WHERE track_scrobbles.user_id IN ({}) AND track_scrobbles.artist_id = {} GROUP BY track_scrobbles.track ORDER BY scrobbles DESC".format(users_list, artist_id)
        else:
            sql = "SELECT albums.name as album, albums.id as album_id, albums.url as album_url, albums.image_url, COUNT(*) as scrobbles FROM track_scrobbles LEFT JOIN artists on artists.id = track_scrobbles.artist_id LEFT JOIN albums on albums.id = track_scrobbles.album_id WHERE track_scrobbles.user_id IN ({}) AND track_scrobbles.artist_id = {} GROUP BY track_scrobbles.album_id ORDER BY scrobbles DESC".format(users_list, artist_id)
    elif wk_mode == "album":
        album_tracks_list = find_album_tracks(album_id)
        sql = "SELECT albums.name as album, albums.id as album_id, track_scrobbles.track, albums.url as album_url, albums.image_url, COUNT(*) as scrobbles FROM track_scrobbles LEFT JOIN artists on artists.id = track_scrobbles.artist_id LEFT JOIN albums on albums.id = track_scrobbles.album_id WHERE track_scrobbles.user_id IN ({}) AND track_scrobbles.artist_id = {} AND track_scrobbles.track IN ({}) GROUP BY track_scrobbles.track ORDER BY scrobbles DESC".format(users_list, artist_id, album_tracks_list)
    cursor.execute(sql)
    records = list(cursor)
    if not records:
        return None
    elif wk_mode == "album" or track_mode:
        for r in records:
            r['track_url'] = r['album_url'] + "/" + r['track'].replace(" ", "+").replace("/", "%2F")
    mdb.close()
    
    return records

def scrobble_leaderboard(users, start_range, end_range):
    mdb = mariadb.connect(**(cfg['sql']))
    cursor = mdb.cursor(dictionary=True)
    users_list = ", ".join(str(u) for u in users)

    if not start_range or not end_range:
        sql = "SELECT users.username, users.profile_image, COUNT(*) as scrobbles FROM `track_scrobbles` LEFT JOIN users on users.user_id = track_scrobbles.user_id WHERE track_scrobbles.user_id IN ({}) GROUP BY track_scrobbles.user_id ORDER BY scrobbles DESC".format(users_list)
    else:
        cursor.execute("SET time_zone='+00:00';")
        sql = "SELECT users.username, users.profile_image, COUNT(*) as scrobbles FROM `track_scrobbles` LEFT JOIN users on users.user_id = track_scrobbles.user_id WHERE from_unixtime(track_scrobbles.timestamp) BETWEEN '{}' AND '{}' AND track_scrobbles.user_id IN ({}) GROUP BY track_scrobbles.user_id ORDER BY scrobbles DESC;".format(start_range, end_range, users_list)
    cursor.execute(sql)
    leaderboard = list(cursor)

    mdb.close()
    return {'leaderboard': leaderboard, 'start_range': start_range, 'end_range': end_range}

def wk_autocomplete(wk_mode, query):
    if len(query.strip()) < 2:
        return []
    mdb = mariadb.connect(**(cfg['sql']))
    cursor = mdb.cursor(dictionary=True)

    sanitized_query = sql_helper.sanitize_query(query)
    partial_result = False

    if wk_mode == "artist":
        sql = "SELECT name from artists WHERE {} LIKE '%{}%' LIMIT 10".format(sql_helper.sanitize_db_field("name"), sanitized_query)
        cursor.execute(sql)
        artists = list(cursor)
        suggestions = [r["name"] for r in artists]
    else: # album or track
        release_query = ""
        typing_release = True
        try:
            artist_query = sanitized_query.split(" - ", 1)[0].strip()
            release_query = sanitized_query.split(" - ", 1)[1].strip()
        except IndexError: # means the user is still typing the artist's name
            typing_release = False
        if typing_release:
            valid_artist = find_artist(artist_query, skip_sanitize=True)
            if valid_artist:
                if wk_mode == "album":
                    if release_query:
                        sql = "SELECT name from albums WHERE artist_name = '{}' AND {} LIKE '%{}%' LIMIT 10".format(sql_helper.esc_db(valid_artist['name']), sql_helper.sanitize_db_field("name"), sql_helper.esc_db(release_query))
                    else:
                        sql = "SELECT name from albums WHERE artist_name = '{}' LIMIT 10".format(sql_helper.esc_db(valid_artist['name']))
                    cursor.execute(sql)
                    albums = list(cursor)
                    suggestions = [valid_artist['name'] + " - " + a['name'] for a in albums]
                else: # track
                    if release_query:
                        sql = "SELECT DISTINCT track as name FROM track_scrobbles WHERE artist_id = {} AND {} LIKE '%{}%' LIMIT 10".format(valid_artist['id'], sql_helper.sanitize_db_field("track"), sql_helper.esc_db(release_query))
                    else:
                        sql = "SELECT track as name, COUNT(*) as scrobbles FROM track_scrobbles WHERE artist_id = {} GROUP BY track ORDER BY scrobbles DESC LIMIT 10".format(valid_artist['id'])
                    cursor.execute(sql)
                    tracks = list(cursor)
                    suggestions = [valid_artist['name'] + " - " + t['name'] for t in tracks]
            else:
                suggestions = []
        else:
            sql = "SELECT name from artists WHERE {} LIKE '%{}%' LIMIT 10".format(sql_helper.sanitize_db_field("name"), sanitized_query)
            cursor.execute(sql)
            artists = list(cursor)
            suggestions = [r["name"] + " - " for r in artists]
            partial_result = True
    
    mdb.close()
    return {'suggestions': suggestions, 'partial_result': partial_result}

def check_artist_redirect(artist_string):
    artist_string = artist_string.strip()
    req_url = "http://ws.audioscrobbler.com/2.0/?method=artist.getcorrection&artist={}&api_key={}&format=json".format(artist_string, cfg['api']['key'])
    try:
        lastfm = requests.get(req_url).json()
        correction = lastfm['corrections']
    except (IndexError, KeyError, requests.exceptions.RequestException) as e:
        logger.log("Error checking for artist redirect for {}: {}.".format(artist_string, e))
        return None
    except Exception as e:
        logger.log("Another error occured checking for artist redirect for {}: {}.".format(artist_string, e))
        return None
    
    try:
        if correction['correction']['artist']['name'].lower() == artist_string.lower(): # no redirect exists for this artist
            return False
        else: # the redirect exists! store it in the database and return it to the user
            artist_name = correction['correction']['artist']['name']
            artist_in_db = find_artist(artist_name)
            if artist_in_db:
                if artist_in_db['fallback'] or artist_in_db['redirect']:
                    return False
            else:
                return False
            
            mdb = mariadb.connect(**(cfg['sql']))
            cursor = mdb.cursor(dictionary=True)

            data = {'artist_name': sql_helper.esc_db(artist_string), 'redirected_name': sql_helper.esc_db(artist_name)}
            sql = sql_helper.insert_into_where_not_exists("artist_redirects", data, "artist_name")
            cursor.execute(sql)
            mdb.commit()
            mdb.close()
            return {'artist': artist_name}
    except (KeyError, TypeError) as e: # this probably means the artist doesn't even exist in Last.fm's db either
        try:
            mdb.close()
        except Exception:
            pass
        return False

def charts(chart_mode, chart_type, users, start_range, end_range):
    mdb = mariadb.connect(**(cfg['sql']))
    cursor = mdb.cursor(dictionary=True)
    entry_limit = 250
    user_charts = []
    group_chart = {}
    days_range = 365
    cursor.execute("SET time_zone='+00:00';")
    
    if chart_mode == "individual":
        users = [users[0]]
    if start_range and end_range:
        days_range = (dateutil.parser.parse(end_range) - dateutil.parser.parse(start_range)).days

    for user in users:
        if chart_type == "track":
            if not start_range or not end_range:
                sql = "SELECT artists.name as artist, artists.id as artist_id, artists.url as artist_url, artists.image_url as artist_image, track_scrobbles.track, albums.image_url as image, COUNT(*) as scrobbles FROM `track_scrobbles` LEFT JOIN artists ON artists.id = track_scrobbles.artist_id LEFT JOIN albums ON albums.id = track_scrobbles.album_id WHERE track_scrobbles.user_id = {} GROUP BY track_scrobbles.track ORDER BY scrobbles DESC LIMIT {}".format(user, entry_limit)
            else:
                sql = "SELECT artists.name as artist, artists.id as artist_id, artists.url as artist_url, artists.image_url as artist_image, track_scrobbles.track, albums.image_url as image, COUNT(*) as scrobbles FROM `track_scrobbles` LEFT JOIN artists ON artists.id = track_scrobbles.artist_id LEFT JOIN albums ON albums.id = track_scrobbles.album_id WHERE track_scrobbles.user_id = {} AND from_unixtime(track_scrobbles.timestamp) BETWEEN '{}' AND '{}' GROUP BY track_scrobbles.track ORDER BY scrobbles DESC LIMIT {}".format(user, start_range, end_range, entry_limit)
        elif chart_type == "album":
            if not start_range or not end_range:
                sql = "SELECT artists.name as artist, artists.id as artist_id, artists.url as artist_url, artists.image_url as artist_image, albums.name as album, albums.id as album_id, albums.url as url, albums.image_url as image, COUNT(*) as scrobbles FROM `track_scrobbles` LEFT JOIN artists ON artists.id = track_scrobbles.artist_id LEFT JOIN albums ON albums.id = track_scrobbles.album_id WHERE track_scrobbles.user_id = {} GROUP BY track_scrobbles.album_id ORDER BY scrobbles DESC LIMIT {}".format(user, entry_limit)
            else:
                sql = "SELECT artists.name as artist, artists.id as artist_id, artists.url as artist_url, artists.image_url as artist_image, albums.name as album, albums.id as album_id, albums.url as url, albums.image_url as image, COUNT(*) as scrobbles FROM `track_scrobbles` LEFT JOIN artists ON artists.id = track_scrobbles.artist_id LEFT JOIN albums ON albums.id = track_scrobbles.album_id WHERE track_scrobbles.user_id = {} AND from_unixtime(track_scrobbles.timestamp) BETWEEN '{}' AND '{}' GROUP BY track_scrobbles.album_id ORDER BY scrobbles DESC LIMIT {}".format(user, start_range, end_range, entry_limit)
        else: # artist
            if not start_range or not end_range:
                sql = "SELECT artists.name as artist, artists.id as artist_id, artists.url as artist_url, artists.image_url as artist_image, COUNT(*) as scrobbles FROM `track_scrobbles` LEFT JOIN artists ON artists.id = track_scrobbles.artist_id WHERE track_scrobbles.user_id = {} GROUP BY track_scrobbles.artist_id ORDER BY scrobbles DESC LIMIT {}".format(user, entry_limit)
            else:
                sql = "SELECT artists.name as artist, artists.id as artist_id, artists.url as artist_url, artists.image_url as artist_image, COUNT(*) as scrobbles FROM `track_scrobbles` LEFT JOIN artists ON artists.id = track_scrobbles.artist_id WHERE track_scrobbles.user_id = {} AND from_unixtime(track_scrobbles.timestamp) BETWEEN '{}' AND '{}' GROUP BY track_scrobbles.artist_id ORDER BY scrobbles DESC LIMIT {}".format(user, start_range, end_range, entry_limit)
        cursor.execute(sql)
        result = list(cursor)
        user_charts.append(result)
    mdb.close()
   
    if chart_mode == "individual":
        result = user_charts[0]
        if chart_type == "track":
            for entry in result:
                entry['url'] = entry['artist_url'] + "/_/" + entry['track'].replace(" ", "+").replace("/", "%2F")
        return result
    else: # group
        for chart in user_charts:
            for entry in chart:
                if chart_type == "track":
                    entry_key = str(entry['artist_id']) + "." + entry['track']
                    entry['url'] = entry['artist_url'] + "/_/" + entry['track'].replace(" ", "+").replace("/", "%2F")
                elif chart_type == "album":
                    entry_key = str(entry['artist_id']) + "." + str(entry['album_id'])
                else:
                    entry_key = str(entry['artist_id'])
                if entry_key in group_chart.keys():
                    group_chart[entry_key]['scrobbles'] += entry['scrobbles']
                    group_chart[entry_key]['score'] += math.log(entry['scrobbles'])
                else:
                    group_chart[entry_key] = entry
                    group_chart[entry_key]['score'] = math.log(entry['scrobbles'])
        group_chart_final = sorted([v for k,v in group_chart.items()], key=itemgetter('score'), reverse=True)
        return group_chart_final[:50]
