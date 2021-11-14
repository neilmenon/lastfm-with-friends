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
        logger.log("Deleting unused album: {} - {} (ID: {})".format(album['artist_name'], album['name'], album['id']))
    sql = "DELETE FROM albums WHERE NOT EXISTS (SELECT track_scrobbles.album_id FROM track_scrobbles WHERE track_scrobbles.album_id = albums.id)"
    sql_helper.execute_db(sql, commit=True)

    # artists
    sql = "SELECT name,id from artists WHERE NOT EXISTS (SELECT track_scrobbles.artist_id FROM track_scrobbles WHERE track_scrobbles.artist_id = artists.id)"
    deleted_artists = sql_helper.execute_db(sql)
    for artist in deleted_artists:
        logger.log("Deleting unused artist: {} (ID: {})".format(artist['name'], artist['id']))
    sql = "DELETE FROM artists WHERE NOT EXISTS (SELECT track_scrobbles.artist_id FROM track_scrobbles WHERE track_scrobbles.artist_id = artists.id)"
    sql_helper.execute_db(sql, commit=True)

    if not deleted_albums and not deleted_artists:
        logger.log("========== No unused artists or albums to delete! ==========")
    else:
        logger.log("========== Deleted {} artist(s) and {} album(s). ==========".format(len(deleted_artists), len(deleted_albums)))

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
        stats['date'] = str(datetime.datetime.utcnow())

        sql = sql_helper.insert_into("stats", stats)
        sql_helper.execute_db(sql, commit=True)
    else:
        sql = "SELECT * FROM stats ORDER BY date DESC LIMIT 1"
        result = sql_helper.execute_db(sql)
        stats = result[0]

    return stats

def insert_demo_scrobbles(demo_users):

    logger.log("====== INSERTING DEMO SCROBBLES ======")
    for user in demo_users:
        logger.log("Scrobbling for demo user {}.".format(user))
        
        # get session key of demo user
        result = sql_helper.execute_db("SELECT session_key FROM sessions where username = '{}'".format(user))
        if result:
            session_key = result[0]['session_key']
        else:
            logger.log("\t SKIPPED. No session key found in the database for this demo user.")
            continue
        
        # find some random tracks to scrobble
        random_num_tracks = random.randint(2, 10)
        sql = "SELECT artists.name AS artist_name, track_scrobbles.track, albums.name as album_name FROM `track_scrobbles` LEFT JOIN artists ON track_scrobbles.artist_id = artists.id LEFT JOIN albums ON track_scrobbles.album_id = albums.id WHERE albums.name <> '' ORDER BY RAND() LIMIT {}".format(random_num_tracks)
        result = sql_helper.execute_db(sql)
        tracks_to_scrobble = result
        logger.log("\t Scrobbling {} random tracks...".format(random_num_tracks))

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
                logger.log("\t [{}/{}] Scrobbling {} - {}".format(index+1, len(tracks_to_scrobble), data['artist'], data['track']))
                scrobble_req = requests.post("https://ws.audioscrobbler.com/2.0", data=signed_data).json()
                t = scrobble_req['scrobbles']
            except Exception as e:
                logger.log("\t\t Error scrobbling this track: {}".format(scrobble_req))
            
    return True