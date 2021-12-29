import datetime
import requests
import dateutil.parser
import math
from operator import itemgetter
from . import config
from . import sql_helper
from . import group_helper
from . import api_logger as logger

cfg = config.config

def find_artist(query, skip_sanitize=False, extended=False):
    columns_to_fetch = "*" if extended else "id, name, url, image_url"
    fallback = False
    redirect = False
    # find artist in the database
    if not skip_sanitize:
        sanitized_query = sql_helper.sanitize_query(query)
    else:
        sanitized_query = query
    sql = "SELECT {} from artists WHERE UPPER({}) = UPPER('{}')".format(columns_to_fetch, sql_helper.sanitize_db_field("name"), sanitized_query)
    result = sql_helper.execute_db(sql)
    if not result:
        # fallback to LIKE
        sql = "SELECT {} from artists WHERE {} LIKE '%{}%'".format(columns_to_fetch, sql_helper.sanitize_db_field("name"), sanitized_query)
        result = sql_helper.execute_db(sql)
        if not result:
            # check artist redirects
            sql = "SELECT * from artist_redirects WHERE UPPER({}) = UPPER('{}')".format(sql_helper.sanitize_db_field("artist_name"), sql_helper.esc_db(sanitized_query))
            result = sql_helper.execute_db(sql)
            if not result:
                return None
            redirect = True
            redirected_name = result[0]['redirected_name']
            sql = "SELECT {} from artists WHERE name = '{}'".format(columns_to_fetch, sql_helper.esc_db(redirected_name))
            result = sql_helper.execute_db(sql)
        fallback = True
    single_check = list(filter(lambda x: x['name'].upper() == query.upper(), result))
    artist = result[0] if len(single_check) != 1 else single_check[0]
    artist['fallback'] = fallback
    artist['redirect'] = redirect

    # get genres if extended mode
    if extended:
        artist['genres'] = sql_helper.execute_db("SELECT genres.* FROM genres LEFT JOIN artist_genres ON artist_genres.genre_id = genres.id WHERE artist_genres.artist_id = {}".format(artist['id']))
    return artist

def find_album_tracks(album_id):
    # find the tracks that are associated with this album
    # need to do this because, technically, tracks can appear in several albums, but Last.fm still counts them all towards
    # the album being viewed
    sql = "SELECT track from track_scrobbles WHERE album_id = {} GROUP BY track".format(album_id)
    result = sql_helper.execute_db(sql)
    album_tracks_list = ', '.join('"' + str(sql_helper.esc_db(track)).replace('"', '\\"') + '"' for track in [r['track'] for r in result])
    return album_tracks_list

def wk_artist(query, users, start_range, end_range):
    if not query:
        return None
    artist = find_artist(query, extended=True)
    if not artist:
        return None

    # find users who have scrobbled this artist
    users_list = ", ".join(str(u) for u in users)
    if start_range and end_range:
        sql = 'SELECT users.user_id as id, users.username, COUNT(*) as scrobbles, CAST(ROUND((COUNT(*)/users.scrobbles)*100, 2) AS FLOAT) as percent FROM track_scrobbles LEFT JOIN users ON users.user_id = track_scrobbles.user_id WHERE track_scrobbles.user_id IN ({}) AND track_scrobbles.artist_id = {} AND from_unixtime(track_scrobbles.timestamp) BETWEEN "{}" AND "{}" GROUP BY users.username order by scrobbles DESC'.format(users_list, artist['id'], start_range, end_range)
    else:
        sql = 'SELECT users.user_id as id, users.username, COUNT(*) as scrobbles, CAST(ROUND((COUNT(*)/users.scrobbles)*100, 2) AS FLOAT) as percent FROM track_scrobbles LEFT JOIN users ON users.user_id = track_scrobbles.user_id WHERE track_scrobbles.user_id IN ({}) AND track_scrobbles.artist_id = {} GROUP BY users.username order by scrobbles DESC'.format(users_list, artist['id'])
    result = sql_helper.execute_db(sql, tz=True)
    total_scrobbles = sum([u['scrobbles'] for u in result])
    return {'artist': artist, 'users': result, 'total_scrobbles': total_scrobbles, 'total_users': len(users)}

