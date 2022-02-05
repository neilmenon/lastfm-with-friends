import random
import requests
import datetime
from flask import current_app

from . import group_helper
from . import user_helper
from . import config
from . import sql_helper
from . import auth_helper
from . import api_logger as logger
cfg = config.config

def remove_unused_artists_albums():
    # use case: user removed scrobbles from app or edited scrobbles (Last.fm Pro users)

    deleted_artists = []
    deleted_albums = []

    # handle albums first due to foreign key relationship
    sql = "SELECT id,artist_name,name from albums WHERE NOT EXISTS (SELECT track_scrobbles.album_id FROM track_scrobbles WHERE track_scrobbles.album_id = albums.id)"
    deleted_albums = sql_helper.execute_db(sql)
    for album in deleted_albums:
        logger.info("Deleting unused album: {} - {} (ID: {})".format(album['artist_name'], album['name'], album['id']))
    sql = "DELETE FROM albums WHERE NOT EXISTS (SELECT track_scrobbles.album_id FROM track_scrobbles WHERE track_scrobbles.album_id = albums.id)"
    sql_helper.execute_db(sql, commit=True)

    # artists
    sql = "SELECT name,id from artists WHERE NOT EXISTS (SELECT track_scrobbles.artist_id FROM track_scrobbles WHERE track_scrobbles.artist_id = artists.id)"
    deleted_artists = sql_helper.execute_db(sql)
    for artist in deleted_artists:
        logger.info("Deleting unused artist: {} (ID: {})".format(artist['name'], artist['id']))
    sql = "DELETE FROM artists WHERE NOT EXISTS (SELECT track_scrobbles.artist_id FROM track_scrobbles WHERE track_scrobbles.artist_id = artists.id)"
    sql_helper.execute_db(sql, commit=True)

    if not deleted_albums and not deleted_artists:
        logger.info("========== No unused artists or albums to delete! ==========")
    else:
        logger.info("========== Deleted {} artist(s) and {} album(s). ==========".format(len(deleted_artists), len(deleted_albums)))

def app_stats(db_store):
    stats = {}
    if db_store:
        result = sql_helper.execute_db("SELECT COUNT(*) as artists FROM artists")
        stats['artists'] = result[0]['artists']
        result = sql_helper.execute_db("SELECT COUNT(*) as albums FROM albums")
        stats['albums'] = result[0]['albums']
        result = sql_helper.execute_db("SELECT COUNT(*) as tracks FROM (SELECT DISTINCT track FROM track_scrobbles GROUP BY track) as dt")
        stats['tracks'] = result[0]['tracks']
        result = sql_helper.execute_db("SELECT COUNT(*) as scrobbles FROM track_scrobbles")
        stats['scrobbles'] = result[0]['scrobbles']
        result = sql_helper.execute_db("SELECT COUNT(*) as users FROM users")
        stats['users'] = result[0]['users']
        result = sql_helper.execute_db("SELECT COUNT(*) as groups FROM groups")
        stats['groups'] = result[0]['groups']
        result = sql_helper.execute_db("SELECT COUNT(*) as genres FROM genres")
        stats['genres'] = result[0]['genres']
        stats['date'] = str(datetime.datetime.utcnow())

        sql = sql_helper.insert_into("stats", stats)
        sql_helper.execute_db(sql, commit=True)
    else:
        sql = "SELECT * FROM stats ORDER BY date DESC LIMIT 1"
        result = sql_helper.execute_db(sql)
        stats = result[0]

    return stats

