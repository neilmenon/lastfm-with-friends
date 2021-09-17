from flask import *
from . import config
from . import auth_helper
from . import user_helper
from . import api_logger as logger
from . import lastfm_scraper
from . import command_helper
from . import group_session_helper
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
    current_session = group_session_helper.get_current_session(username)
    if current_session: # returns None if not in session
        # if the session is silent (one user silently following another), end that session
        if current_session['is_silent'] and not is_silent:
            logger.log("Silent session was found for session created by {}. Ending...".format(username))
            group_session_helper.end_session(current_session['id'])
        else: # return "already in session error"
            response = make_response(jsonify(error="You are already in a session."), 400)
            abort(response)
    if is_silent and (not silent_followee or silent_followee == username):
        response = make_response(jsonify(error="Silent followee must be specified and must not be yourself."), 400)
        abort(response)
    group_session_helper.create_group_session(username, group_jc, is_silent, silent_followee, catch_up_timestamp)
    return jsonify({"data": "success"})

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
        if not current_session['is_silent']:
            if not group_session_helper.is_in_session(username, session_id):
                group_session_helper.join_session(username, session_id, catch_up_timestamp)
                return jsonify({"data": "success"})
            else: 
                response = make_response(jsonify(error="You are already in this session."), 400)
                abort(response)
    response = make_response(jsonify(error="Session not found."), 404)
    abort(response)