def wk_album(query, users, start_range, end_range):
    query = sql_helper.sanitize_query(query)
    try:
        artist_query = query.strip().split(" - ", 1)[0].strip()
        album_query = query.strip().split(" - ", 1)[1].strip()
    except IndexError:
        return False

    artist = find_artist(artist_query)
    if not artist:
        return None

    # find album in the database
    sql = "SELECT * from albums WHERE artist_name = '{}' AND UPPER({}) = UPPER('{}')".format(sql_helper.esc_db(artist['name']), sql_helper.sanitize_db_field("name"), sql_helper.esc_db(album_query))
    result = sql_helper.execute_db(sql, tz=True)
    if not result:
        sql = "SELECT * from albums WHERE artist_name = '{}' AND {} LIKE '%{}%'".format(sql_helper.esc_db(artist['name']), sql_helper.sanitize_db_field("name"), sql_helper.esc_db(album_query))
        result = sql_helper.execute_db(sql, tz=True)
        if not result:
            return None
    album = result[0]

    # find album tracks from this album
    album_tracks_list = find_album_tracks(album['id'])

    if album_tracks_list:
        # find users who have scrobbled this album
        users_list = ", ".join(str(u) for u in users)
        if start_range and end_range:
            sql = 'SELECT users.user_id as id, users.username, COUNT(*) as scrobbles, CAST(ROUND((COUNT(*)/users.scrobbles)*100, 2) AS FLOAT) as percent FROM track_scrobbles LEFT JOIN users ON users.user_id = track_scrobbles.user_id WHERE track_scrobbles.user_id IN ({}) AND track_scrobbles.artist_id = {} AND track_scrobbles.track IN ({}) AND from_unixtime(track_scrobbles.timestamp) BETWEEN "{}" AND "{}" GROUP BY users.username order by scrobbles DESC'.format(users_list, artist['id'], album_tracks_list, start_range, end_range)
        else:
            sql = 'SELECT users.user_id as id, users.username, COUNT(*) as scrobbles, CAST(ROUND((COUNT(*)/users.scrobbles)*100, 2) AS FLOAT) as percent FROM track_scrobbles LEFT JOIN users ON users.user_id = track_scrobbles.user_id WHERE track_scrobbles.user_id IN ({}) AND track_scrobbles.artist_id = {} AND track_scrobbles.track IN ({}) GROUP BY users.username order by scrobbles DESC'.format(users_list, artist['id'], album_tracks_list)
        result = sql_helper.execute_db(sql)
        total_scrobbles = sum([u['scrobbles'] for u in result])
    else:
        result = []
        total_scrobbles = 0
    return {'artist': artist, 'album': album, 'users': result, 'total_scrobbles': total_scrobbles, 'total_users': len(users)}

def wk_track(query, users, start_range, end_range):
    query = sql_helper.sanitize_query(query)
    try:
        artist_query = query.strip().split(" - ", 1)[0].strip()
        track_query = query.strip().split(" - " , 1)[1].strip()
    except IndexError:
        return False

    artist = find_artist(artist_query)
    if not artist:
        return None

    # find track in the database
    sql = "SELECT DISTINCT track as name, albums.image_url, albums.name as album_name from track_scrobbles LEFT JOIN albums ON track_scrobbles.album_id = albums.id WHERE artist_id = {} AND UPPER({}) = UPPER('{}')".format(artist['id'], sql_helper.sanitize_db_field("track"), sql_helper.esc_db(track_query))
    result = sql_helper.execute_db(sql, tz=True)
    if not result:
        sql = "SELECT DISTINCT track as name, albums.image_url, albums.name as album_name from track_scrobbles LEFT JOIN albums ON track_scrobbles.album_id = albums.id WHERE artist_id = {} AND {} LIKE '%{}%'".format(artist['id'], sql_helper.sanitize_db_field("track"), sql_helper.esc_db(track_query))
        result = sql_helper.execute_db(sql, tz=True)
        if not result:
            return None
        track = result[0]
    track = result[0]
    track['url'] = artist['url'] + "/_/" + sql_helper.format_lastfm_string(track['name'])
    # find users who have scrobbled this track
    users_list = ", ".join(str(u) for u in users)
    if start_range and end_range:
        sql = "SELECT users.user_id as id, users.username, COUNT(*) as scrobbles, CAST(ROUND((COUNT(*)/users.scrobbles)*100, 2) AS FLOAT) as percent FROM track_scrobbles LEFT JOIN users ON users.user_id = track_scrobbles.user_id WHERE track_scrobbles.user_id IN ({}) AND track_scrobbles.artist_id = {} AND track_scrobbles.track = '{}' AND from_unixtime(track_scrobbles.timestamp) BETWEEN '{}' AND '{}' GROUP BY users.username order by scrobbles DESC".format(users_list, artist['id'], sql_helper.esc_db(track['name']), start_range, end_range)
    else:
        sql = "SELECT users.user_id as id, users.username, COUNT(*) as scrobbles, CAST(ROUND((COUNT(*)/users.scrobbles)*100, 2) AS FLOAT) as percent FROM track_scrobbles LEFT JOIN users ON users.user_id = track_scrobbles.user_id WHERE track_scrobbles.user_id IN ({}) AND track_scrobbles.artist_id = {} AND track_scrobbles.track = '{}' GROUP BY users.username order by scrobbles DESC".format(users_list, artist['id'], sql_helper.esc_db(track['name']))
    result = sql_helper.execute_db(sql)
    total_scrobbles = sum([u['scrobbles'] for u in result])
    return {'artist': artist, 'track': track, 'users': result, 'total_scrobbles': total_scrobbles, 'total_users': len(users)}

