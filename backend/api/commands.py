import sys
from flask import *
import json
import mariadb
import datetime
from . import config
from . import auth_helper
from . import user_helper
from . import api_logger as logger
from . import command_helper
cfg = config.config

command_api = Blueprint('commands', __name__)

@command_api.route('/api/commands/wkartist', methods=['POST'])
def wk_artist():
    try:
        params = request.get_json()
        if auth_helper.is_authenticated(params['username'], params['session_key']):
            result = command_helper.wk_artist(params['query'], params['users'])
            if not result:
                abort(404)
            return jsonify(result)
        else:
            abort(401)
    except mariadb.Error as e:
        logger.log("Database error: " + str(e))
        response = make_response(jsonify(error="A database error occured. Please try again later."), 500)
        abort(response)
    except KeyError as e:
        response = make_response(jsonify(error="Missing required parameter '" + str(e.args[0]) + "'."), 400)
        abort(response)

@command_api.route('/api/commands/wkalbum', methods=['POST'])
def wk_album():
    try:
        params = request.get_json()
        if auth_helper.is_authenticated(params['username'], params['session_key']):
            result = command_helper.wk_album(params['query'], params['users'])
            if result == None:
                abort(404)
            elif result == False:
                abort(400)
            return jsonify(result)
        else:
            abort(401)
    except mariadb.Error as e:
        logger.log("Database error: " + str(e))
        response = make_response(jsonify(error="A database error occured. Please try again later."), 500)
        abort(response)
    except KeyError as e:
        response = make_response(jsonify(error="Missing required parameter '" + str(e.args[0]) + "'."), 400)
        abort(response)

@command_api.route('/api/commands/wktrack', methods=['POST'])
def wk_track():
    try:
        params = request.get_json()
        if auth_helper.is_authenticated(params['username'], params['session_key']):
            result = command_helper.wk_track(params['query'], params['users'])
            if result == None:
                abort(404)
            elif result == False:
                abort(400)
            return jsonify(result)
        else:
            abort(401)
    except mariadb.Error as e:
        logger.log("Database error: " + str(e))
        response = make_response(jsonify(error="A database error occured. Please try again later."), 500)
        abort(response)
    except KeyError as e:
        response = make_response(jsonify(error="Missing required parameter '" + str(e.args[0]) + "'."), 400)
        abort(response)

@command_api.route('/api/commands/nowplaying', methods=['POST'])
def nowplaying():
    try:
        params = request.get_json()
        if auth_helper.is_authenticated(params['username'], params['session_key']):
            result = command_helper.get_nowplaying(params['join_code'])
            return jsonify(result)
        else:
            abort(401)
    except mariadb.Error as e:
        logger.log("Database error: " + str(e))
        response = make_response(jsonify(error="A database error occured. Please try again later."), 500)
        abort(response)
    except KeyError as e:
        response = make_response(jsonify(error="Missing required parameter '" + str(e.args[0]) + "'."), 400)
        abort(response)

@command_api.route('/api/commands/nowplayingdb', methods=['POST'])
def nowplayingdb():
    try:
        params = request.get_json()
        if params:
            try:
                secret_key = params['secret_key']
            except KeyError as e:
                response = make_response(jsonify(error="Missing required parameter: " + str(e.args[0]) + "."), 400)
                abort(response)
        else:
            response = make_response(jsonify(error="Empty JSON body - no data was sent."), 400)
            abort(response)
        if secret_key != cfg['api']['secret']:
            abort(401)
        result = command_helper.nowplaying(database=True)
        if not result:
            abort(500)
        return jsonify({'data': 'success'})
    except mariadb.Error as e:
        logger.log("Database error: " + str(e))
        response = make_response(jsonify(error="A database error occured. Please try again later."), 500)
        abort(response)

@command_api.route('/api/commands/history', methods=['POST'])
def history():
    try:
        params = request.get_json()
        if auth_helper.is_authenticated(params['username'], params['session_key']):
            wk_mode = params['wk_mode']
            if wk_mode == "track":
                result = command_helper.play_history(wk_mode, params['artist_id'], params['users'], params['track'], sort_by=params['sort_by'], sort_order=params['sort_order'], limit=params['limit'], offset=params['offset'])
            elif wk_mode == "album":
                result = command_helper.play_history(wk_mode, params['artist_id'], params['users'], None, params['album_id'], params['sort_by'], sort_order=params['sort_order'], limit=params['limit'], offset=params['offset'])
            elif wk_mode == "artist":
                result = command_helper.play_history(wk_mode, params['artist_id'], params['users'], sort_by=params['sort_by'], sort_order=params['sort_order'], limit=params['limit'], offset=params['offset'])
            elif wk_mode == "overall":
                result = command_helper.play_history(wk_mode, None, params['users'], sort_by=params['sort_by'], sort_order=params['sort_order'], limit=params['limit'], offset=params['offset'])
            else:
                abort(400)
            return jsonify(result)
        else:
            abort(401)
    except mariadb.Error as e:
        logger.log("Database error: " + str(e))
        response = make_response(jsonify(error="A database error occured. Please try again later."), 500)
        abort(response)
    except KeyError as e:
        response = make_response(jsonify(error="Missing required parameter '" + str(e.args[0]) + "'."), 400)
        abort(response)

