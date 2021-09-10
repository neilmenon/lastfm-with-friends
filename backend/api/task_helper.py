import random
import mariadb
import datetime
from . import config
from . import sql_helper
from . import api_logger as logger
cfg = config.config

def remove_unused_artists_albums():
    # use case: user removed scrobbles from app or edited scrobbles (Last.fm Pro users)
    mdb = mariadb.connect(**(cfg['sql']))
    cursor = mdb.cursor(dictionary=True)

    deleted_artists = []
    deleted_albums = []

    # handle albums first due to foreign key relationship
    sql = "SELECT id,artist_name,name from albums WHERE NOT EXISTS (SELECT track_scrobbles.album_id FROM track_scrobbles WHERE track_scrobbles.album_id = albums.id)"
    cursor.execute(sql)
    deleted_albums = list(cursor)
    for album in deleted_albums:
        logger.log("Deleting unused album: {} - {} (ID: {})".format(album['artist_name'], album['name'], album['id']))
    sql = "DELETE FROM albums WHERE NOT EXISTS (SELECT track_scrobbles.album_id FROM track_scrobbles WHERE track_scrobbles.album_id = albums.id)"
    cursor.execute(sql)
    mdb.commit()

    # artists
    sql = "SELECT name,id from artists WHERE NOT EXISTS (SELECT track_scrobbles.artist_id FROM track_scrobbles WHERE track_scrobbles.artist_id = artists.id)"
    cursor.execute(sql)
    deleted_artists = list(cursor)
    for artist in deleted_artists:
        logger.log("Deleting unused artist: {} (ID: {})".format(artist['name'], artist['id']))
    sql = "DELETE FROM artists WHERE NOT EXISTS (SELECT track_scrobbles.artist_id FROM track_scrobbles WHERE track_scrobbles.artist_id = artists.id)"
    cursor.execute(sql)
    mdb.commit()

    mdb.close()

    if not deleted_albums and not deleted_artists:
        logger.log("========== No unused artists or albums to delete! ==========")
    else:
        logger.log("========== Deleted {} artist(s) and {} album(s). ==========".format(len(deleted_artists), len(deleted_albums)))

def app_stats(db_store):
    mdb = mariadb.connect(**(cfg['sql']))
    cursor = mdb.cursor(dictionary=True)

    stats = {}
    if db_store:
        cursor.execute("SELECT COUNT(*) as artists FROM artists")
        stats['artists'] = list(cursor)[0]['artists']
        cursor.execute("SELECT COUNT(*) as albums FROM albums")
        stats['albums'] = list(cursor)[0]['albums']
        cursor.execute("SELECT COUNT(*) as tracks FROM (SELECT DISTINCT track FROM track_scrobbles GROUP BY track) as dt")
        stats['tracks'] = list(cursor)[0]['tracks']
        cursor.execute("SELECT COUNT(*) as scrobbles FROM track_scrobbles")
        stats['scrobbles'] = list(cursor)[0]['scrobbles']
        cursor.execute("SELECT COUNT(*) as users FROM users")
        stats['users'] = list(cursor)[0]['users']
        cursor.execute("SELECT COUNT(*) as groups FROM groups")
        stats['groups'] = list(cursor)[0]['groups']
        stats['date'] = str(datetime.datetime.utcnow())

        sql = sql_helper.insert_into("stats", stats)
        cursor.execute(sql)
        mdb.commit()
    else:
        sql = "SELECT * FROM stats ORDER BY date DESC LIMIT 1"
        cursor.execute(sql)
        stats = list(cursor)[0]

    mdb.close()
    return stats

def insert_demo_scrobbles(demo_users):
    mdb = mariadb.connect(**(cfg['sql']))
    cursor = mdb.cursor(dictionary=True)

    logger.log("====== INSERTING DEMO SCROBBLES ======")
    for user in demo_users:
        logger.log("Scrobbling for demo user {}.".format(user))
        
        # get session key of demo user
        cursor.execute("SELECT session_key FROM sessions where username = '{}'".format(user))
        result = list(cursor)
        if result:
            session_key = result[0]['session_key']
        else:
            logger.log("\t SKIPPED. No session key found in the database for this demo user.")
            continue
        
        # find some random tracks to scrobble
        random_num_tracks = random.randint(5, 50)
        sql = "SELECT artists.name AS artist_name, track_scrobbles.track, albums.name as album_name FROM `track_scrobbles` LEFT JOIN artists ON track_scrobbles.artist_id = artists.id LEFT JOIN albums ON track_scrobbles.album_id = albums.id WHERE albums.name <> '' ORDER BY RAND() LIMIT {}".format(random_num_tracks)
        cursor.execute(sql)
        tracks_to_scrobble = list(cursor)
        logger.log("\t Scrobbling {} random tracks...".format(random_num_tracks))

        # scrobble the tracks...

    mdb.close()
    return True