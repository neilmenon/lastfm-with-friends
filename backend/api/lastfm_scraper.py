import sys
import json
from threading import Thread
import requests
import datetime
import time
from bs4 import BeautifulSoup
from . import config
from . import sql_helper
from . import auth_helper
from . import user_helper
from . import api_logger as logger
cfg = config.config

# this method allows an update to go through without holding up the request
# (i.e. the request will not wait until a user update finishes to return)
# this function is ALWAYS called inside a thread instance, where we need to manually
# specify the Flask application context (this function must be called via a new thread!)
def update_user_from_thread(username, full=False, app=None, fix_count=False, stall_if_existing=True, wipe=None, from_queue=False):
    if app:
        with app.app_context():
            if wipe:
                user_helper.change_update_progress(username, -420)
                user_helper.wipe_scrobbles(username, wipe) # wipe is user_id
                user_helper.change_update_progress(username, 3, clear_progress=True)
            update_user(username, full, app, fix_count, stall_if_existing, from_queue=from_queue)
    else:
        update_user(username, full, app, fix_count, stall_if_existing, from_queue=from_queue)

def update_user(username, full=False, app=None, fix_count=False, stall_if_existing=True, from_queue=False):
    logger.info("User update triggered for: " + username, app)
    user: dict = user_helper.get_user(username, extended=False)
    last_update = user_helper.get_updated_date(username)
    full_scrape = not last_update or full or (user['scrobbles'] == 0 and last_update and user['progress'] > 0)
    failed_update = False

    # start queue handling
    if from_queue and user['progress'] == -22: # if pulled off queue, start execution
        user_helper.change_update_progress(username, None, clear_progress=True)
        user_helper.change_updated_date(username, clear_date=True)
        user['progress'] = 0
    else: # if not from queue, check if we are trying a full scrape, if so, we need to queue it first
        if full_scrape:
            logger.info("\tQueueing full scrape update for {}.".format(username))
            user_helper.change_update_progress(username, -22)
            user_helper.change_updated_date(username, start_time=datetime.datetime.utcnow())
            return
    
    if user['progress']:
        # if progress value is -420, system is wiping the old scrobbles in preparation for a full scrape
        # exit here
        if int(user["progress"]) == -420:
            logger.warn("\tDetected another process is wiping scrobbles in order to do a full scrape. Exiting here...", app)
            return
        elif int(user["progress"]) == -22:
            logger.info("\tUser update already queued for {}. Exiting here...".format(username))
            return
    # end queue handling

    if not full_scrape:
        updated_unix = str(int(last_update.replace(tzinfo=datetime.timezone.utc).timestamp()))
        current_unix = str(int(datetime.datetime.now(tz=datetime.timezone.utc).timestamp()))
        if user['progress']: # if there is a value here it means a scrape has not/did not finish
            # logger.info("\tDetected an unfinished ({}%) scrape. Finishing it...".format(user['progress']), app)
            registered_unix = str(user['registered'])
        # we can clear the last updated date now to signify an update
        user_helper.change_updated_date(username, clear_date=True)
    else: # if full scrape, we always clear this date
        user_helper.change_updated_date(username, clear_date=True)
        if user['progress'] and stall_if_existing: # we don't always want to stall, for example, user updates triggered from group sessions tasks
            logger.warn("\tDetected a potential in-progress scrape ({}%). Stalling a bit to see if it's progressing...".format(user['progress']), app)
            time.sleep(30)
            current_progress = user_helper.get_user(username)['progress']
            if current_progress != user['progress']: # other task exists and is chugging along
                logger.info("\t\tAnother process exists and is progressing. Exiting...", app)
                return # kill this process as the other one already is doing something
            logger.info("\t\tOther process does not exist or is stuck. Continuing...", app)
        elif not stall_if_existing and user['progress']: # we don't want to wait for existing processes if user update was fired a task other than the main update task!
            logger.info("\tKilling user update due to other potential process ({}%).".format(user['progress']), app)
            return
    page = 1
    total_pages = 1
    get_recent_uts = True
    most_recent_uts = None
    previous_track = None
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
            logger.warn("\tSome Last.fm issue occurred on getting this user from Last.fm: " + str(e), app)
            logger.warn("\tTrying to fetch this next page again...", app)
            try:
               req = requests.get(req_url).json()
               lastfm = req["recenttracks"] 
            except Exception as e:
                logger.error("\tFailed to fetch a second time. {}. Aborting...".format(str(e)), app)
                failed_update = True
        except Exception as e:
            logger.error("\tSome other issue occurred on getting this user from Last.fm: " + str(e), app)
            failed_update = True
        finally:
            if failed_update:
                if full_scrape or user['progress']:
                    logger.error("\tSomething went during the initial update or fixing failed update, now's date and queueing.", app)
                    sql = 'SELECT timestamp FROM `track_scrobbles` WHERE user_id = {} ORDER BY `track_scrobbles`.`timestamp` ASC LIMIT 1'.format(user['user_id'])
                    result = sql_helper.execute_db(sql)
                    if (len(result)):
                        user_helper.change_updated_date(username, start_time=datetime.datetime.utcfromtimestamp(int(result[0]['timestamp'])))
                    else:
                        logger.warn("\tNo earliest track to store for {}!".format(username), app)
                    return
                return

        # get the total pages
        total_pages = int(lastfm["@attr"]["totalPages"])
        tracks_fetched = int(lastfm["@attr"]["total"])
        if total_pages:
            logger.info("\tFetching page {}/{} for {}.".format(page, total_pages, username), app)
            user_helper.change_update_progress(username, round((page/total_pages)*100, 2))
        if tracks_fetched == 0:
            logger.info("\tNo tracks to fetch, user is up to date!", app)
            if user['scrobbles'] == 0: # if user hasn't scrobbled anything yet... set time to 2 weeks before last.fm registration, which is the earliest possible first scrobble
                earliest_scrobble_time = datetime.datetime.utcfromtimestamp(int(user['registered'])) - datetime.timedelta(days=15)
                user_helper.change_updated_date(username, start_time=earliest_scrobble_time)
                return {'tracks_fetched': -1, "last_update": str(earliest_scrobble_time)}
            # store latest track timestamp
            sql = 'SELECT timestamp FROM `track_scrobbles` WHERE user_id = {} ORDER BY `track_scrobbles`.`timestamp` DESC LIMIT 1'.format(user['user_id'])
            result = sql_helper.execute_db(sql)
            if len(result):
                user_helper.change_updated_date(username, start_time=datetime.datetime.utcfromtimestamp(int(result[0]['timestamp'])))
                user_helper.change_update_progress(username, None, clear_progress=True)
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
            track = track[:400] if len(track) > 400 else track
            timestamp = entry['date']['uts']
            image_url = entry['image'][3]['#text']

            # try:
            # insert artist record
            artist_record = {"name": artist, "url": artist_url}
            sql = sql_helper.insert_into_where_not_exists("artists", artist_record, "name")
            sql_helper.execute_db(sql, commit=True, pass_on_error=True)

            # get the album id that was created
            result = sql_helper.execute_db("SELECT id FROM artists WHERE name = '"+artist+"';", pass_on_error=True)
            artist_id = result[0]["id"]

            # insert album record
            album_record = {
                "artist_name": artist, 
                "name": album,
                "url": sql_helper.esc_db(album_url),
                "image_url": image_url
            }
            sql = sql_helper.insert_into_where_not_exists_2("albums", album_record, "artist_name", "name")
            sql_helper.execute_db(sql, commit=True, pass_on_error=True)

            # get the album id that was created
            result = sql_helper.execute_db("SELECT id FROM albums WHERE artist_name = '"+artist+"' AND name = '"+album+"';", pass_on_error=True)
            album_id = result[0]["id"]

            # insert full track record
            scrobble_record = {
                "artist_id": artist_id,
                "album_id": album_id,
                "user_id": user['user_id'],
                "track": track,
                "timestamp": timestamp,
            }
            
            # workaround for issue where Last.fm allows an exact duplicate scrobble record to exist in their database
            # while the app's database does not for multiple reasons, resulting in a data discrepancy
            # the below nudges the timestamp by 1 second to ensure that the record makes it into the database
            # and the total Last.fm <> app DB scrobble remains intact (to prevent triggering full scrapes infinitely)
            if previous_track == scrobble_record:
                logger.warn("[RESOLVED] Exact scrobble record duplicate fetched from Last.fm: {}".format(str(scrobble_record)))
                scrobble_record["timestamp"] = str(int(scrobble_record["timestamp"]) + 1)

            sql = sql_helper.replace_into("track_scrobbles", scrobble_record)
            sql_helper.execute_db(sql, commit=True, pass_on_error=True)
            previous_track = scrobble_record
        page += 1
    if tracks_fetched > 0:
        updated_user = user_helper.get_user_account(username, update=True)
        if not full_scrape or not user['progress']: # if it's a normal routine update
            sql = "SELECT COUNT(*) as total FROM `track_scrobbles` WHERE user_id = {} ORDER BY `timestamp` DESC".format(user['user_id'])
            result = sql_helper.execute_db(sql)
            lfm_more_scrobbles = int(updated_user['scrobbles']) > result[0]['total']
            app_more_scrobbles_threshold = result[0]['total'] - int(updated_user['scrobbles']) > 5
            app_more_scrobbles = result[0]['total'] - int(updated_user['scrobbles'])
            if app_more_scrobbles > 0:
                logger.warn("\tDetected {} unaccounted for scrobble(s) in DB which are not in Last.fm for {}. Fetched {} tracks this update.".format(app_more_scrobbles, username, tracks_fetched))
            if lfm_more_scrobbles or app_more_scrobbles_threshold: # if Last.fm has more scrobbles than the database, or vis versa
                # lfm_more_scrobbles: this could happen if user went back and submitted scrobbles before most recent updated timestamp in database
                # app_more_scrobbles: cause unknown
                # delete scrobbles from past two weeks and fetch again in the same time period
                if not fix_count: # if we haven't already tried to fix the scrobble count (prevent infinite loop)
                    logger.warn("\t{} scrobbles for {} ({} lfm/{} db)! Deleting & re-fetching past two weeks...".format("Missing" if lfm_more_scrobbles else "Extra", username, updated_user['scrobbles'], result[0]['total']))
                    two_weeks_ago = most_recent_uts - 1209600
                    sql = "DELETE FROM `track_scrobbles` WHERE `user_id` = {} AND CAST(timestamp AS FLOAT) BETWEEN {} AND {}".format(user['user_id'], two_weeks_ago, str(int(datetime.datetime.now(tz=datetime.timezone.utc).timestamp())))
                    sql_helper.execute_db(sql, commit=True)
                    user_helper.change_update_progress(username, None, clear_progress=True)
                    user_helper.change_updated_date(username, start_time=datetime.datetime.utcfromtimestamp(two_weeks_ago))
                    response = update_user(username, fix_count=True)
                    if response:
                        return response
                else:
                    logger.error("\tFix attempt did not resolve {} scrobbles for {}. Triggering full scrape...".format("missing" if lfm_more_scrobbles else "extra", username))
                    if app_more_scrobbles > 0:
                        user_helper.change_update_progress(username, -420)
                        user_helper.wipe_scrobbles(username, user["user_id"])
                    user_helper.change_update_progress(username, -22)
                    user_helper.change_updated_date(username, start_time=datetime.datetime.utcnow())
                    return { 'message': "Discrepancy between Last.fm and app detected, queueing full scrape to resolve.", 'progress': -22, 'last_update': str(datetime.datetime.utcnow()) }
    if user['progress']:
        sql = 'SELECT timestamp FROM `track_scrobbles` WHERE user_id = {} ORDER BY `track_scrobbles`.`timestamp` DESC LIMIT 1'.format(user['user_id'])
        result = sql_helper.execute_db(sql)
        if len(result):
            user_helper.change_updated_date(username, start_time=datetime.datetime.utcfromtimestamp(int(result[0]['timestamp'])))
        else:
            user_helper.change_updated_date(username, start_time=datetime.datetime.utcfromtimestamp(1))
    else:
        user_helper.change_updated_date(username, start_time=datetime.datetime.utcfromtimestamp(most_recent_uts))
    user_helper.change_update_progress(username, None, clear_progress=True)
    logger.info("\tFetched {} track(s) for {}.".format(tracks_fetched, username), app)
    return {'tracks_fetched': tracks_fetched, "last_update": datetime.datetime.utcfromtimestamp(most_recent_uts)}