def insert_demo_scrobbles(demo_users):

    logger.info("====== INSERTING DEMO SCROBBLES ======")
    for user in demo_users:
        logger.info("Scrobbling for demo user {}.".format(user))
        
        # get session key of demo user
        result = sql_helper.execute_db("SELECT session_key FROM sessions where username = '{}'".format(user))
        if result:
            session_key = result[0]['session_key']
        else:
            logger.warn("\t SKIPPED scrobbling for {}. No session key found in the database for this demo user.".format(user))
            continue
        
        # find some random tracks to scrobble
        random_num_tracks = random.randint(2, 10)
        sql = "SELECT artists.name AS artist_name, track_scrobbles.track, albums.name as album_name FROM `track_scrobbles` LEFT JOIN artists ON track_scrobbles.artist_id = artists.id LEFT JOIN albums ON track_scrobbles.album_id = albums.id WHERE albums.name <> '' ORDER BY RAND() LIMIT {}".format(random_num_tracks)
        result = sql_helper.execute_db(sql)
        tracks_to_scrobble = result
        logger.info("\t Scrobbling {} random tracks...".format(random_num_tracks))

        # scrobble the tracks
        for index, entry in enumerate(tracks_to_scrobble):
            data = {}
            data['api_key'] = cfg['api']['key']
            data['sk'] = session_key
            data['method'] = 'track.scrobble'
            data['artist'] = entry['artist_name']
            data['track'] = entry['track']
            data['album'] = entry['album_name']
            # random timestamp in the past hour
            data['timestamp'] = str(int(datetime.datetime.now(tz=datetime.timezone.utc).timestamp()) - random.randint(1, 1*60*60))
            signed_data = auth_helper.get_signed_object(data)
            try:
                logger.info("\t [{}/{}] Scrobbling {} - {}".format(index+1, len(tracks_to_scrobble), data['artist'], data['track']))
                scrobble_req = requests.post("https://ws.audioscrobbler.com/2.0", data=signed_data).json()
                t = scrobble_req['scrobbles']
            except Exception as e:
                logger.error("\t\t Error scrobbling this track: {}".format(scrobble_req))
            
    return True

def task_handler(task_name, task_operation):
    task = sql_helper.execute_db("SELECT * FROM tasks WHERE name = '{}'".format(task_name))
    if not len(task): # entry for this task does not exist in DB, create row
        sql_helper.execute_db("INSERT INTO tasks (name) VALUES ('{}')".format(task_name), commit=True)
        task = sql_helper.execute_db("SELECT * FROM tasks WHERE name = '{}'".format(task_name))[0]
    else:
        task = task[0]

    if task_operation == "start":
        if not task['last_finished']: # task is currently running somewhere else!
            logger.warn("[task_handler] [{}] [skips: {}] This task is currently running somewhere else. Skipping current run.".format(task_name, task['skips']))
            # increment skips counter on task
            sql_helper.execute_db("UPDATE tasks SET skips = {} WHERE name = '{}'".format(task['skips'] + 1, task_name), commit=True)
            return False
        else: # task is not currently running, clear last_finished and proceed
            sql_helper.execute_db("UPDATE tasks SET last_finished = NULL WHERE name = '{}'".format(task_name), commit=True)
            return True
    elif task_operation == "end":
        # set last_finished to current timestamp, clear skips
        sql_helper.execute_db("UPDATE tasks SET last_finished = '{}', skips = 0 WHERE name = '{}'".format(str(datetime.datetime.utcnow()), task_name), commit=True)
        return True
    else:
        logger.error("[task_handler] [{}] [skips: {}] Invalid task operation '{}'. This task will not run.".format(task_name, task['skips'], task_operation))
        return False