@command_api.route('/api/commands/wktop', methods=['POST'])
def wk_top():
    try:
        params = request.get_json()
        if auth_helper.is_authenticated(params['username'], params['session_key']):
            if params['wk_mode'] == "artist":
                result = command_helper.wk_top(params['wk_mode'], params['users'], params['artist_id'], params['album_id'], params['track_mode'])
            elif params['wk_mode'] == "album":
                result = command_helper.wk_top(params['wk_mode'], params['users'], params['artist_id'], params['album_id'])
            else:
                abort(409)
            
            if result == None:
                abort(404)
            return jsonify(result)
        else:
            abort(401)
    except mariadb.Error as e:
        logger.log("Database error: " + str(e))
        response = make_response(jsonify(error="A database error occured. Please try again later."), 500)
        abort(response)
    except KeyError as e:
        response = make_response(jsonify(error="Missing required parameter '" + str(e.args[0]) + "'."), 400)
        abort(response)

@command_api.route('/api/commands/scrobble-leaderboard', methods=['POST'])
def leaderboard():
    try:
        params = request.get_json()
        if auth_helper.is_authenticated(params['username'], params['session_key']):
            result = command_helper.scrobble_leaderboard(params['users'], params['start_range'], params['end_range'])
            return jsonify(result)
        else:
            abort(401)
    except mariadb.Error as e:
        logger.log("Database error: " + str(e))
        response = make_response(jsonify(error="A database error occured. Please try again later."), 500)
        abort(response)
    except KeyError as e:
        response = make_response(jsonify(error="Missing required parameter '" + str(e.args[0]) + "'."), 400)
        abort(response)

@command_api.route('/api/commands/wkautocomplete', methods=['POST'])
def wk_autocomplete():
    try:
        params = request.get_json()
        if auth_helper.is_authenticated(params['username'], params['session_key']):
            if params['wk_mode'] in ['track', 'album', 'artist']:
                result = command_helper.wk_autocomplete(params['wk_mode'], params['query'])
                return jsonify(result)
            else:
                abort(400)
        else:
            abort(401)
    except mariadb.Error as e:
        logger.log("Database error: " + str(e))
        response = make_response(jsonify(error="A database error occured. Please try again later."), 500)
        abort(response)
    except KeyError as e:
        response = make_response(jsonify(error="Missing required parameter '" + str(e.args[0]) + "'."), 400)
        abort(response)

@command_api.route('/api/commands/artistredirects', methods=['POST'])
def artist_redirects():
    try:
        params = request.get_json()
        if auth_helper.is_authenticated(params['username'], params['session_key']):
            artist_string = params['artist_string']
        else:
            abort(401)
        response = command_helper.check_artist_redirect(artist_string)
        if response == False:
            return jsonify({'artist': None})
        elif response == None:
            abort(500)
        else:
            return jsonify(response)
    except mariadb.Error as e:
        logger.log("Database error: " + str(e))
        response = make_response(jsonify(error="A database error occured. Please try again later."), 500)
        abort(response)
    except KeyError as e:
        response = make_response(jsonify(error="Missing required parameter '" + str(e.args[0]) + "'."), 400)
        abort(response)

@command_api.route('/api/commands/charts', methods=['POST'])
def charts():
    try:
        params = request.get_json()
        if auth_helper.is_authenticated(params['username'], params['session_key']):
            response = command_helper.charts(params['chart_mode'], params['chart_type'], params['users'], params['start_range'], params['end_range'])
            return jsonify(response)
        else:
            abort(401)
    except mariadb.Error as e:
        logger.log("Database error: " + str(e))
        response = make_response(jsonify(error="A database error occured. Please try again later."), 500)
        abort(response)
    except KeyError as e:
        response = make_response(jsonify(error="Missing required parameter '" + str(e.args[0]) + "'."), 400)
        abort(response)