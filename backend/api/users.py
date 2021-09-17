import sys
from flask import *
import json
import mariadb
import datetime
from . import config
from . import sql_helper
from . import auth_helper
from . import user_helper
from . import api_logger as logger
from . import lastfm_scraper
from . import command_helper
cfg = config.config

user_api = Blueprint('users', __name__)

@user_api.route('/api/users/authenticate', methods=['POST'])
def auth():
    params = request.get_json()
    if params:
        try:
            token = params['token']
        except KeyError as e:
            response = make_response(jsonify(error="Missing required parameter: " + str(e.args[0]) + "."), 400)
            abort(response)
    else:
        response = make_response(jsonify(error="Empty JSON body - no data was sent."), 400)
        abort(response)
    authenticated_user = auth_helper.get_and_store_session(token)
    if authenticated_user:
        return jsonify(authenticated_user)
    else:
        response = make_response(jsonify(error="Authentication failed. This is most likely due to a Last.fm server error or invalid/used Last.fm token. Please try again."), 401)
        abort(response)

@user_api.route('/api/users/signout', methods=['POST'])
def signout():
    params = request.get_json()
    if params:
        try:
            username = params['username']
            session_key = params['session_key']
        except KeyError as e:
            response = make_response(jsonify(error="Missing required parameter: " + str(e.args[0]) + "."), 400)
            abort(response)
    else:
        response = make_response(jsonify(error="Empty JSON body - no data was sent."), 400)
        abort(response)
    auth_helper.remove_session(username, session_key)
    return jsonify({"success": "Successfully signed out " + username + "."})

@user_api.route('/api/users', methods=['POST'])
def create():
    try:
        mdb = mariadb.connect(**(cfg['sql']))
        cursor = mdb.cursor(dictionary=True)
        params = request.get_json()
        if params:
            try:
                data = {
                    "username": params['username'],
                    "display_name": params['display_name'],
                    "registered": params['registered'],
                    "profile_image": params['profile_image'],
                }
            except KeyError as e:
                response = make_response(jsonify(error="Missing required parameter: " + str(e.args[0]) + "."), 400)
                abort(response)
        else:
            response = make_response(jsonify(error="Empty JSON body - no data was sent."), 400)
            abort(response)
        sql = sql_helper.insert_into_where_not_exists("users", data, "username")
        result = cursor.execute(sql)
        mdb.commit()
        mdb.close()
        if cursor.rowcount > 0:
            return jsonify({"success": "Successfuly created user " + params['username'] +"."})
        else:
            response = make_response(jsonify(error="User "+params['username']+" already exists."), 409)
            abort(response)
    except mariadb.Error as e:
        logger.log("Database error while creating user: " + str(e))
        response = make_response(jsonify(error="A database error occured. Please try again later."), 500)
        abort(response)

@user_api.route('/api/users/<string:username>', methods=['GET'])
def get(username):
    try:
        params = request.args
        result = user_helper.get_user(username, get_session=True)
        if result:
            return jsonify(result)
        else:
            response = make_response(jsonify(error="User " + str(username) + " not found."), 404)
            abort(response)
    except mariadb.Error as e:
        logger.log("Database error while getting user " + username + ": " + str(e))
        response = make_response(jsonify(error="A database error occured. Please try again later."), 500)
        abort(response)
    except KeyError as e:
        response = make_response(jsonify(error="Missing required parameter '" + str(e.args[0]) + "'."), 400)
        abort(response)

@user_api.route('/api/users/update', methods=['POST'])
def update():
    params = request.get_json()
    if params:
        try:
            username = params['username']
            session_key = params['session_key']
            full_scrape = params['full_scrape']
            user_id = params['user_id']
        except KeyError as e:
            response = make_response(jsonify(error="Missing required parameter: " + str(e.args[0]) + "."), 400)
            abort(response)
    else:
        response = make_response(jsonify(error="Empty JSON body - no data was sent."), 400)
        abort(response)
    if not auth_helper.is_authenticated(username, session_key):
        abort(401)
    if full_scrape:
        user_helper.wipe_scrobbles(user_id)
        response = lastfm_scraper.update_user(username, full=True, app=current_app._get_current_object())
    else:
        command_helper.nowplaying(single_user=username)
        response = lastfm_scraper.update_user(username)
    if response:
        return jsonify(response)
    else:
        abort(500)

@user_api.route('/api/users/delete', methods=['POST'])
def delete():
    params = request.get_json()
    if params:
        try:
            username = params['username']
            session_key = params['session_key']
            user_id = params['user_id']
        except KeyError as e:
            response = make_response(jsonify(error="Missing required parameter: " + str(e.args[0]) + "."), 400)
            abort(response)
    else:
        response = make_response(jsonify(error="Empty JSON body - no data was sent."), 400)
        abort(response)
    if not auth_helper.is_authenticated(username, session_key):
        abort(401)
    try:
        result = user_helper.delete_user(user_id, username)
    except Exception:
        abort(500)
    if not result:
        abort(409)
    return jsonify({"data": "success"})

@user_api.route('/api/users/<string:username>/settings', methods=['POST'])
def set_settings(username):
    params = request.get_json()
    if params:
        try:
            session_key = params['session_key']
            settings = params['settings']
        except KeyError as e:
            response = make_response(jsonify(error="Missing required parameter: " + str(e.args[0]) + "."), 400)
            abort(response)
    else:
        response = make_response(jsonify(error="Empty JSON body - no data was sent."), 400)
        abort(response)
    if not auth_helper.is_authenticated(username, session_key):
        abort(401)
    user_helper.set_settings(username, settings)
    return jsonify({"data": "success"})

@user_api.route('/api/demo', methods=['POST'])
def get_demo():
    params = request.get_json()
    if params:
        try:
            username = params['username']
        except KeyError as e:
            abort(401)
    else:
        response = make_response(jsonify(error="Empty JSON body - no data was sent."), 400)
        abort(response)
    if username == cfg['demo_user']:
        result = user_helper.get_demo_user()
        if result:
            return jsonify(result)
        else:
            abort(404)
    else:
        abort(401)