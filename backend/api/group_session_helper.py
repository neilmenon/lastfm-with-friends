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

def get_current_session(username=None, session_id=None, with_members=False):
    where_sql = "group_sessions.id = {}".format(session_id) if session_id else "username = '{}'".format(username)
    result = sql_helper.execute_db("SELECT group_sessions.* FROM user_group_sessions LEFT JOIN group_sessions ON user_group_sessions.session_id = group_sessions.id WHERE {}".format(where_sql))
    if len(result):
        session = result[0]
        session['is_silent'] = True if session['is_silent'] else False
    else:
        return None
    if with_members:
        result = sql_helper.execute_db("SELECT user_group_sessions.username, users.profile_image FROM user_group_sessions LEFT JOIN users ON users.username = user_group_sessions.username WHERE session_id = {}".format(session['id']))
        session['members'] = list(filter(lambda x: x['username'] == session['owner'], result)) + list(filter(lambda x: x['username'] != session['owner'], result))
    return session

def create_group_session(initiator, group_jc, is_silent, silent_followee, catch_up_timestamp):
    # create group session
    final_owner = silent_followee if is_silent else initiator
    data = {
        'owner': final_owner,
        'group_jc': group_jc,
        'is_silent': int(is_silent),
        'created': str(datetime.datetime.utcnow())
    }
    sql_helper.execute_db(sql_helper.insert_into("group_sessions", data), commit=True)
    # insert owner into user_group_sessions table
    result = sql_helper.execute_db("SELECT id from group_sessions WHERE owner = '{}'".format(final_owner))
    data = {
        'username': final_owner,
        'session_id': result[0]['id'],
        'last_timestamp': str(int(datetime.datetime.now(tz=datetime.timezone.utc).timestamp()))
    }
    sql_helper.execute_db(sql_helper.insert_into("user_group_sessions", data), commit=True)
    # if is silent mode, insert the initiator into the user_group_sessions table
    if is_silent:
        data = {
            'username': initiator,
            'session_id': result[0]['id'],
            'last_timestamp': str(int(datetime.datetime.now(tz=datetime.timezone.utc).timestamp())) if not catch_up_timestamp else catch_up_timestamp
        }
        sql_helper.execute_db(sql_helper.insert_into("user_group_sessions", data), commit=True)

    # set now playing count status to 1 to make sure it gets checked within two minutes, but not too soon in case the user creates the session and does not start the music immediately
    sql_helper.execute_db("UPDATE now_playing SET check_count = 1 WHERE username = '{}' AND check_count IS NOT NULL".format(final_owner), commit=True)

    # update the user on create so that the prune task doesn't incorrectly end the session immediately.
    lastfm_scraper.update_user(final_owner, stall_if_existing=False)

    return get_current_session(username=initiator, with_members=True)

def end_session(session_id):
    # when session ends, run scrobbler one more time
    group_session_scrobbler(delay=False, session_id=session_id)

    # delete users from user_group_sessions table
    sql_helper.execute_db("DELETE FROM user_group_sessions WHERE session_id = {}".format(session_id), commit=True)
    
    # delete session
    sql_helper.execute_db("DELETE FROM group_sessions WHERE id = {}".format(session_id), commit=True)

def leave_session(username, session_id):

    # give users pending scrobbles before they leave
    group_session_scrobbler(delay=False, session_id=session_id)

    # delete users from user_group_sessions table
    sql_helper.execute_db("DELETE FROM user_group_sessions WHERE session_id = {} AND username = '{}'".format(session_id, username), commit=True)

def join_session(username, session_id, catch_up_timestamp):
    if not catch_up_timestamp:
        session = get_current_session(session_id=session_id)
        # get owner's user_id
        result = sql_helper.execute_db("SELECT user_id FROM users WHERE username = '{}'".format(session['owner']))
        owner_id = result[0]['user_id']

        # update owner so we can properly set update timestamp for joiner
        lastfm_scraper.update_user(session['owner'], stall_if_existing=False)

        # get most recent track's timestamp for owner 
        final_timestamp = str(int(command_helper.play_history("overall", None, [owner_id], None, None, limit=1)['records'][0]['timestamp']) + 1)
    else:
        final_timestamp = catch_up_timestamp

    data = { 
        "username": username, 
        "session_id": session_id,
        'last_timestamp': final_timestamp
    }
    sql_helper.execute_db(sql_helper.insert_into("user_group_sessions", data), commit=True)
    return get_current_session(session_id=session_id, with_members=True)

def is_in_session(username, session_id):
    result = sql_helper.execute_db("SELECT * from user_group_sessions WHERE username = '{}' AND session_id = {}".format(username, session_id))
    return True if len(result) else False

def make_non_silent(session_id):
    sql_helper.execute_db("UPDATE group_sessions SET is_silent = '0' WHERE id = {}".format(session_id), commit=True)

def get_sessions(join_code, get_silent=False):
    silent_sql = " AND is_silent = '0'" if not get_silent else ""
    result = sql_helper.execute_db("SELECT id FROM group_sessions WHERE group_jc = '{}'{}".format(join_code, silent_sql))
    ids = [s['id'] for s in result]
    sessions = []
    for session_id in ids:
        sessions.append(get_current_session(session_id=session_id, with_members=True))
    return sessions

