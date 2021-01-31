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