# gets series of personal stats for a given user (used on app homepage)
def personal_stats(username, genre_filter_list):
    logger.info("Generating personal stats for {}".format(username))
    # get user details
    u = sql_helper.execute_db("SELECT user_id, username, scrobbles FROM users WHERE username = '{}'".format(username))[0]

    min_scrobbles = 250

    if u['scrobbles'] < min_scrobbles: # not enough data
        logger.info("\tNot enough scrobble data to generate stats. Skipping... (scrobbles: {})".format(u['scrobbles']))
        return
    
    stats = {}
    stats['username'] = username

    # define datetime time periods
    now = datetime.datetime.utcnow()
    beginning_of_time = datetime.datetime.fromtimestamp(0)
    calc_days_ago = None
    calc_time_days = None
    
    # determine how precise we want to stats to be based on how much the user scrobbles
    # need at least 300 scrobbles for stats to be revelant enough to run calculations
    # find first time period that satisfies this
    time_periods = [7, 14, 30, 60, 90, 180, 365, 9999] # 9999 is 'all time'
    for t in time_periods:
        calc_days_ago = now - datetime.timedelta(days=t)
        calc_time_days = t
        scrobbles = sql_helper.execute_db("SELECT COUNT(*) as scrobbles FROM `track_scrobbles` WHERE from_unixtime(track_scrobbles.timestamp) BETWEEN '{}' AND '{}' AND track_scrobbles.user_id = {} GROUP BY track_scrobbles.user_id ORDER BY scrobbles DESC".format(calc_days_ago, now, u['user_id']))
        if len(scrobbles):
            scrobbles = scrobbles[0]['scrobbles']
        else:
            continue
        if scrobbles >= min_scrobbles:
            logger.info("\tGenerating stats with time period of {} days (scrobbles: {})".format(t, scrobbles))
            break
    stats['time_period_days'] = calc_time_days
    
    # can't get enough of
    sql = "SELECT artists.name as artist, artists.url as artist_url, artists.image_url as artist_image, track_scrobbles.track, albums.name as album, albums.image_url as image, COUNT(*) as scrobbles FROM `track_scrobbles` LEFT JOIN artists ON artists.id = track_scrobbles.artist_id LEFT JOIN albums ON albums.id = track_scrobbles.album_id WHERE track_scrobbles.user_id = {} AND from_unixtime(track_scrobbles.timestamp) BETWEEN '{}' AND '{}' GROUP BY track_scrobbles.artist_id, track_scrobbles.track ORDER BY scrobbles DESC LIMIT 10".format(u['user_id'], calc_days_ago, now)
    tracks = list(filter(lambda x: x['scrobbles'] >= 5, sql_helper.execute_db(sql)))

    if len(tracks):
        len_tracks = 3 if len(tracks) >= 3 else len(tracks)
        stats['cant_get_enough'] = sql_helper.escape_keys_in_dict(random.choice(tracks[:len_tracks]))

    # top genre
    sql = "SELECT genres.name, COUNT(*) as genre_count, CAST(SUM(scrobbles) as int) as sum_scrobbles FROM genres LEFT JOIN artist_genres ON genres.id = artist_genres.genre_id INNER JOIN (SELECT track_scrobbles.artist_id, COUNT(*) as scrobbles FROM `track_scrobbles` WHERE track_scrobbles.user_id = {} AND from_unixtime(track_scrobbles.timestamp) BETWEEN '{}' AND '{}' GROUP BY track_scrobbles.artist_id ORDER BY scrobbles DESC) as top ON artist_genres.artist_id = top.artist_id WHERE genres.id NOT IN ({}) GROUP BY genres.name ORDER BY sum_scrobbles DESC LIMIT 1".format(u['user_id'], calc_days_ago, now, genre_filter_list)
    top_genre = sql_helper.execute_db(sql)[0]
    stats['top_genre'] = sql_helper.escape_keys_in_dict(top_genre)

    # most active hour
    sql = "SELECT EXTRACT(HOUR FROM from_unixtime(track_scrobbles.timestamp)) as hour, COUNT(*) as total FROM track_scrobbles WHERE user_id = {} AND from_unixtime(track_scrobbles.timestamp) BETWEEN '{}' AND '{}' GROUP BY hour ORDER BY total DESC LIMIT 1".format(u['user_id'], calc_days_ago, now)
    most_active_hour = sql_helper.execute_db(sql, tz=True)[0]['hour']

    stats['most_active_hour'] = most_active_hour

    # scrobbles increase/decrease % from previous period
    previous_period_start = calc_days_ago - datetime.timedelta(days=calc_time_days)

    sql = "SELECT COUNT(*) as scrobbles FROM track_scrobbles WHERE from_unixtime(track_scrobbles.timestamp) BETWEEN '{}' AND '{}' AND track_scrobbles.user_id = {}".format(previous_period_start, calc_days_ago, u['user_id'])
    previous_period_scrobbles = sql_helper.execute_db(sql)[0]['scrobbles']
    sql = "SELECT COUNT(*) as scrobbles FROM track_scrobbles WHERE from_unixtime(track_scrobbles.timestamp) BETWEEN '{}' AND '{}' AND track_scrobbles.user_id = {}".format(calc_days_ago, now, u['user_id'])
    current_period_scrobbles = sql_helper.execute_db(sql)[0]['scrobbles']

    percentage_increase = round(((current_period_scrobbles - previous_period_scrobbles)/previous_period_scrobbles) * 100, 1)
    stats['scrobble_compare'] = {
        "current": current_period_scrobbles,
        "previous": previous_period_scrobbles,
        "percent": percentage_increase
    }

    # top rising artist
    # get top artists for this time period
    sql = "SELECT artists.name as artist, artists.id as artist_id, COUNT(*) as scrobbles FROM `track_scrobbles` LEFT JOIN artists ON artists.id = track_scrobbles.artist_id WHERE track_scrobbles.user_id = {} AND from_unixtime(track_scrobbles.timestamp) BETWEEN '{}' AND '{}' GROUP BY track_scrobbles.artist_id HAVING scrobbles >= 10 ORDER BY scrobbles DESC LIMIT 15".format(u['user_id'], calc_days_ago, now)
    top_artists = sql_helper.execute_db(sql)
    
    if not len(top_artists):
        stats['top_rising'] = []
    else:
        top_artists_ids_list = ",".join([str(a['artist_id']) for a in top_artists])

        # get scrobble count from the start until now for the above artists
        sql = "SELECT artists.name as artist, artists.id as artist_id, COUNT(*) as scrobbles FROM `track_scrobbles` LEFT JOIN artists ON artists.id = track_scrobbles.artist_id WHERE track_scrobbles.user_id = {} AND from_unixtime(track_scrobbles.timestamp) BETWEEN '{}' AND '{}' AND artists.id IN ({}) GROUP BY track_scrobbles.artist_id HAVING scrobbles ORDER BY scrobbles DESC LIMIT 15".format(u['user_id'], beginning_of_time, now, top_artists_ids_list)
        current_count = sql_helper.execute_db(sql)

        # get scrobble count from the start until X days ago
        sql = "SELECT artists.name as artist, artists.id as artist_id, COUNT(*) as scrobbles FROM `track_scrobbles` LEFT JOIN artists ON artists.id = track_scrobbles.artist_id WHERE track_scrobbles.user_id = {} AND from_unixtime(track_scrobbles.timestamp) BETWEEN '{}' AND '{}' AND artists.id IN ({}) GROUP BY track_scrobbles.artist_id ORDER BY scrobbles DESC".format(u['user_id'], beginning_of_time, calc_days_ago, top_artists_ids_list)
        previous_count = sql_helper.execute_db(sql)

        unsorted_top_rising = []
        for a in current_count:
            previous_record = list(filter(lambda x: x['artist_id'] == a['artist_id'], previous_count))
            if not len(previous_record):
                continue
            else:
                previous_record = previous_record[0]

            a['prev_scrobbles'] = previous_record['scrobbles']
            a['percent'] = round(((a['scrobbles'] - previous_record['scrobbles'])/previous_record['scrobbles']) * 100, 1)
            unsorted_top_rising.append(a)

        stats['top_rising'] = [sql_helper.escape_keys_in_dict(t) for t in sorted(unsorted_top_rising, key = lambda i: i['percent'], reverse=True)]
    
    stats['date_generated'] = datetime.datetime.utcnow()

    return stats

