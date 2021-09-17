import mariadb
import datetime
import requests
import time
from . import config
from . import sql_helper
from . import api_logger as logger
from . import lastfm_scraper
from . import command_helper
from . import auth_helper
cfg = config.config

def get_current_session(username, session_id=None):
    mdb = mariadb.connect(**(cfg['sql']))
    cursor = mdb.cursor(dictionary=True)
    where_sql = "group_sessions.id = {}".format(session_id) if session_id else "username = '{}'".format(username)
    cursor.execute("SELECT group_sessions.* FROM user_group_sessions LEFT JOIN group_sessions ON user_group_sessions.session_id = group_sessions.id WHERE {}".format(where_sql))
    result = list(cursor)
    mdb.close()
    if len(result):
        ret = result[0]
        ret['is_silent'] = True if ret['is_silent'] else False
        return ret
    return None

def create_group_session(initiator, group_jc, is_silent, silent_followee, catch_up_timestamp):
    mdb = mariadb.connect(**(cfg['sql']))
    cursor = mdb.cursor(dictionary=True)
    # create group session
    final_owner = silent_followee if is_silent else initiator
    data = {
        'owner': final_owner,
        'group_jc': group_jc,
        'is_silent': int(is_silent),
        'created': str(datetime.datetime.utcnow())
    }
    cursor.execute(sql_helper.insert_into("group_sessions", data))
    mdb.commit()
    # insert owner into user_group_sessions table
    cursor.execute("SELECT id from group_sessions WHERE owner = '{}'".format(final_owner))
    result = list(cursor)
    data = {
        'username': final_owner,
        'session_id': result[0]['id'],
        'last_timestamp': str(int(datetime.datetime.now(tz=datetime.timezone.utc).timestamp()))
    }
    cursor.execute(sql_helper.insert_into("user_group_sessions", data))
    mdb.commit()
    # if is silent mode, insert the initiator into the user_group_sessions table
    if is_silent:
        data = {
            'username': initiator,
            'session_id': result[0]['id'],
            'last_timestamp': str(int(datetime.datetime.now(tz=datetime.timezone.utc).timestamp())) if not catch_up_timestamp else catch_up_timestamp
        }
        cursor.execute(sql_helper.insert_into("user_group_sessions", data))
        mdb.commit()
    mdb.close()

def end_session(session_id):
    mdb = mariadb.connect(**(cfg['sql']))
    cursor = mdb.cursor(dictionary=True)
    # delete users from user_group_sessions table
    cursor.execute("DELETE FROM user_group_sessions WHERE session_id = {}".format(session_id))
    mdb.commit()
    # delete session
    cursor.execute("DELETE FROM group_sessions WHERE id = {}".format(session_id))
    mdb.commit()
    mdb.close()

def leave_session(username, session_id):
    mdb = mariadb.connect(**(cfg['sql']))
    cursor = mdb.cursor(dictionary=True)
    # delete users from user_group_sessions table
    cursor.execute("DELETE FROM user_group_sessions WHERE session_id = {} AND username = '{}'".format(session_id, username))
    mdb.commit()
    mdb.close()

def join_session(username, session_id, catch_up_timestamp):
    mdb = mariadb.connect(**(cfg['sql']))
    cursor = mdb.cursor(dictionary=True)
    data = { 
        "username": username, 
        "session_id": session_id,
        'last_timestamp': str(int(datetime.datetime.now(tz=datetime.timezone.utc).timestamp())) if not catch_up_timestamp else catch_up_timestamp
    }
    cursor.execute(sql_helper.insert_into("user_group_sessions", data))
    mdb.commit()
    mdb.close()

def is_in_session(username, session_id):
    mdb = mariadb.connect(**(cfg['sql']))
    cursor = mdb.cursor(dictionary=True)
    cursor.execute("SELECT * from user_group_sessions WHERE username = '{}' AND session_id = {}".format(username, session_id))
    result = list(cursor)
    mdb.close()
    return True if len(result) else False