def nowplaying(single_user=None):
    if not single_user:
        sql = "SELECT user_id, username FROM users;"
        users = sql_helper.execute_db(sql)
    else:
        logger.info("[User-triggered now playing update] {}".format(single_user))
        users = [{'username': single_user}]
    now_playing_users = []
    played_users = []
    for user in users:
        if single_user: # if update is user-triggered, no need to calculate next update (yet)
            sql = "UPDATE now_playing SET check_count = NULL WHERE username = '{}'".format(user['username'])
            sql_helper.execute_db(sql, commit=True)
        else:
            sql = "SELECT check_count,timestamp FROM now_playing WHERE username = '{}'".format(user['username'])
            result = sql_helper.execute_db(sql)
            if result:
                check_count = result[0]['check_count']
                timestamp = int(result[0]['timestamp'])
                if check_count == None: # calculate next nowplaying status
                    if timestamp != 0:
                        last_scrobbled_date = datetime.datetime.utcfromtimestamp(int(timestamp))
                        diff = datetime.datetime.utcnow() - last_scrobbled_date
                        hours = float(diff.days * 24 + diff.seconds / 3600)
                        new_count = 0

                        # these calculations are based on the assumption this task will be run every minute!
                        if hours <= 2:
                            pass # check nowplaying
                        elif hours <= 36:
                            new_count = round(math.log(hours) * math.log(hours))
                        else:
                            new_count = round(math.log(hours) * math.log(hours) * math.log(hours))
                        
                        if new_count:
                            logger.info("New now playing interval for {}: {}.".format(user['username'], new_count))
                            sql = "UPDATE now_playing SET check_count = {} WHERE username = '{}'".format(new_count, user['username'])
                            sql_helper.execute_db(sql, commit=True)
                            continue
                elif check_count == 0: # check nowplaying status
                    sql = "UPDATE now_playing SET check_count = NULL WHERE username = '{}'".format(user['username'])
                    sql_helper.execute_db(sql, commit=True)
                elif check_count > 0: # decrement interval and skip check
                    new_count = check_count - 1
                    sql = "UPDATE now_playing SET check_count = {} WHERE username = '{}'".format(new_count, user['username'])
                    sql_helper.execute_db(sql, commit=True)
                    continue
            else: # user does not have a nowplaying row in table, so check nowplaying status
                pass
        logger.info("Checking now playing status for {}.".format(user['username']))
        req_url = 'http://ws.audioscrobbler.com/2.0/?method=user.getrecenttracks&user={}&api_key={}&limit=1&format=json'.format(user['username'], cfg['api']['key'])
        try:
            req = requests.get(req_url).json()
            track = req['recenttracks']['track'][0]
        except IndexError:
            continue
        except (KeyError, requests.exceptions.RequestException) as e:
            logger.warn("Error getting most recently played track for {}: {}. Continuing...".format(user['username'], e))
            continue
        except Exception as e:
            logger.error("[FATAL] Error getting most recently played track for {}: {}".format(user['username'], e))
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

        # fix bug where Last.fm recenttracks endpoint returns a very old/incorrect nowplaying status (hard to reproduce)
        # check if the now playing timestamp is BEFORE the latest track fetched in the db (never should happen)
        if tmp_user['timestamp']:
            latest_track = sql_helper.execute_db("SELECT timestamp FROM track_scrobbles WHERE user_id = {} ORDER BY timestamp DESC LIMIT 1".format(user['user_id']))
            if len(latest_track):
                latest_timestamp = int(latest_track[0]['timestamp'])
                if tmp_user['timestamp'] < latest_timestamp:
                    logger.warn("Detected now playing timestamp earlier than latest timestamp in DB for {}. Skipping...")
                    logger.warn("Response from API: {}".format(track))
                    continue
        sql = sql_helper.replace_into("now_playing", tmp_user)
        sql_helper.execute_db(sql, commit=True, pass_on_error=True)
    return True

def get_nowplaying(join_code):
    sql = "SELECT now_playing.* FROM user_groups LEFT JOIN now_playing ON now_playing.username = user_groups.username WHERE user_groups.group_jc = '{}' AND now_playing.username IS NOT NULL ORDER BY IF(now_playing.timestamp = 0, 9999999999, now_playing.timestamp) DESC, user_groups.joined ASC".format(join_code)
    return sql_helper.execute_db(sql)

