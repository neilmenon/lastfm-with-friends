import sys
import json
import requests
import mariadb
import datetime
import time
from bs4 import BeautifulSoup
from . import config
from . import sql_helper
from . import auth_helper
from . import user_helper
from . import api_logger as logger
cfg = config.config

def update_user(username, full=False, app=None, fix_count=False, stall_if_existing=True):
    logger.log("User update triggered for: " + username, app)
    user = user_helper.get_user(username, extended=False)
    last_update = user_helper.get_updated_date(username)
    full_scrape = not last_update or full
    failed_update = False
    if not full_scrape:
        updated_unix = str(int(last_update.replace(tzinfo=datetime.timezone.utc).timestamp()))
        current_unix = str(int(datetime.datetime.now(tz=datetime.timezone.utc).timestamp()))
        if user['progress']: # if there is a value here it means a scrape has not/did not finish
            # logger.log("\tDetected an unfinished ({}%) scrape. Finishing it...".format(user['progress']), app)
            registered_unix = str(user['registered'])
            # we can clear the last updated date now to signify an update
            user_helper.change_updated_date(username, clear_date=True)
    else: # if full scrape, we always clear this date
        user_helper.change_updated_date(username, clear_date=True)
        if user['progress'] and stall_if_existing: # we don't always want to stall, for example, user updates triggered from group sessions tasks
            logger.log("\tDetected a potential in-progress scrape ({}%). Stalling a bit to see if it's progressing...".format(user['progress']), app)
            time.sleep(60)
            current_progress = user_helper.get_user(username)['progress']
            if current_progress != user['progress']: # other task exists and is chugging along
                logger.log("\t\tAnother process exists and is progressing. Exiting...", app)
                return # kill this process as the other one already is doing something
            logger.log("\t\tOther process does not exist or is stuck. Continuing...", app)
        elif not stall_if_existing and user['progress']: # we don't want to wait for existing processes if user update was fired a task other than the main update task!
            logger.log("\tKilling user update due to other potential process ({}%).".format(user['progress']), app)
            return
    mdb = mariadb.connect(**(cfg['sql']))
    cursor = mdb.cursor(dictionary=True)
    page = 1
    total_pages = 1
    get_recent_uts = True
    most_recent_uts = None
    while page <= total_pages:
        if not full_scrape and not user['progress']:
            req_url = "http://ws.audioscrobbler.com/2.0/?method=user.getrecenttracks&user="+username+"&api_key="+cfg['api']['key']+"&from="+updated_unix+"&to="+current_unix+"&page="+str(page)+"&limit=1000&extended=1&format=json"
        elif user['progress'] and not full_scrape:
            req_url = "http://ws.audioscrobbler.com/2.0/?method=user.getrecenttracks&user="+username+"&api_key="+cfg['api']['key']+"&from="+registered_unix+"&to="+updated_unix+"&page="+str(page)+"&limit=1000&extended=1&format=json"
        else:
            req_url = "http://ws.audioscrobbler.com/2.0/?method=user.getrecenttracks&user="+username+"&api_key="+cfg['api']['key']+"&page="+str(page)+"&limit=1000&extended=1&format=json"
        try:
            req = requests.get(req_url).json()
            lastfm = req["recenttracks"]
        except KeyError as e:
            logger.log("\tSome Last.fm issue occurred on getting this user from Last.fm: " + str(e), app)
            logger.log("\tTrying to fetch this next page again...", app)
            try:
               req = requests.get(req_url).json()
               lastfm = req["recenttracks"] 
            except Exception as e:
                logger.log("\tFailed to fetch a second time. {}. Aborting...".format(str(e)), app)
                failed_update = True
        except Exception as e:
            logger.log("\tSome otherissue occurred on getting this user from Last.fm: " + str(e), app)
            failed_update = True
        finally:
            if failed_update:
                if full_scrape or user['progress']:
                    logger.log("\tSomething went during the initial update or fixing failed update, storing earliest grabbed track date as last updated date.", app)
                    sql = 'SELECT timestamp FROM `track_scrobbles` WHERE user_id = {} ORDER BY `track_scrobbles`.`timestamp` ASC LIMIT 1'.format(user['user_id'])
                    cursor.execute(sql)
                    result = list(cursor)
                    user_helper.change_updated_date(username, start_time=datetime.datetime.utcfromtimestamp(int(result[0]['timestamp']))) 
                    mdb.close()
                    return
                mdb.close()
                return

        # get the total pages
        total_pages = int(lastfm["@attr"]["totalPages"])
        tracks_fetched = int(lastfm["@attr"]["total"])
        if total_pages:
            logger.log("\tFetching page {}/{} for {}.".format(page, total_pages, username), app)
            user_helper.change_update_progress(username, round((page/total_pages)*100, 2))
        if tracks_fetched == 0:
            logger.log("\tNo tracks to fetch, user is up to date!", app)
            if user['scrobbles'] == 0: # if user hasn't scrobbled anything yet... set time to 2 weeks before last.fm registration, which is the earliest possible first scrobble
                earliest_scrobble_time = datetime.datetime.utcfromtimestamp(int(user['registered'])) - datetime.timedelta(days=15)
                user_helper.change_updated_date(username, start_time=earliest_scrobble_time)
                mdb.close()
                return {'tracks_fetched': -1, "last_update": str(earliest_scrobble_time)}
            mdb.close()
            return {'tracks_fetched': -1, "last_update": last_update}

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
            album_url = artist_url + "/" + sql_helper.format_lastfm_string(entry['album']['#text'])
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
                    logger.log("\t\tRedirected artist name conflict detected for '{} ({})'. Trying to get the Last.fm listed name...".format(artist, album_url), app)
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
                        logger.log("\t\t\tFound Last.fm artist name: {}. Continuing with inserts...".format(redirected_name), app)
                        
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
                            logger.log("\t\t\tFailed to insert.", app)
                            break
                elif artist == "Various Artists":
                    continue
                else:
                    logger.log("A database error occurred while inserting a record: " + str(e), app)
                    logger.log("\t\tQuery: " + sql, app)
                continue
            except Exception as e:
                logger.log("An unknown error occured while inserting a record: " + str(e), app)
                continue
        page += 1
    if tracks_fetched > 0:
        updated_user = user_helper.get_user_account(username, update=True)
        if not full_scrape or not user['progress']: # if it's a normal routine update
            sql = "SELECT COUNT(*) as total FROM `track_scrobbles` WHERE user_id = {} ORDER BY `timestamp` DESC".format(user['user_id'])
            cursor.execute(sql)
            result = list(cursor)
            if int(updated_user['scrobbles']) > result[0]['total']: # if Last.fm has more scrobbles than the database
                # this could happen if user went back and submitted scrobbles before most recent updated timestamp in database
                # delete scrobbles from past two weeks and fetch again in the same time period
                if not fix_count: # if we haven't already tried to fix the scrobble count (prevent infinite loop)
                    logger.log("\tMissing scrobbles for {} ({} lfm/{} db)! Deleting & re-fetching past two weeks...".format(username, updated_user['scrobbles'], result[0]['total']))
                    two_weeks_ago = most_recent_uts - 1209600
                    sql = "DELETE FROM `track_scrobbles` WHERE `user_id` = {} AND CAST(timestamp AS FLOAT) BETWEEN {} AND {}".format(user['user_id'], two_weeks_ago, str(int(datetime.datetime.now(tz=datetime.timezone.utc).timestamp())))
                    cursor.execute(sql)
                    mdb.commit()
                    user_helper.change_update_progress(username, None, clear_progress=True)
                    user_helper.change_updated_date(username, start_time=datetime.datetime.utcfromtimestamp(two_weeks_ago))
                    update_user(username, fix_count=True)
                else:
                    logger.log("\tFix attempt did not resolve missing scrobbles for {}. Triggering full scrape...".format(username))
                    update_user(username, full=True)
    if user['progress']:
        sql = 'SELECT timestamp FROM `track_scrobbles` WHERE user_id = {} ORDER BY `track_scrobbles`.`timestamp` DESC LIMIT 1'.format(user['user_id'])
        cursor.execute(sql)
        result = list(cursor)
        user_helper.change_updated_date(username, start_time=datetime.datetime.utcfromtimestamp(int(result[0]['timestamp'])))
    else:
        user_helper.change_updated_date(username, start_time=datetime.datetime.utcfromtimestamp(most_recent_uts))
    user_helper.change_update_progress(username, None, clear_progress=True)
    logger.log("\tFetched {} track(s) for {}.".format(tracks_fetched, username), app)
    mdb.close()
    return {'tracks_fetched': tracks_fetched, "last_update": datetime.datetime.utcfromtimestamp(most_recent_uts)}