def get_popular_genre_filter_list(limit):
    return ",".join([str(g['id']) for g in sql_helper.execute_db("SELECT genres.id FROM artist_genres LEFT JOIN genres ON genres.id = artist_genres.genre_id GROUP BY genres.id ORDER BY COUNT(*) DESC LIMIT {}".format(limit))])

def prune_inactive_users(dry_run=True):
    logger.info("===> Running prune users task")
    for u in user_helper.get_users():
        user = user_helper.get_user(u['username'], extended=True)

        prune_user = False
        if len(user['groups']) > 0:
            # check if user is only one in group(s)
            is_solo_in_group = True
            latest_create_date = None
            for g in user['groups']:
                if len(g['members']) > 1:
                    is_solo_in_group = False
                    break
                else:
                    create_date = g['created']
                    if latest_create_date is not None:
                        if create_date > latest_create_date:
                            latest_create_date = create_date
                    else:
                        latest_create_date = create_date
            if is_solo_in_group:
                # check if create date is > 7 days
                if ((datetime.datetime.utcnow() - latest_create_date) >= datetime.timedelta(days=7)) and ((datetime.datetime.utcnow() - user['joined_date']) >= datetime.timedelta(days=7)):
                    prune_user = True
        else:
            if ((datetime.datetime.utcnow() - user['joined_date']) >= datetime.timedelta(days=7)):
                prune_user = True

        if prune_user:
            logger.warn("{}Pruning user {} due to inactivity! {} group(s) with no users besides creator will be deleted.".format("[DRY RUN] " if dry_run else "", user['username'], len(user['groups'])))
            if not dry_run:
                for g in user['groups']:
                    logger.warn("\tDeleting group {}...".format(g['name']))
                    group_helper.delete_group(g['join_code'])
                user_helper.delete_user(user['user_id'], user['username'], current_app._get_current_object())
        