def play_history(wk_mode, artist_id, users, start_range, end_range, track=None, album_id=None, sort_by="track_scrobbles.timestamp", sort_order="DESC", limit=50, offset=0):
    users_list = ", ".join(str(u) for u in users)
    
    if start_range and end_range:
        date_sql = "AND from_unixtime(track_scrobbles.timestamp) BETWEEN '{}' AND '{}'".format(start_range, end_range)
    else:
        date_sql = ""

    if wk_mode == "track":
        sql = "SELECT users.user_id ,users.username, artists.name as artist, artists.url as artist_url, albums.url as album_url, track_scrobbles.track, albums.name as album, track_scrobbles.timestamp FROM `track_scrobbles` LEFT JOIN users ON users.user_id = track_scrobbles.user_id LEFT JOIN artists ON artists.id = track_scrobbles.artist_id LEFT JOIN albums ON albums.id = track_scrobbles.album_id WHERE track_scrobbles.user_id IN ({}) AND artists.id = {} AND track_scrobbles.track = '{}' {} ORDER BY {} {}, track_scrobbles.timestamp DESC LIMIT {} OFFSET {}".format(users_list, artist_id, sql_helper.esc_db(track), date_sql, sort_by, sort_order, limit, offset)
    elif wk_mode == "album":
        album_tracks_list = find_album_tracks(album_id)
        sql = "SELECT users.user_id ,users.username, artists.name as artist, artists.url as artist_url, albums.url as album_url, track_scrobbles.track, albums.name as album, track_scrobbles.timestamp FROM `track_scrobbles` LEFT JOIN users ON users.user_id = track_scrobbles.user_id LEFT JOIN artists ON artists.id = track_scrobbles.artist_id LEFT JOIN albums ON albums.id = track_scrobbles.album_id WHERE track_scrobbles.user_id IN ({}) AND artists.id = {} AND track_scrobbles.track IN ({}) {} ORDER BY {} {}, track_scrobbles.timestamp DESC LIMIT {} OFFSET {}".format(users_list, artist_id, album_tracks_list, date_sql, sort_by, sort_order, limit, offset)
    elif wk_mode == "artist":
        sql = "SELECT users.user_id ,users.username, artists.name as artist, artists.url as artist_url, albums.url as album_url, track_scrobbles.track, albums.name as album, track_scrobbles.timestamp FROM `track_scrobbles` LEFT JOIN users ON users.user_id = track_scrobbles.user_id LEFT JOIN artists ON artists.id = track_scrobbles.artist_id LEFT JOIN albums ON albums.id = track_scrobbles.album_id WHERE track_scrobbles.user_id IN ({}) AND artists.id = {} {} ORDER BY {} {}, track_scrobbles.timestamp DESC LIMIT {} OFFSET {}".format(users_list, artist_id, date_sql, sort_by, sort_order, limit, offset)
    elif wk_mode == "overall":
        sql = "SELECT users.user_id ,users.username, artists.name as artist, artists.url as artist_url, albums.url as album_url, track_scrobbles.track, albums.name as album, track_scrobbles.timestamp FROM `track_scrobbles` LEFT JOIN users ON users.user_id = track_scrobbles.user_id LEFT JOIN artists ON artists.id = track_scrobbles.artist_id LEFT JOIN albums ON albums.id = track_scrobbles.album_id WHERE track_scrobbles.user_id IN ({}) {} ORDER BY {} {}, track_scrobbles.timestamp DESC LIMIT {} OFFSET {}".format(users_list, date_sql, sort_by, sort_order, limit, offset)
    else:
        return False
    records = sql_helper.execute_db(sql, tz=True)
    if not records:
        return None
    total = sql_helper.execute_db("SELECT COUNT(*) as total FROM track_scrobbles")[0]['total']
    for r in records:
        r['track_url'] = r['artist_url'] + "/" + sql_helper.format_lastfm_string(r['album']) + "/" + sql_helper.format_lastfm_string(r['track'])
    data = {
        'records': records,
        'total': total,
        'limit': limit,
        'offset': offset
    }
    return data