def scrape_artist_images(full=False):
    mdb = mariadb.connect(**(cfg['sql']))
    cursor = mdb.cursor(dictionary=True)
    if full: # check for new image for ALL artists, regardless of whether they have an image or not
        sql = "SELECT * FROM `artists` WHERE `image_url`;"
    else:
        sql = "SELECT * FROM `artists` WHERE `image_url` IS null;"
    cursor.execute(sql)
    result = list(cursor)

    for artist in result:
        img = requests.get(artist['url']).text
        soup = BeautifulSoup(img, features="html.parser")
        s = soup.find('div', {"class", "header-new-background-image"})
        if s:
            image_url = s.get('content')
            logger.log("Added image for " + artist['name'] + ".")
        else:
            image_url = 'data:image/gif;base64,R0lGODlhAQABAAAAACH5BAEKAAEALAAAAAABAAEAAAICTAEAOw=='
            logger.log("\tImage for " + artist['name'] + " not found.")
        sql = "UPDATE `artists` SET `image_url` = '{}' WHERE `id` = {}".format(image_url, artist['id'])
        cursor.execute(sql)
        mdb.commit()
    mdb.close()

def scrape_album_data(full=False):
    mdb = mariadb.connect(**(cfg['sql']))
    cursor = mdb.cursor(dictionary=True)
    no_artwork_url = "https://lastfm.freetls.fastly.net/i/u/300x300/2a96cbd8b46e442fc41c2b86b821562f.png"
    if full: # scrape data for ALL albums, regardless of whether they have an image or not
        sql = "SELECT id,artist_name,name FROM `albums`;"
    else:
        sql = "SELECT id,artist_name,name FROM `albums` WHERE image_url = '{}'".format(no_artwork_url)
    cursor.execute(sql)
    result = list(cursor)
    logger.log("=========== Initiating album data scrape {}for {} albums... ===========".format("FULL MODE " if full else "", len(result)))
    newly_fetched_artwork = 0
    for album in result:
        logger.log("Fetching album data for {} - {}".format(album['artist_name'], album['name']))
        req_url = "https://ws.audioscrobbler.com/2.0/?method=album.getinfo&api_key={}&artist={}&album={}&format=json".format(cfg['api']['key'], sql_helper.format_lastfm_string(album['artist_name']), sql_helper.format_lastfm_string(album['name']))
        try:
            req = requests.get(req_url).json()
            album_info = req['album']
        except Exception as e:
            logger.log("\tAn error ocurred while trying get album data. Skipping... {}".format(e))
            logger.log("\tRequest URL: {}".format(req_url))
            continue
        artwork_url = album_info['image'][3]['#text'].strip()
        if artwork_url:
            logger.log("\t Artwork found!")
            newly_fetched_artwork += 1
            sql = "UPDATE `albums` SET `image_url` = '{}' WHERE id = {}".format(artwork_url, album['id'])
            cursor.execute(sql)
            mdb.commit()
    mdb.close()
    logger.log("Fetched new album art for {} out of {} ({}%) checked albums in the database.".format(newly_fetched_artwork, len(result), round((newly_fetched_artwork/(len(result)+1))*100, 2)))
