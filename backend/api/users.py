import sys
from flask import *
import json
import mariadb
import datetime
from . import config
from . import sql_helper
from . import auth_helper
from . import api_logger as logger
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
        mdb = mariadb.connect(**(cfg['sql']))
        cursor = mdb.cursor(dictionary=True)
        params = request.args
        cursor.execute("SELECT * FROM users WHERE username = '" + str(username) + "';")
        result = list(cursor)
        mdb.close()
        if result:
            return jsonify(result[0])
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