def wk_top(wk_mode, users, artist_id, start_range, end_range, album_id=None, track_mode=False):
    users_list = ", ".join(str(u) for u in users)

    if start_range and end_range:
        range_sql = " AND from_unixtime(track_scrobbles.timestamp) BETWEEN '{}' AND '{}'".format(start_range, end_range)
    else:
        range_sql = ""

    if wk_mode == "artist" or wk_mode == "track":
        if track_mode:
            sql = "SELECT track_scrobbles.track, albums.name as album, albums.id as album_id, albums.url as album_url, albums.image_url, COUNT(*) as scrobbles FROM track_scrobbles LEFT JOIN artists on artists.id = track_scrobbles.artist_id LEFT JOIN albums on albums.id = track_scrobbles.album_id WHERE track_scrobbles.user_id IN ({}) AND track_scrobbles.artist_id = {}{} GROUP BY track_scrobbles.track ORDER BY scrobbles DESC".format(users_list, artist_id, range_sql)
        else:
            sql = "SELECT albums.name as album, albums.id as album_id, albums.url as album_url, albums.image_url, COUNT(*) as scrobbles FROM track_scrobbles LEFT JOIN artists on artists.id = track_scrobbles.artist_id LEFT JOIN albums on albums.id = track_scrobbles.album_id WHERE track_scrobbles.user_id IN ({}) AND track_scrobbles.artist_id = {}{} GROUP BY track_scrobbles.album_id ORDER BY scrobbles DESC".format(users_list, artist_id, range_sql)
    elif wk_mode == "album":
        album_tracks_list = find_album_tracks(album_id)
        sql = "SELECT albums.name as album, albums.id as album_id, track_scrobbles.track, albums.url as album_url, albums.image_url, COUNT(*) as scrobbles FROM track_scrobbles LEFT JOIN artists on artists.id = track_scrobbles.artist_id LEFT JOIN albums on albums.id = track_scrobbles.album_id WHERE track_scrobbles.user_id IN ({}) AND track_scrobbles.artist_id = {} AND track_scrobbles.track IN ({}){} GROUP BY track_scrobbles.track ORDER BY scrobbles DESC".format(users_list, artist_id, album_tracks_list, range_sql)
    records = sql_helper.execute_db(sql, tz=True)
    if not records:
        return None
    elif wk_mode == "album" or track_mode:
        for r in records:
            r['track_url'] = r['album_url'] + "/" + sql_helper.format_lastfm_string(r['track'])
    
    return records

def scrobble_leaderboard(users, start_range, end_range):
    users_list = ", ".join(str(u) for u in users)

    if not start_range or not end_range:
        sql = "SELECT users.username, users.profile_image, COUNT(*) as scrobbles FROM `track_scrobbles` LEFT JOIN users on users.user_id = track_scrobbles.user_id WHERE track_scrobbles.user_id IN ({}) GROUP BY track_scrobbles.user_id ORDER BY scrobbles DESC".format(users_list)
    else:
        sql = "SELECT users.username, users.profile_image, COUNT(*) as scrobbles FROM `track_scrobbles` LEFT JOIN users on users.user_id = track_scrobbles.user_id WHERE from_unixtime(track_scrobbles.timestamp) BETWEEN '{}' AND '{}' AND track_scrobbles.user_id IN ({}) GROUP BY track_scrobbles.user_id ORDER BY scrobbles DESC;".format(start_range, end_range, users_list)
    leaderboard = sql_helper.execute_db(sql, tz=True)
    total = sum([u['scrobbles'] for u in leaderboard])
    return {'leaderboard': leaderboard, 'start_range': start_range, 'end_range': end_range, 'total': total}

def wk_autocomplete(wk_mode, query):
    if len(query.strip()) < 2:
        return []

    sanitized_query = sql_helper.sanitize_query(query)
    partial_result = False

    if wk_mode == "artist":
        sql = "SELECT name from artists WHERE {} LIKE '%{}%' LIMIT 10".format(sql_helper.sanitize_db_field("name"), sanitized_query)
        artists = sql_helper.execute_db(sql)
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
                    albums = sql_helper.execute_db(sql)
                    suggestions = [valid_artist['name'] + " - " + a['name'] for a in albums]
                else: # track
                    if release_query:
                        sql = "SELECT DISTINCT track as name FROM track_scrobbles WHERE artist_id = {} AND {} LIKE '%{}%' LIMIT 10".format(valid_artist['id'], sql_helper.sanitize_db_field("track"), sql_helper.esc_db(release_query))
                    else:
                        sql = "SELECT track as name, COUNT(*) as scrobbles FROM track_scrobbles WHERE artist_id = {} GROUP BY track ORDER BY scrobbles DESC LIMIT 10".format(valid_artist['id'])
                    tracks = sql_helper.execute_db(sql)
                    suggestions = [valid_artist['name'] + " - " + t['name'] for t in tracks]
            else:
                suggestions = []
        else:
            sql = "SELECT name from artists WHERE {} LIKE '%{}%' LIMIT 10".format(sql_helper.sanitize_db_field("name"), sanitized_query)
            artists = sql_helper.execute_db(sql)
            suggestions = [r["name"] + " - " for r in artists]
            partial_result = True
    
    return {'suggestions': suggestions, 'partial_result': partial_result}

