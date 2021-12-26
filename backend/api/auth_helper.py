import datetime
import requests
import hashlib
from flask import request
from threading import Thread
from . import config
from . import sql_helper
from . import user_helper
from . import api_logger as logger

cfg = config.config

def is_authenticated(username, session_key):
    '''
        returns True if session key is valid and matches the user
        returns False if the above are false
    '''
    try:
        sql = 'SELECT * FROM sessions WHERE session_key = "{}";'.format(session_key)
        result = sql_helper.execute_db(sql)
        if len(result) > 0:
            session = result[0]
            if session['username'] != username: # user does not match session key
                return False
            # session key is valid; updated last_used field in sessions table then return True
            sql = "UPDATE `sessions` SET `last_used` = '"+str(datetime.datetime.utcnow())+"' WHERE `sessions`.`session_key` = '"+session_key+"'"
            sql_helper.execute_db(sql, commit=True)
            return True
        else: # session key not found in database, user is not authenticated
            return False
    except Exception as e:
        logger.error("Error while checking if {} is authenticated: ".format(username) + str(e))
        return False

def remove_session(username, session_key):
    try:
        sql = 'DELETE FROM sessions WHERE session_key = "'+session_key+'";'
        sql_helper.execute_db(sql, True)
        return True
    except Exception as e:
        logger.error("Error while removing session key for " + username + ": " + str(e))
        return False

def get_and_store_session(token):
    '''
        Gets session key from Last.fm and stores it in the database.
        If user is not in database, a new record will be added to the database.
        returns the user's username if session key was obtained and stored properly, else False
    '''
    data = {}
    data['api_key'] = cfg['api']['key']
    data['token'] = token
    data['method'] = 'auth.getSession'
    signed_data = get_signed_object(data)
    # get session_key from Last.fm
    try:
        lastfm_auth = requests.post("https://ws.audioscrobbler.com/2.0", data=signed_data).json()
        session_key = lastfm_auth['session']['key']
        username = lastfm_auth['session']['name']
        logger.info("New login from Last.fm user " + username)
    except AttributeError:
        logger.error("Error while getting session from Last.fm: did not return JSON object")
        return False
    except KeyError:
        logger.error("Error while getting session from Last.fm: " + str(lastfm_auth))
        return False
    except Exception as e:
        logger.error("Error while getting session from Last.fm:" + str(e))
        return False
    # check if user exists in database, if not create new user
    if not user_helper.get_user(username):
        just_registered = True
        user_helper.get_user_account(username)
    else:
        just_registered = False
    # store session key in sessions table
    try:
        table_data = {}
        table_data['username'] = username
        table_data['session_key'] = session_key
        table_data['last_used'] = str(datetime.datetime.utcnow())
        sql = sql_helper.insert_into_where_not_exists("sessions", table_data, "session_key")
        sql_helper.execute_db(sql, commit=True)

        if just_registered:
            # new user needs an initial data fetch!
            new_user = user_helper.get_user(username, False)
            thread = Thread(target=user_helper.fire_and_forget_user_update, args=(username, session_key, new_user['user_id'], request.base_url.replace("authenticate", "update")))
            thread.start()

        return {"username": username, "session_key": session_key}
    except Exception as e:
        logger.error("Error while storing session for " + username + ": " + str(e))
        return False

def get_signed_object(data):
    '''
        Creates hashed API signature and returns signed object for authentication - https://www.last.fm/api/webauth
        Python solution based on the https://stackoverflow.com/a/30626108/14861722 JS/JQuery solution - thanks!
    '''
    signed_signature = ""
    object_keys = []
    signed_object = {}
    hashed_signature = ""
    for k,v in data.items(): # get list of keys from data
        object_keys.append(k)
    object_keys.sort()
    for key in object_keys: # construct the API method signature as described at , Section 6
        signed_signature = signed_signature + key + data[key]
        signed_object[key] = data[key] # make sure object is in same order, just in case
    signed_signature += cfg['api']['secret'] # secret key needs to appended to end of signature according to API docs
    # escaped_signature = urllib.parse.quote(signed_signature, safe=" ").encode('utf-8')
    escaped_signature = signed_signature.encode('utf-8')
    hashed_signature = hashlib.md5(escaped_signature).hexdigest()
    signed_object['api_sig'] = hashed_signature
    signed_object['format'] = "json" # add return format **after** hashing, signature will be invalid otherwise
    return signed_object

def generate_scrobble_body(session_key, tracks):
    http_datas = []
    for track in tracks:
        data = {}
        data['api_key'] = cfg['api']['key']
        data['sk'] = session_key
        data['method'] = 'track.scrobble'
        data['artist'] = track['artist']
        data['track'] = track['track']
        if track['album']:
            data['album'] = track['album']
        data['timestamp'] = track['timestamp'] if track['timestamp'] else str(int(datetime.datetime.now(tz=datetime.timezone.utc).timestamp()))
        signed_data = get_signed_object(data)

        http_datas.append(signed_data)
    
    return http_datas