def group_session_scrobbler(delay=True, session_id=None):
    # sleep 30 seconds for purposes of cron tasks
    if delay:
        time.sleep(30)

    logger.info("===== GROUP SESSION SCROBBLER {}=====".format("(ID: {}) ".format(session_id) if session_id else ""))
    
    # get all active sessions
    session_sql = " WHERE id = {}".format(session_id) if session_id else ""
    sessions = sql_helper.execute_db("SELECT * FROM group_sessions{}".format(session_sql))
    if not sessions:
        logger.info("\t No active sessions! All done.")

    # loop through sessions
    for session in sessions:
        logger.info("=====> Syncing scrobbles and now playing for session ID: {} / owner: {}".format(session['id'], session['owner']))
        # get owner's user_id
        result = sql_helper.execute_db("SELECT user_id FROM users WHERE username = '{}'".format(session['owner']))
        owner_id = result[0]['user_id']

        # first, update the owner, whose scrobbles with propagate to other members in the session
        lastfm_scraper.update_user(session['owner'], stall_if_existing=False)

        # get all children of the group session (aka not including owner)
        members = sql_helper.execute_db("SELECT user_group_sessions.username, user_group_sessions.last_timestamp, s.session_key FROM user_group_sessions LEFT JOIN group_sessions ON user_group_sessions.session_id = group_sessions.id LEFT JOIN sessions as s ON s.session_key = ( SELECT session_key from sessions WHERE sessions.username = user_group_sessions.username LIMIT 1 ) WHERE session_id = {} AND user_group_sessions.username != group_sessions.owner".format(session['id']))
        
        # loop through the members
        unix_now = str(int(datetime.datetime.now(tz=datetime.timezone.utc).timestamp()))
        # owner's nowplaying track, if any
        result = sql_helper.execute_db("SELECT * FROM now_playing WHERE username = '{}' AND timestamp = 0".format(session['owner']))
        np_entry = result[0] if len(result) else None
        for member in members:
            logger.info("Syncing {}...".format(member['username']))
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
                    logger.error("\t Error setting now playing status: {}".format(nowplaying_req))

                # manually replace now playing status in database for quicker turnaround on frontend
                # np_entry['username'] = member['username']
                # np_entry['check_count'] = 2 # this is to make sure we don't make an extra call to Last.fm
                # np_entry['artist'] = sql_helper.esc_db(np_entry['artist'])
                # np_entry['track'] = sql_helper.esc_db(np_entry['track'])
                # np_entry['album'] = sql_helper.esc_db(np_entry['album'])
                # logger.info(sql_helper.replace_into("now_playing", np_entry))
                # cursor.execute(sql_helper.replace_into("now_playing", np_entry))
                # mdb.commit()

            # (2) catch up on scrobbles from owner
            play_history = command_helper.play_history("overall", None, [owner_id], str(datetime.datetime.utcfromtimestamp(int(member['last_timestamp']))), str(datetime.datetime.utcfromtimestamp(int(unix_now))))
            if not play_history:
                logger.info("\t No scrobbles to sync at this time.")
                continue
            else:
                # loop through tracks and scrobble them
                if len(play_history['records']) > 0 and len(play_history['records']) < 60:
                    logger.info("\t Scrobbling {} track(s) for {}.".format(len(play_history['records']), member['username']))
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
                            logger.error("\t\t Error scrobbling {} - {}: {}".format(data['artist'], data['track'], scrobble_req))

                    # (3) set update timestamp to timestamp of last scrobbled track + 1 second
                    sql_helper.execute_db("UPDATE user_group_sessions SET last_timestamp = '{}' WHERE username = '{}'".format(int(play_history['records'][0]['timestamp']) + 1, member['username']), commit=True)
                elif len(play_history['records']) >= 60:
                    logger.warn("\t A large amount of scrobbles were set to be scrobbled. These were declined.")
                    # (3) set update timestamp to timestamp of last scrobbled track + 1 second
                    sql_helper.execute_db("UPDATE user_group_sessions SET last_timestamp = '{}' WHERE username = '{}'".format(int(play_history['records'][0]['timestamp']) + 1, member['username']), commit=True)
                else:
                    logger.info("\t No scrobbles to sync at this time.")


def prune_sessions():

    # prune sessions that have gone too long
    logger.info("Checking for any group sessions to kill...")
    result = sql_helper.execute_db("SELECT id FROM group_sessions WHERE created >= now() + INTERVAL 12 HOUR")
    for session in result:
        logger.info("\t Ending session with ID: {} (max limit exceeded)".format(session['id']))
        end_session(session['id'])

    # prune sessions where owner hasn't scrobbled anything in a while
    sessions = sql_helper.execute_db("SELECT id,owner,created FROM group_sessions")
    for session in sessions:
        # first check if session has existed for more than 30 minutes before trying to kill it
        session_created = session['created']
        now = datetime.datetime.utcnow()
        if (now - session_created) >= datetime.timedelta(minutes=30):
            # fetch most recent track by owner. is there anything played within the last 90 minutes?
            result = sql_helper.execute_db("SELECT timestamp FROM track_scrobbles LEFT JOIN users ON users.user_id = track_scrobbles.user_id WHERE users.username = '{}' ORDER BY timestamp DESC LIMIT 1".format(session['owner']))
            timestamp = result[0]['timestamp']
            dt = datetime.datetime.utcfromtimestamp(int(timestamp))
            if (now - dt) >= datetime.timedelta(minutes=90):
                logger.info("\t Ending session with ID: {} (no owner activity in {})".format(session['id'], now - dt))
                end_session(session['id'])

