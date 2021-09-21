from flask import *
from . import config
from . import auth_helper
from . import user_helper
from . import api_logger as logger
from . import lastfm_scraper
from . import command_helper
from . import group_session_helper
from . import group_helper
cfg = config.config

group_session_api = Blueprint('group-sessions', __name__)

@group_session_api.route('/api/group-sessions/create', methods=['POST'])
def create():
    params = request.get_json()
    if params:
        try:
            username = params['username']
            session_key = params['session_key']
            group_jc = params['group_jc']
            is_silent = params['is_silent']
            silent_followee = params['silent_followee']
            catch_up_timestamp = params['catch_up_timestamp']
        except KeyError as e:
            response = make_response(jsonify(error="Missing required parameter: " + str(e.args[0]) + "."), 400)
            abort(response)
    else:
        response = make_response(jsonify(error="Empty JSON body - no data was sent."), 400)
        abort(response)
    if not auth_helper.is_authenticated(username, session_key):
        abort(401)
    current_session = group_session_helper.get_current_session(username, with_members=True)
    if current_session: # returns None if not in session
        if current_session['group_jc'] != group_jc: # trying to create session in different group!
            logger.log("{} trying to create session in different group!".format(username))
            if current_session['owner'] == username: # if owner of session, end session
                group_session_helper.end_session(current_session['id'])
            else: # if just member, then leave session
                group_session_helper.leave_session(username, current_session['id'])
        elif current_session['is_silent'] and not is_silent: # if the session is silent (one user silently following another), make non-silent
            logger.log("Silent session was found for session created by {}. Making non-silent...".format(username))
            group_session_helper.make_non_silent(current_session['id'])
            current_session['is_silent'] = False
            return jsonify(current_session)
        else: # return "already in session error"
            response = make_response(jsonify(error="You are already in a session."), 400)
            abort(response)
    else:
        if is_silent:
            current_sessions = group_session_helper.get_sessions(group_jc)
            for s in current_sessions: # check if owner is in another session
                if s['owner'] == silent_followee:
                    response = make_response(jsonify(error="{} has already started a public session. Please join that one.".format(s['owner'])), 400)
                    abort(response)
    if is_silent and (not silent_followee or silent_followee == username):
        response = make_response(jsonify(error="Silent followee must be specified and must not be yourself."), 400)
        abort(response)
    new_session = group_session_helper.create_group_session(username, group_jc, is_silent, silent_followee, catch_up_timestamp)
    return jsonify(new_session)

@group_session_api.route('/api/group-sessions/end', methods=['POST'])
def end():
    params = request.get_json()
    if params:
        try:
            username = params['username']
            session_key = params['session_key']
            session_id = params['session_id']
        except KeyError as e:
            response = make_response(jsonify(error="Missing required parameter: " + str(e.args[0]) + "."), 400)
            abort(response)
    else:
        response = make_response(jsonify(error="Empty JSON body - no data was sent."), 400)
        abort(response)
    if not auth_helper.is_authenticated(username, session_key):
        abort(401)
    current_session = group_session_helper.get_current_session(username)
    if current_session: # returns None if not in session
        if current_session['id'] == session_id and (current_session['owner'] == username or current_session['is_silent']):
            group_session_helper.end_session(session_id)
            return jsonify({"data": "success"})
        elif current_session['id'] != session_id:
            response = make_response(jsonify(error="Session not found."), 404)
            abort(response)
        else:
            response = make_response(jsonify(error="You cannot end a session of which you are not the owner."), 401)
            abort(response)
    abort(400)

@group_session_api.route('/api/group-sessions/leave', methods=['POST'])
def leave():
    params = request.get_json()
    if params:
        try:
            username = params['username']
            session_key = params['session_key']
            session_id = params['session_id']
        except KeyError as e:
            response = make_response(jsonify(error="Missing required parameter: " + str(e.args[0]) + "."), 400)
            abort(response)
    else:
        response = make_response(jsonify(error="Empty JSON body - no data was sent."), 400)
        abort(response)
    if not auth_helper.is_authenticated(username, session_key):
        abort(401)
    current_session = group_session_helper.get_current_session(username)
    if current_session: # returns None if not in session
        if current_session['id'] == session_id and current_session['owner'] != username and not current_session['is_silent']:
            group_session_helper.leave_session(username, session_id)
            return jsonify({"data": "success"})    
        elif current_session['owner'] == username:
            response = make_response(jsonify(error="You cannot leave a session which you created."), 401)
            abort(response)
        elif current_session['is_silent'] and current_session['owner'] != username:
            group_session_helper.end_session(session_id)
            return jsonify({"data": "success"})
    response = make_response(jsonify(error="Session not found."), 404)
    abort(response)

@group_session_api.route('/api/group-sessions/join', methods=['POST'])
def join():
    params = request.get_json()
    if params:
        try:
            username = params['username']
            session_key = params['session_key']
            session_id = params['session_id']
            group_jc = params['group_jc']
            catch_up_timestamp = params['catch_up_timestamp']
        except KeyError as e:
            response = make_response(jsonify(error="Missing required parameter: " + str(e.args[0]) + "."), 400)
            abort(response)
    else:
        response = make_response(jsonify(error="Empty JSON body - no data was sent."), 400)
        abort(response)
    if not auth_helper.is_authenticated(username, session_key):
        abort(401)
    current_session = group_session_helper.get_current_session(username, session_id)
    if current_session: # returns None if not in session
        if current_session['group_jc'] != group_jc: # trying to join session in different group!
            logger.log("{} trying to join session in different group!".format(username))
            if current_session['owner'] == username: # if owner of session, end session
                group_session_helper.end_session(current_session['id'])
            else: # if just member, then leave session
                group_session_helper.leave_session(username, current_session['id'])
        if not current_session['is_silent']:
            if not group_session_helper.is_in_session(username, session_id):
                response = group_session_helper.join_session(username, session_id, catch_up_timestamp)
                return jsonify(response)
            else: 
                response = make_response(jsonify(error="You are already in this session."), 400)
                abort(response)
    response = make_response(jsonify(error="Session not found."), 404)
    abort(response)

@group_session_api.route('/api/group-sessions/list', methods=['POST'])
def sessions_list():
    params = request.get_json()
    if params:
        try:
            username = params['username']
            session_key = params['session_key']
            join_code = params['join_code']
        except KeyError as e:
            response = make_response(jsonify(error="Missing required parameter: " + str(e.args[0]) + "."), 400)
            abort(response)
    else:
        response = make_response(jsonify(error="Empty JSON body - no data was sent."), 400)
        abort(response)
    if not auth_helper.is_authenticated(username, session_key) or not group_helper.is_in_group(username, join_code):
        abort(401)
    response = group_session_helper.get_sessions(join_code)
    return jsonify(response)