def scrape_artist_images(full=False):
    if full: # check for new image for ALL artists (except ones who are null to avoid multi processing)
        sql = "SELECT * FROM `artists` WHERE `image_url` IS NOT NULL;"
    else:
        sql = "SELECT * FROM `artists` WHERE `image_url` IS NULL;"
    result = sql_helper.execute_db(sql)

    for artist in result:
        img = requests.get(artist['url']).text
        soup = BeautifulSoup(img, features="html.parser")
        s = soup.find('div', {"class", "header-new-background-image"})
        if s:
            image_url = s.get('content')
            logger.info("Added image for " + artist['name'] + ".")
        else:
            image_url = 'data:image/gif;base64,R0lGODlhAQABAAAAACH5BAEKAAEALAAAAAABAAEAAAICTAEAOw=='
            logger.info("\tImage for " + artist['name'] + " not found.")
        sql = "UPDATE `artists` SET `image_url` = '{}' WHERE `id` = {}".format(image_url, artist['id'])
        sql_helper.execute_db(sql, commit=True)

def scrape_album_data(full=False):
    no_artwork_url = "https://lastfm.freetls.fastly.net/i/u/300x300/2a96cbd8b46e442fc41c2b86b821562f.png"
    if full: # scrape data for ALL albums, regardless of whether they have an image or not
        sql = "SELECT id,artist_name,name FROM `albums`;"
    else:
        sql = "SELECT id,artist_name,name FROM `albums` WHERE image_url = '{}'".format(no_artwork_url)
    result = sql_helper.execute_db(sql)
    logger.info("=========== Initiating album data scrape {}for {} albums... ===========".format("FULL MODE " if full else "", len(result)))
    newly_fetched_artwork = 0
    for album in result:
        logger.info("Fetching album data for {} - {}".format(album['artist_name'], album['name']))
        req_url = "https://ws.audioscrobbler.com/2.0/?method=album.getinfo&api_key={}&artist={}&album={}&format=json".format(cfg['api']['key'], sql_helper.format_lastfm_string(album['artist_name']), sql_helper.format_lastfm_string(album['name']))
        try:
            req = requests.get(req_url).json()
            album_info = req['album']
        except Exception as e:
            try:
                if album_info['error'] == 6:
                    logger.warn("\tAlbum was not found via Last.fm API. Skipping...")
                    logger.warn("\tRequest URL: {}".format(req_url))
            except KeyError:
                logger.error("\tAn error ocurred while trying get album data. Skipping... {}".format(e))
                logger.error("\tRequest URL: {}".format(req_url))
            continue
        artwork_url = album_info['image'][3]['#text'].strip()
        if artwork_url:
            logger.info("\t Artwork found!")
            newly_fetched_artwork += 1
            sql = "UPDATE `albums` SET `image_url` = '{}' WHERE id = {}".format(artwork_url, album['id'])
            sql_helper.execute_db(sql, commit=True)
    logger.info("Fetched new album art for {} out of {} ({}%) checked albums in the database.".format(newly_fetched_artwork, len(result), round((newly_fetched_artwork/(len(result)+1))*100, 2)))

