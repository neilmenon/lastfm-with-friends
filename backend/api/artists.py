import sys
import json
import requests
import mariadb
import datetime
from . import config
from . import sql_helper
from . import auth_helper
from . import user_helper
from . import api_logger as logger
cfg = config.config

def scrape_artist_data():
    mdb = mariadb.connect(**(cfg['sql']))
    cursor = mdb.cursor(dictionary=True)
    users = user_helper.get_users()
    if not users:
        logger.log("No users to scrape artists from!")
        return False
    count = 0
    for user_row in users:
        user = user_row['username']
        api_key = cfg['api']['key']
        page = 1
        total_pages = 1
        while page <= total_pages:
            logger.log("Getting page" + str(page))
            req_url = "https://ws.audioscrobbler.com/2.0/?method=user.gettopartists&user=" + user + "&api_key=" + api_key + "&page="+str(page)+"&limit=500&format=json"
            try:
                req = requests.get(req_url).json()
                lastfm = req["topartists"]
            except KeyError:
                logger.log("KeyError, skipping...")
                logger.log("Raw output: " + str(lastfm.text))
                break
            except Exception as e:
                logger.log("Some other issue occurred on getting this user from Last.fm:", e)
                break

            # get the total pages
            total_pages = int(lastfm["@attr"]["totalPages"])

            for entry in lastfm["artist"]:
                artist = sql_helper.esc_db(entry["name"])
                scrobbles = int(entry["playcount"])
                url = entry["url"]

                try:
                    # insert artist record
                    artist_record = {"name": artist, "url": url}
                    logger.log("Inserting new artist: " + str(artist_record))
                    sql = sql_helper.insert_into_where_not_exists("artists", artist_record, "name")
                    cursor.execute(sql)
                    mdb.commit()

                    # insert scrobble record
                    scrobble_record = {
                        "artist_name": artist,
                        "username": user,
                        "scrobbles": scrobbles
                    }
                    logger.log("Inserting new scrobble record: " + str(scrobble_record))
                    sql = sql_helper.replace_into("artist_scrobbles", scrobble_record)

                    cursor.execute(sql)
                    mdb.commit()
                except mariadb.Error as e:
                    logger.log("A database error occurred while inserting a record: " + str(e))
                    continue
                except Exception as e:
                    logger.log("An unknown error occured while inserting a record: " + str(e))
                    continue
            page += 1
    mdb.close()

def get_artists():
    mdb = mariadb.connect(**(cfg['sql']))
    cursor = mdb.cursor(dictionary=True)
    cursor.execute("SELECT * FROM artists;")
    result = list(cursor)
    mdb.close()
    if result:
        return result
    else:
        return False

scrape_artist_data()