def check_artist_redirect(artist_string):
    artist_string = artist_string.strip()
    req_url = "http://ws.audioscrobbler.com/2.0/?method=artist.getcorrection&artist={}&api_key={}&format=json".format(artist_string, cfg['api']['key'])
    try:
        lastfm = requests.get(req_url).json()
        correction = lastfm['corrections']
    except (IndexError, KeyError, requests.exceptions.RequestException) as e:
        logger.error("Error checking for artist redirect for {}: {}.".format(artist_string, e))
        return None
    except Exception as e:
        logger.error("Another error occured checking for artist redirect for {}: {}.".format(artist_string, e))
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

            data = {'artist_name': sql_helper.esc_db(artist_string), 'redirected_name': sql_helper.esc_db(artist_name)}
            sql = sql_helper.insert_into_where_not_exists("artist_redirects", data, "artist_name")
            sql_helper.execute_db(sql, commit=True)
            return {'artist': artist_name}
    except (KeyError, TypeError) as e: # this probably means the artist doesn't even exist in Last.fm's db either
        return False

def charts(chart_mode, chart_type, users, start_range, end_range):
    if not users:
        return []
    entry_limit = 250
    user_charts = []
    group_chart = {}
    days_range = 365
    
    if chart_mode == "individual":
        users = [users[0]]
    if start_range and end_range:
        days_range = (dateutil.parser.parse(end_range) - dateutil.parser.parse(start_range)).days

    for user in users:
        if chart_type == "track":
            if not start_range or not end_range:
                sql = "SELECT artists.name as artist, artists.id as artist_id, artists.url as artist_url, artists.image_url as artist_image, track_scrobbles.track, albums.name as album, albums.image_url as image, COUNT(*) as scrobbles FROM `track_scrobbles` LEFT JOIN artists ON artists.id = track_scrobbles.artist_id LEFT JOIN albums ON albums.id = track_scrobbles.album_id WHERE track_scrobbles.user_id = {} GROUP BY artists.id, track_scrobbles.track ORDER BY scrobbles DESC LIMIT {}".format(user, entry_limit)
            else:
                sql = "SELECT artists.name as artist, artists.id as artist_id, artists.url as artist_url, artists.image_url as artist_image, track_scrobbles.track, albums.name as album, albums.image_url as image, COUNT(*) as scrobbles FROM `track_scrobbles` LEFT JOIN artists ON artists.id = track_scrobbles.artist_id LEFT JOIN albums ON albums.id = track_scrobbles.album_id WHERE track_scrobbles.user_id = {} AND from_unixtime(track_scrobbles.timestamp) BETWEEN '{}' AND '{}' GROUP BY artists.id, track_scrobbles.track ORDER BY scrobbles DESC LIMIT {}".format(user, start_range, end_range, entry_limit)
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
        result = sql_helper.execute_db(sql, tz=True)
        user_charts.append(result)
   
    if chart_mode == "individual":
        result = user_charts[0]
        for i, entry in enumerate(result):
            entry['position'] = i + 1
            if chart_type == "track":
                entry['url'] = entry['artist_url'] + "/_/" + sql_helper.format_lastfm_string(entry['track'])
        return result[:100]
    else: # group
        for chart in user_charts:
            for entry in chart:
                if chart_type == "track":
                    entry_key = str(entry['artist_id']) + "." + entry['track']
                    entry['url'] = entry['artist_url'] + "/_/" + sql_helper.format_lastfm_string(entry['track'])
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
        group_chart_condensed = sorted([v for k,v in group_chart.items()], key=itemgetter('score'), reverse=True)[:100]
        group_chart_final = []
        for i, entry in enumerate(group_chart_condensed):
            entry['position'] = i + 1
            group_chart_final.append(entry)
        return group_chart_final