def scrape_extra_artist_info(full=False):
    # get artists who do not have listeners and playcount set
    if not full:
        sql = "SELECT id, name FROM artists WHERE listeners IS NULL AND playcount IS NULL"
    else:
        sql = "SELECT id, name FROM artists"
    artists = sql_helper.execute_db(sql)
    
    for artist in artists:
        logger.info("Fetching extra artist data for {} (ID: {})".format(artist['name'], artist['id']))
        req_url = "https://ws.audioscrobbler.com/2.0/?method=artist.getinfo&artist={}&api_key={}&format=json&autocorrect=1".format(sql_helper.format_lastfm_string(artist['name']), cfg['api']['key'])
        try:
            req = requests.get(req_url).json()
            artist_info = req['artist']
        except Exception as e:
            logger.error("\tAn error ocurred while trying get artist data. Skipping... {}".format(e))
            logger.error("\tRequest URL: {}".format(req_url))
            continue

        listeners = artist_info['stats']['listeners']
        playcount = artist_info['stats']['playcount']
        genres = [g['name'].lower().replace("-", " ") for g in artist_info['tags']['tag']]

        # update artist with listeners and playcount
        sql_helper.execute_db("UPDATE artists SET listeners = {}, playcount = {} WHERE id = {}".format(listeners, playcount, artist['id']), commit=True)

        # filter genres from blacklist (TODO)
        blacklisted_genres = [artist['name'].lower(), 'seen live', 'female vocalists', 'american', 'male vocalists', 'usa', 'all', 'under 2000 listeners', 'vocal', 'gay']
        filtered_genres = list(filter(lambda x: x not in blacklisted_genres and len(x) < 50, genres))

        for g in filtered_genres:
            # insert genre if it does not already exist
            sql_helper.execute_db(sql_helper.insert_into_where_not_exists("genres", { "name": sql_helper.esc_db(g) }, "name"), commit=True)

            # get ID of the genre
            genre_id = sql_helper.execute_db("SELECT id FROM genres WHERE name = '{}'".format(sql_helper.esc_db(g)))[0]['id']

            # add association between the artist and the genre
            data = { "artist_id": artist['id'], "genre_id": genre_id }
            sql_helper.execute_db(sql_helper.replace_into("artist_genres", data), commit=True)

    return { 'artists_processed': len(artists) }

