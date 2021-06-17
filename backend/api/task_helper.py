import mariadb
from . import config
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

def app_stats():
    mdb = mariadb.connect(**(cfg['sql']))
    cursor = mdb.cursor(dictionary=True)

    stats = {}
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

    mdb.close()
    return stats