def listening_trends(join_code, cmd_mode, wk_options, start_range, end_range):
    # get list of users in group
    group = group_helper.get_group(join_code, short=False)
    
    scrobbles = []
    days_range = -1

    if start_range and end_range:
        days_range = (dateutil.parser.parse(end_range) - dateutil.parser.parse(start_range)).days

    if cmd_mode == "wk":
        album_sql = " AND track IN ({}) ".format(find_album_tracks(wk_options['album_id'])) if wk_options['wk_mode'] == "album" else " "
        track_sql = " AND track = '{}' ".format(sql_helper.esc_db(wk_options['track'])) if wk_options['wk_mode'] == "track" else " "
        
        for u in group['users']:
            if start_range and end_range:
                sql = "SELECT track,timestamp FROM `track_scrobbles` WHERE user_id = {} AND from_unixtime(track_scrobbles.timestamp) BETWEEN '{}' AND '{}' AND artist_id = {}{}{}ORDER BY timestamp ASC".format(u['user_id'], start_range, end_range, wk_options['artist_id'], album_sql, track_sql)
            else:
                sql = "SELECT track,timestamp FROM `track_scrobbles` WHERE user_id = {} AND artist_id = {}{}{}ORDER BY timestamp ASC".format(u['user_id'], wk_options['artist_id'], album_sql, track_sql)
            result = [r['timestamp'] for r in sql_helper.execute_db(sql, tz=True)]
            if result:
                scrobbles.append({u['username']: result})
    elif cmd_mode == "user-track": # timeline of different track's scrobbles
        album_sql = " AND track IN ({}) ".format(find_album_tracks(wk_options['album_id'])) if wk_options['wk_mode'] == "album" else " "

        # get tracks to find timestamps for (limit 20)
        if start_range and end_range:
            sql = "SELECT track FROM `track_scrobbles` WHERE user_id = {} AND from_unixtime(track_scrobbles.timestamp) BETWEEN '{}' AND '{}' AND artist_id = {}{}GROUP BY track ORDER BY COUNT(*) DESC LIMIT 20".format(wk_options['user_id'], start_range, end_range, wk_options['artist_id'], album_sql)
        else:
            sql = "SELECT track FROM `track_scrobbles` WHERE user_id = {} AND artist_id = {}{}GROUP BY track ORDER BY COUNT(*) DESC LIMIT 20".format(wk_options['user_id'], wk_options['artist_id'], album_sql)    
        selected_tracks = [t['track'] for t in sql_helper.execute_db(sql, tz=True)]
        for track in selected_tracks:
            if start_range and end_range:
                sql = "SELECT track,timestamp FROM `track_scrobbles` WHERE user_id = {} AND from_unixtime(track_scrobbles.timestamp) BETWEEN '{}' AND '{}' AND track_scrobbles.artist_id = {} AND track = '{}' ORDER BY timestamp ASC".format(wk_options['user_id'], start_range, end_range, wk_options['artist_id'], sql_helper.esc_db(track))
            else:
                sql = "SELECT track,timestamp FROM `track_scrobbles` WHERE user_id = {} AND track_scrobbles.artist_id = {} AND track = '{}' ORDER BY timestamp ASC".format(wk_options['user_id'], wk_options['artist_id'], sql_helper.esc_db(track))
            result = [r['timestamp'] for r in sql_helper.execute_db(sql, tz=True)]
            if result:
                scrobbles.append({track: result})
    elif cmd_mode == "user-album":
        # get albums to find timestamps for (limit 10)
        if start_range and end_range:
            sql = "SELECT track_scrobbles.album_id,albums.name FROM track_scrobbles LEFT JOIN albums on track_scrobbles.album_id = albums.id WHERE track_scrobbles.user_id = {} AND track_scrobbles.artist_id = {} AND albums.name != '' AND from_unixtime(track_scrobbles.timestamp) BETWEEN '{}' AND '{}' GROUP BY track_scrobbles.album_id ORDER BY COUNT(*) DESC LIMIT 10".format(wk_options['user_id'], wk_options['artist_id'], start_range, end_range)
        else:
            sql = "SELECT track_scrobbles.album_id,albums.name FROM track_scrobbles LEFT JOIN albums on track_scrobbles.album_id = albums.id WHERE track_scrobbles.user_id = {} AND track_scrobbles.artist_id = {} AND albums.name != '' GROUP BY track_scrobbles.album_id ORDER BY COUNT(*) DESC LIMIT 10".format(wk_options['user_id'], wk_options['artist_id'])
        selected_albums = sql_helper.execute_db(sql, tz=True)
        for record in selected_albums:
            if start_range and end_range:
                sql = "SELECT albums.name,track_scrobbles.timestamp FROM track_scrobbles LEFT JOIN albums on track_scrobbles.album_id = albums.id WHERE track_scrobbles.user_id = {} AND track_scrobbles.artist_id = {} AND track_scrobbles.track IN ({}) AND from_unixtime(track_scrobbles.timestamp) BETWEEN '{}' AND '{}' ORDER BY track_scrobbles.timestamp ASC".format(wk_options['user_id'], wk_options['artist_id'], find_album_tracks(record['album_id']), start_range, end_range)
            else:
                sql = "SELECT albums.name,track_scrobbles.timestamp FROM track_scrobbles LEFT JOIN albums on track_scrobbles.album_id = albums.id WHERE track_scrobbles.user_id = {} AND track_scrobbles.artist_id = {} AND track_scrobbles.track IN ({}) ORDER BY track_scrobbles.timestamp ASC".format(wk_options['user_id'], wk_options['artist_id'], find_album_tracks(record['album_id']))
            result = sql_helper.execute_db(sql, tz=True)
            album_scrobbles = [r['timestamp'] for r in result]
            if album_scrobbles:
                scrobbles.append({record['name']: album_scrobbles})
    elif "leaderboard" in cmd_mode:
        if days_range == -1 or days_range > 365:
            days_increment = 30
        elif days_range < 3:
            days_increment = 1/24
        elif days_range <= 7:
            days_increment = 1
        elif days_range < 180:
            days_increment = 1
        elif days_range <= 365:
            days_increment = 7
        
        if days_range == -1:
            users_list = ", ".join(str(u['user_id']) for u in group['users'])
            sql = "SELECT timestamp from track_scrobbles WHERE user_id IN ({}) ORDER BY timestamp ASC LIMIT 1".format(users_list)
            result = sql_helper.execute_db(sql, tz=True)
            start = datetime.datetime.utcfromtimestamp(int(result[0]['timestamp']))
            end = datetime.datetime.utcnow()
            days_range = (end - start).days
        else:
            start = dateutil.parser.parse(start_range).replace(tzinfo=None)
            end = dateutil.parser.parse(end_range).replace(tzinfo=None)

        for u in group['users']:
            days_tmp = 0
            registered_datetime = datetime.datetime.utcfromtimestamp(int(u['registered']))
            scrbl_tmp = []
            scrbl_count = 0
            while days_tmp < days_range/days_increment: # make discrete data points for each day
                start_tmp = (start + datetime.timedelta(days=days_tmp*days_increment))
                end_tmp = (start + datetime.timedelta(days=(days_tmp*days_increment)+days_increment))
                if end_tmp < registered_datetime: # don't query db if time range is before registered date
                    scrbl_tmp.append({ int(start_tmp.timestamp()): 0 })
                else:
                    sql = "SELECT COUNT(*) as total FROM `track_scrobbles` WHERE user_id = {} AND from_unixtime(track_scrobbles.timestamp) BETWEEN '{}' AND '{}'".format(u['user_id'], start_tmp.strftime("%Y-%m-%dT%H:%M:%SZ"), end_tmp.strftime("%Y-%m-%dT%H:%M:%SZ"))
                    res = sql_helper.execute_db(sql, tz=True)
                    if cmd_mode == "leaderboard-cu": # cumulative mode
                        scrbl_count += int(res[0]['total'])
                    else: # non-cumulative mode
                        scrbl_count = int(res[0]['total'])
                    scrbl_tmp.append({ int(start_tmp.timestamp()): scrbl_count })
                days_tmp += 1
            if cmd_mode == "leaderboard-cu":
                if scrbl_count > 0:
                    scrobbles.append({ u['username']: scrbl_tmp})
            else:
                scrobbles.append({ u['username']: scrbl_tmp})

    return scrobbles

