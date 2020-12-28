import mariadb
import datetime
import requests
import hashlib
from . import config
from . import sql_helper
from . import user_helper
from . import api_logger as logger
import urllib

cfg = config.config

'''
    returns True if session key is valid and matches the user
    returns False if the above are false
'''
def is_authenticated(username, session_key):
    try:
        mdb = mariadb.connect(**(cfg['sql']))
        cursor = mdb.cursor(dictionary=True)
        sql = 'SELECT * FROM sessions WHERE session_key = "'+session_key+'";'
        cursor.execute(sql)
        result = list(cursor)
        if len(result) > 0:
            session = result[0]
            if session['username'] != username: # user does not match session key
                return False
            # session key is valid; updated last_used field in sessions table then return True
            sql = "UPDATE `sessions` SET `last_used` = '"+str(datetime.datetime.now())+"' WHERE `sessions`.`session_key` = '"+session_key+"'"
            cursor.execute(sql)
            mdb.commit()
            mdb.close()
            return True
        else: # session key not found in database, user is not authenticated
            return False
    except mariadb.Error as e:
        logger.log("Database error while checking if " + username + " is authenticated: " + str(e))
        return False
    except Exception as e:
        logger.log("Error while checking if " + username + " is authenticated: " + str(e))

'''
    Gets session key from Last.fm and stores it in the database.
    If user is not in database, a new record will be added to the database.
    returns the user's username if session key was obtained and stored properly, else False
'''
def get_and_store_session(token):
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
        logger.log("New login from Last.fm user " + username)
    except AttributeError:
        logger.log("Error while getting session from Last.fm: did not return JSON object")
        return False
    except KeyError:
        logger.log("Error while getting session from Last.fm: " + str(lastfm_auth))
        return False
    except Exception as e:
        logger.log("Error while getting session from Last.fm:" + str(e))
        return False
    # check if user exists in database, if not create new user
    if not user_helper.get_user(username):
        user_helper.create_user(username)
    # store session key in sessions table
    try:
        mdb = mariadb.connect(**(cfg['sql']))
        cursor = mdb.cursor(dictionary=True)
        table_data = {}
        table_data['username'] = username
        table_data['session_key'] = session_key
        table_data['last_used'] = str(datetime.datetime.now())
        sql = sql_helper.insert_into_where_not_exists("sessions", table_data, "session_key")
        cursor.execute(sql)
        mdb.commit()
        mdb.close()
        return {"username": username, "session_key": session_key}
    except mariadb.Error as e:
        logger.log("Database error while storing session for " + username + ": " + str(e))
        return False
    except Exception as e:
        logger.log("Error while storing session for " + username + ": " + str(e))
        return False
'''
    Creates hashed API signature and returns signed object for authentication - https://www.last.fm/api/webauth
    Python solution based on the https://stackoverflow.com/a/30626108/14861722 JS/JQuery solution - thanks!
'''
def get_signed_object(data):
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
    hashed_signature = hashlib.md5(urllib.parse.quote(signed_signature).encode('utf-8')).hexdigest()
    signed_object['api_sig'] = hashed_signature
    signed_object['format'] = "json" # add return format **after** hashing, signature will be invalid otherwise
    return signed_object
