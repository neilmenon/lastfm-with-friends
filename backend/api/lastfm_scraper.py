import sys
import json
import requests
import mariadb
import datetime
from bs4 import BeautifulSoup
from . import config
from . import sql_helper
from . import auth_helper
from . import user_helper
from . import api_logger as logger
cfg = config.config

def user_scrape(username):
    change_updated_date(username, True)
    scrape_artist_data(username)
    scrape_album_data(username)
    change_updated_date(username)

def change_updated_date(username, clear_date=False):
    mdb = mariadb.connect(**(cfg['sql']))
    cursor = mdb.cursor(dictionary=True)
    if clear_date:
        sql = "UPDATE `users` SET `last_update` = NULL WHERE `users`.`username` = '"+ username + "';"
    else:
        sql = "UPDATE `users` SET `last_update` = '"+str(datetime.datetime.utcnow())+"' WHERE `users`.`username` = '"+ username + "';"
    cursor.execute(sql)
    mdb.commit()
    mdb.close()

def scrape_artist_data(username=None):
    mdb = mariadb.connect(**(cfg['sql']))
    cursor = mdb.cursor(dictionary=True)
    if username:
        users = [{"username": username}]
        logger.log("Fetching artist data for user: " + username)
    else:
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
            # logger.log("Getting page " + str(page) + " of artists for " + user)
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
                    # logger.log("Inserting new artist: " + str(artist_record))
                    sql = sql_helper.insert_into_where_not_exists("artists", artist_record, "name")
                    cursor.execute(sql)
                    mdb.commit()

                    # get the album id that was created
                    cursor.execute("SELECT id FROM artists WHERE name = '"+artist+"';")
                    result = list(cursor)
                    artist_id = result[0]["id"]

                    # insert scrobble record
                    scrobble_record = {
                        "artist_id": artist_id,
                        "username": user,
                        "scrobbles": scrobbles
                    }
                    # logger.log("Inserting new scrobble record: " + str(scrobble_record))
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

def scrape_album_data(username=None):
    failed_artists = []
    mdb = mariadb.connect(**(cfg['sql']))
    cursor = mdb.cursor(dictionary=True)
    if username:
        users = [{"username": username}]
        logger.log("Fetching album data for user: " + username)
    else:
        users = user_helper.get_users()
        if not users:
            logger.log("No users to scrape albums from!")
            return False
    count = 0
    for user_row in users:
        user = user_row['username']
        api_key = cfg['api']['key']
        page = 1
        total_pages = 1
        while page <= total_pages:
            # logger.log("Getting page " + str(page) + " of artists for " + user)
            req_url = "https://ws.audioscrobbler.com/2.0/?method=user.gettopalbums&user=" + user + "&api_key=" + api_key + "&page="+str(page)+"&limit=500&format=json"
            try:
                req = requests.get(req_url).json()
                lastfm = req["topalbums"]
            except KeyError:
                logger.log("KeyError, skipping...")
                logger.log("Raw output: " + str(lastfm.text))
                break
            except Exception as e:
                logger.log("Some other issue occurred on getting this user from Last.fm:", e)
                break

            # get the total pages
            total_pages = int(lastfm["@attr"]["totalPages"])

            for entry in lastfm["album"]:
                artist = sql_helper.esc_db(entry["artist"]["name"])
                album = sql_helper.esc_db(entry["name"])
                url = entry["url"]
                image_url = entry["image"][3]["#text"]
                scrobbles = int(entry["playcount"])

                try:
                    # insert album record
                    album_record = {
                        "artist_name": artist, 
                        "name": album,
                        "url": url,
                        "image_url": image_url
                    }
                    # logger.log("Inserting new artist: " + str(artist_record))
                    sql = sql_helper.insert_into_where_not_exists("albums", album_record, "url")
                    cursor.execute(sql)
                    mdb.commit()

                    # get the album id that was created
                    cursor.execute("SELECT id FROM albums WHERE url = '"+url+"';")
                    result = list(cursor)
                    album_id = result[0]["id"]

                    # insert scrobble record
                    scrobble_record = {
                        "album_id": album_id,
                        "username": user,
                        "scrobbles": scrobbles
                    }
                    # logger.log("Inserting new scrobble record: " + str(scrobble_record))
                    sql = sql_helper.replace_into("album_scrobbles", scrobble_record)

                    cursor.execute(sql)
                    mdb.commit()
                except mariadb.Error as e:
                    if "albums_ibfk_1" in str(e) and artist != "Various Artists": 
                        logger.log("Redirected artist name conflict detected for '{} ({})'. Trying to get the Last.fm listed name...".format(artist, url))
                        # artist name redirected to different page so not in artist table
                        # add alternate name to artist_redirects table

                        redirected_url = entry['artist']['url']
                        artist_page = requests.get(redirected_url).text
                        soup = BeautifulSoup(artist_page, features="html.parser")
                        if "noredirect" in redirected_url:
                            s = soup.select('p.nag-bar-message > strong > a')[0].text.strip()
                        else:
                            s = soup.select('h1.header-new-title')[0].text.strip()
                        if s:
                            artist_name = artist
                            redirected_name = s
                            logger.log("\tFound Last.fm artist name: {}. Continuing with inserts...".format(redirected_name))
                            
                            try:
                                # insert into artist_redirects table
                                data = {"artist_name": artist_name, "redirected_name": redirected_name}
                                sql = sql_helper.insert_into_where_not_exists("artist_redirects", data, "artist_name")
                                cursor.execute(sql)
                                mdb.commit()

                                # now we can insert into the the albums table and album_scrobbles tables
                                album_record["artist_name"] = redirected_name
                                sql = sql_helper.insert_into_where_not_exists("albums", album_record, "url")
                                cursor.execute(sql)
                                mdb.commit()

                                # get the album id that was created
                                cursor.execute("SELECT id FROM albums WHERE url = '"+url+"';")
                                result = list(cursor)
                                album_id = result[0]["id"]

                                # insert scrobble record
                                scrobble_record = {
                                    "album_id": album_id,
                                    "username": user,
                                    "scrobbles": scrobbles
                                }
                                sql = sql_helper.replace_into("album_scrobbles", scrobble_record)
                                cursor.execute(sql)
                                mdb.commit()
                            except mariadb.Error as e:
                                logger.log("\tFailed to insert.")
                                failed_artists.append([redirected_name, redirected_url])
                                break
                    elif artist == "Various Artists":
                        continue
                    else:
                        logger.log("A database error occurred while inserting a record: " + str(e))
                        logger.log("\tQuery: " + sql)
                    continue
                except Exception as e:
                    logger.log("An unknown error occured while inserting a record: " + str(e))
                    continue
            page += 1
    mdb.close()
    logger.log("------ Failed after attempted fix -----")
    for f in failed_artists:
        logger.log(str(f))

def scrape_artist_images():
    mdb = mariadb.connect(**(cfg['sql']))
    cursor = mdb.cursor(dictionary=True)
    cursor.execute("SELECT * FROM `artists` WHERE `image_url` IS null;")
    result = list(cursor)

    for artist in result:
        img = requests.get(artist['url']).text
        soup = BeautifulSoup(img, features="html.parser")
        s = soup.find('div', {"class", "header-new-background-image"})
        if s:
            image_url = s.get('content')
            record = artist
            record['name'] = sql_helper.esc_db(record['name'])
            record['image_url'] = image_url
            sql = sql_helper.replace_into("artists", record)
            cursor.execute(sql)
            mdb.commit()
            print("Added image for " + artist['name'] + ".")
        else:
            continue
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
