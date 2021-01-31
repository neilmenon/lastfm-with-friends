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

def full_user_scrape(username):
    user_helper.change_updated_date(username, True)
    start_time = datetime.datetime.utcnow()
    scrape_artist_data(username)
    scrape_album_data(username)
    user_helper.change_updated_date(username=username, start_time=start_time)

def update_user(username, full=False):
    logger.log("User update triggered for: " + username)
    user = user_helper.get_user(username, extended=False)
    last_update = user_helper.get_updated_date(username)
    full_scrape = not last_update or full
    if not full_scrape:
        updated_unix = str(int(last_update.replace(tzinfo=datetime.timezone.utc).timestamp()))
        current_unix = str(int(datetime.datetime.now(tz=datetime.timezone.utc).timestamp()))
        if user['progress']: # if there is a value here it means the the initial scrape did not finish
            logger.log("\tDetected an unfinished ({}%) initial scrape. Finishing it...".format(user['progress']))
            registered_unix = str(user['registered'])
            # we can clear the last updated date now to signify an update
            user_helper.change_updated_date(username, clear_date=True)
    mdb = mariadb.connect(**(cfg['sql']))
    cursor = mdb.cursor(dictionary=True)
    page = 1
    total_pages = 1
    get_recent_uts = True
    most_recent_uts = None
    while page <= total_pages:
        if not full_scrape and not user['progress']:
            req_url = "http://ws.audioscrobbler.com/2.0/?method=user.getrecenttracks&user="+username+"&api_key="+cfg['api']['key']+"&from="+updated_unix+"&to="+current_unix+"&page="+str(page)+"&limit=1000&extended=1&format=json"
        elif user['progress']:
            req_url = "http://ws.audioscrobbler.com/2.0/?method=user.getrecenttracks&user="+username+"&api_key="+cfg['api']['key']+"&from="+registered_unix+"&to="+updated_unix+"&page="+str(page)+"&limit=1000&extended=1&format=json"
        else:
            req_url = "http://ws.audioscrobbler.com/2.0/?method=user.getrecenttracks&user="+username+"&api_key="+cfg['api']['key']+"&page="+str(page)+"&limit=1000&extended=1&format=json"
        try:
            req = requests.get(req_url).json()
            lastfm = req["recenttracks"]
        except Exception as e:
            logger.log("\tSome issue occurred on getting this user from Last.fm: " + str(e))
            if full_scrape or user['progress']:
                logger.log("\tSomething went during the initial update or fixing failed update, storing earliest grabbed track date as last updated date.")
                sql = 'SELECT timestamp FROM `track_scrobbles` WHERE user_id = {} ORDER BY `track_scrobbles`.`timestamp` ASC LIMIT 1'.format(user['user_id'])
                cursor.execute(sql)
                result = list(cursor)
                user_helper.change_updated_date(username, start_time=datetime.datetime.utcfromtimestamp(int(result[0]['timestamp'])))
                return
            return

        # get the total pages
        total_pages = int(lastfm["@attr"]["totalPages"])
        tracks_fetched = int(lastfm["@attr"]["total"])
        if total_pages:
            logger.log("\tFetching page {}/{} for {}.".format(page, total_pages, username))
            user_helper.change_update_progress(username, round((page/total_pages)*100, 2))
        if tracks_fetched == 0:
            logger.log("\tNo tracks to fetch, user is up to date!")
            return {'tracks_fetched': -1, "last_update": last_update}
            break

        for entry in lastfm["track"]:
            try:
                if entry['@attr']['nowplaying']:
                    continue
            except KeyError:
                pass
            
            if get_recent_uts: # use the most recent track's timestamp as the last_updated date
                most_recent_uts = int(entry['date']['uts']) + 1
                get_recent_uts = False

            artist = sql_helper.esc_db(entry['artist']["name"])
            artist_url = entry['artist']['url']
            album = sql_helper.esc_db(entry['album']['#text'])
            album_url = artist_url + "/" + entry['album']['#text'].replace(" ", "+")
            track = sql_helper.esc_db(entry['name'])
            timestamp = entry['date']['uts']
            image_url = entry['image'][3]['#text']

            try:
                # insert artist record
                artist_record = {"name": artist, "url": artist_url}
                sql = sql_helper.insert_into_where_not_exists("artists", artist_record, "name")
                cursor.execute(sql)
                mdb.commit()

                # get the album id that was created
                cursor.execute("SELECT id FROM artists WHERE name = '"+artist+"';")
                result = list(cursor)
                artist_id = result[0]["id"]

                # insert album record
                album_record = {
                    "artist_name": artist, 
                    "name": album,
                    "url": sql_helper.esc_db(album_url),
                    "image_url": image_url
                }
                sql = sql_helper.insert_into_where_not_exists_2("albums", album_record, "artist_name", "name")
                cursor.execute(sql)
                mdb.commit()

                # get the album id that was created
                cursor.execute("SELECT id FROM albums WHERE artist_name = '"+artist+"' AND name = '"+album+"';")
                result = list(cursor)
                album_id = result[0]["id"]

                # insert full track record
                scrobble_record = {
                    "artist_id": artist_id,
                    "album_id": album_id,
                    "user_id": user['user_id'],
                    "track": track,
                    "timestamp": timestamp,
                }
                sql = sql_helper.replace_into("track_scrobbles", scrobble_record)
                cursor.execute(sql)
                mdb.commit()
            except mariadb.Error as e:
                if "albums_ibfk_1" in str(e) and artist != "Various Artists": 
                    logger.log("\t\tRedirected artist name conflict detected for '{} ({})'. Trying to get the Last.fm listed name...".format(artist, album_url))
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
                        logger.log("\t\t\tFound Last.fm artist name: {}. Continuing with inserts...".format(redirected_name))
                        
                        try:
                            # insert into artist_redirects table
                            data = {"artist_name": artist_name, "redirected_name": redirected_name}
                            sql = sql_helper.insert_into_where_not_exists("artist_redirects", data, "artist_name")
                            cursor.execute(sql)
                            mdb.commit()

                            # now we can insert into the the albums table and album_scrobbles tables
                            album_record["artist_name"] = redirected_name
                            sql = sql_helper.insert_into_where_not_exists_2("albums", album_record, "artist_name", "name")
                            cursor.execute(sql)
                            mdb.commit()

                            # get the album id that was created
                            cursor.execute("SELECT id FROM albums WHERE artist_name = '"+artist+"' AND name = '"+album+"';")
                            result = list(cursor)
                            album_id = result[0]["id"]

                            # insert full track record
                            scrobble_record = {
                                "artist_id": artist_id,
                                "album_id": album_id,
                                "user_id": user['user_id'],
                                "track": track,
                                "timestamp": timestamp
                            }
                            sql = sql_helper.replace_into("track_scrobbles", scrobble_record)
                            cursor.execute(sql)
                            mdb.commit()
                        except mariadb.Error as e:
                            logger.log("\t\t\tFailed to insert.")
                            break
                elif artist == "Various Artists":
                    continue
                else:
                    logger.log("A database error occurred while inserting a record: " + str(e))
                    logger.log("\t\tQuery: " + sql)
                continue
            except Exception as e:
                logger.log("An unknown error occured while inserting a record: " + str(e))
                continue
        page += 1
    if user['progress']:
        sql = 'SELECT timestamp FROM `track_scrobbles` WHERE user_id = {} ORDER BY `track_scrobbles`.`timestamp` DESC LIMIT 1'.format(user['user_id'])
        cursor.execute(sql)
        result = list(cursor)
        user_helper.change_updated_date(username, start_time=datetime.datetime.utcfromtimestamp(int(result[0]['timestamp'])))
    else:
        user_helper.change_updated_date(username, start_time=datetime.datetime.utcfromtimestamp(most_recent_uts))
    if tracks_fetched > 0:
        user_helper.get_user_account(username, update=True)
    user_helper.change_update_progress(username, None, clear_progress=True)
    logger.log("\tFetched {} track(s) for {}.".format(tracks_fetched, username))
    return {'tracks_fetched': tracks_fetched, "last_update": datetime.datetime.utcfromtimestamp(most_recent_uts)}

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
            except Exception as e:
                logger.log("Some other issue occurred on getting this user from Last.fm:", e)
                user_helper.change_updated_date(username, start_time=datetime.datetime.utcfromtimestamp(1))
                return

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
            logger.log("Added image for " + artist['name'] + ".")
        else:
            logger.log("\tImage for " + artist['name'] + " not found.")
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
