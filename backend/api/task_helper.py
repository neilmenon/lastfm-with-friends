import random
import requests
import datetime
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