def group_session_scrobbler():
    # sleep 30 seconds for purposes of cron tasks
    time.sleep(30)

    mdb = mariadb.connect(**(cfg['sql']))
    cursor = mdb.cursor(dictionary=True)
    cursor.execute("SET time_zone='+00:00';")
    logger.log("===== GROUP SESSION SCROBBLER =====")
    
    # get all active sessions
    cursor.execute("SELECT * FROM group_sessions")
    sessions = list(cursor)
    if not sessions:
        logger.log("\t No active sessions! All done.")

    # loop through sessions
    for session in sessions:
        logger.log("=====> Syncing scrobbles and now playing for session ID: {} / owner: {}".format(session['id'], session['owner']))
        # get owner's user_id
        cursor.execute("SELECT user_id FROM users WHERE username = '{}'".format(session['owner']))
        owner_id = list(cursor)[0]['user_id']

        # first, update the owner, whose scrobbles with propagate to other members in the session
        lastfm_scraper.update_user(session['owner'])

        # get all children of the group session (aka not including owner)
        cursor.execute("SELECT user_group_sessions.username, user_group_sessions.last_timestamp, s.session_key FROM user_group_sessions LEFT JOIN group_sessions ON user_group_sessions.session_id = group_sessions.id LEFT JOIN sessions as s ON s.session_key = ( SELECT session_key from sessions WHERE sessions.username = user_group_sessions.username LIMIT 1 ) WHERE session_id = {} AND user_group_sessions.username != group_sessions.owner".format(session['id']))
        members = list(cursor)
        
        # loop through the members
        unix_now = str(int(datetime.datetime.now(tz=datetime.timezone.utc).timestamp()))
        # owner's nowplaying track, if any
        cursor.execute("SELECT artist, track, album FROM now_playing WHERE username = '{}' AND check_count IS NULL".format(session['owner']))
        result = list(cursor)
        np_entry = result[0] if len(result) else None
        for member in members:
            logger.log("Syncing {}...".format(member['username']))
            # (1) update nowplaying status
            if np_entry:
                data = {}
                data['api_key'] = cfg['api']['key']
                data['sk'] = member['session_key']
                data['method'] = 'track.updateNowPlaying'
                data['artist'] = np_entry['artist']
                data['track'] = np_entry['track']
                data['album'] = np_entry['album']
                signed_data = auth_helper.get_signed_object(data)
                try:
                    nowplaying_req = requests.post("https://ws.audioscrobbler.com/2.0", data=signed_data).json()
                    t = nowplaying_req['nowplaying']
                except Exception as e:
                    logger.log("\t Error setting now playing status: {}".format(nowplaying_req))

            # (2) catch up on scrobbles from owner
            play_history = command_helper.play_history("overall", None, [owner_id], str(datetime.datetime.utcfromtimestamp(int(member['last_timestamp']))), str(datetime.datetime.utcfromtimestamp(int(unix_now))))
            if not play_history:
                logger.log("\t No scrobbles to sync at this time.")
                continue
            else:
                # loop through tracks and scrobble them
                logger.log("\t Scrobbling {} track(s) for {}.".format(len(play_history['records']), member['username']))
                for entry in play_history['records']:
                    data = {}
                    data['api_key'] = cfg['api']['key']
                    data['sk'] = member['session_key']
                    data['method'] = 'track.scrobble'
                    data['artist'] = entry['artist']
                    data['track'] = entry['track']
                    data['album'] = entry['album']
                    data['timestamp'] = entry['timestamp']
                    signed_data = auth_helper.get_signed_object(data)
                    try:
                        scrobble_req = requests.post("https://ws.audioscrobbler.com/2.0", data=signed_data).json()
                        t = scrobble_req['scrobbles']
                    except Exception as e:
                        logger.log("\t\t Error scrobbling {} - {}: {}".format(data['artist'], data['track'], scrobble_req))

                # (3) update new timestamp
                cursor.execute("UPDATE user_group_sessions SET last_timestamp = '{}' WHERE username = '{}'".format(unix_now, member['username']))
                mdb.commit()
    mdb.close()

def prune_sessions():
    mdb = mariadb.connect(**(cfg['sql']))
    cursor = mdb.cursor(dictionary=True)

    # prune sessions that have gone too long
    logger.log("Checking for any group sessions to kill...")
    cursor.execute("SELECT id FROM group_sessions WHERE created >= now() + INTERVAL 12 HOUR")
    for session in list(cursor):
        logger.log("\t Ending session with ID: {} (max limit exceeded)".format(session['id']))
        end_session(session['id'])

    # prune sessions where owner hasn't scrobbled anything in a while
    cursor.execute("SELECT id,owner FROM group_sessions")
    sessions = list(cursor)
    for session in sessions:
        cursor.execute("SELECT timestamp FROM track_scrobbles LEFT JOIN users ON users.user_id = track_scrobbles.user_id WHERE users.username = '{}' ORDER BY timestamp DESC".format(session['owner']))
        timestamp = list(cursor)[0]['timestamp']
        dt = datetime.datetime.utcfromtimestamp(int(timestamp))
        now = datetime.datetime.utcnow()
        if (now - dt) >= datetime.timedelta(minutes=20):
            logger.log("\t Ending session with ID: {} (no owner activity in {})".format(session['id'], now - dt))
            end_session(session['id'])

    mdb.close()