def quick_wk_charts(users, artist_id, album_id, track, start_range, end_range):
    if start_range and end_range:
        range_sql = " AND from_unixtime(track_scrobbles.timestamp) BETWEEN '{}' AND '{}'".format(start_range, end_range)
    else:
        range_sql = ""
    album_sql = " AND album_id = {}".format(album_id) if album_id else ""
    track_sql = " AND UPPER({}) = UPPER('{}')".format(sql_helper.sanitize_db_field("track"), sql_helper.esc_db(track)) if track else ""
    wk_field = "track" if track else ("album_id" if album_id else "artist_id")
    wk_value = track if track else (album_id if album_id else artist_id)
    sql_groupby = "artist_id, track" if track else ("album_id" if album_id else "artist_id")

    records = []
    for u in users:
        sql = "SELECT {}, artist_id as artist, COUNT(*) as scrobbles FROM track_scrobbles WHERE user_id = {}{} GROUP BY {} ORDER BY scrobbles DESC LIMIT 10".format(wk_field, u, range_sql, sql_groupby)
        result = sql_helper.execute_db(sql, tz=True)
        result = [entry | {'rank': i+1} for i, entry, in enumerate(result)]
        filtered_list = list(filter(lambda x: str(x[wk_field]).lower() == str(wk_value).lower() and x['artist'] == artist_id, result))
        if filtered_list:
            tmp = { 'id': u, 'rank': filtered_list[0]['rank'] }
            records.append(tmp)
    return records

def genre_top_artists(genre_id):
    return sql_helper.execute_db("SELECT artists.* FROM artists LEFT JOIN artist_genres ON artists.id = artist_genres.artist_id WHERE artist_genres.genre_id = {} ORDER BY artists.playcount DESC LIMIT 250".format(genre_id))