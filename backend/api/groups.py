import sys
from flask import *
import json
import mariadb
import datetime
import random
import string
from . import config
from . import sql_helper
from . import auth_helper
from . import user_helper
from . import api_logger as logger
from . import command_helper
from . import group_helper
cfg = config.config

group_api = Blueprint('groups', __name__)

@group_api.route('/api/groups', methods=['POST'])
def create():
    try:
        mdb = mariadb.connect(**(cfg['sql']))
        cursor = mdb.cursor(dictionary=True)
        params = request.get_json()
        if params:
            try:
                if not auth_helper.is_authenticated(params['username'], params['session_key']):
                    mdb.close()
                    abort(401)
                join_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
                data = {
                    "name": params['name'],
                    "description": params['description'],
                    "created": str(datetime.datetime.utcnow()),
                    "owner": params['username'],
                    "join_code": join_code
                }
            except KeyError as e:
                mdb.close()
                response = make_response(jsonify(error="Missing required parameter: " + str(e.args[0]) + "."), 400)
                abort(response)
        else:
            mdb.close()
            response = make_response(jsonify(error="Empty JSON body - no data was sent."), 400)
            abort(response)
        sql = sql_helper.insert_into("groups", data)
        cursor.execute(sql)
        mdb.commit()
        mdb.close()
        if cursor.rowcount > 0:
            group_helper.join_group(params['username'], join_code)
            command_helper.nowplaying(join_code, database=True)
            return jsonify(data)
        else:
            response = make_response(jsonify(error="Group with join code "+join_code+" already exists. Randomness has failed."), 409)
            abort(response)
    except mariadb.Error as e:
        logger.log("Database error while creating group: " + str(e))
        response = make_response(jsonify(error="A database error occured. Please try again later."), 500)
        abort(response)

@group_api.route('/api/groups/<string:join_code>/edit', methods=['POST'])
def edit(join_code):
    try:
        params = request.get_json()
        if not auth_helper.is_authenticated(params['username'], params['session_key']):
            abort(401)
        elif not group_helper.get_group(join_code):
            abort(404)
        elif not group_helper.get_group(join_code)['owner'] == params['username']:
            abort(401)
        data = {
            'name': params['name'],
            'description': params['description'],
            'owner': params['owner']
        }
        group_helper.edit_group(join_code, data)
        return group_helper.get_group(join_code)
    except mariadb.Error as e:
        logger.log("Database error while editing group with join code " + join_code + ": " + str(e))
        response = make_response(jsonify(error="A database error occured. Please try again later."), 500)
        abort(response)
    except KeyError as e:
        response = make_response(jsonify(error="Missing required parameter '" + str(e.args[0]) + "'."), 400)
        abort(response)

@group_api.route('/api/groups/<string:join_code>', methods=['POST'])
def get(join_code):
    try:
        params = request.get_json()
        if not auth_helper.is_authenticated(params['username'], params['session_key']):
            abort(401)
        elif not group_helper.get_group(join_code):
            abort(404)
        elif not group_helper.is_in_group(params['username'], join_code):
            abort(401)
        result = group_helper.get_group(join_code)
        if result:
            return jsonify(result)
        else:
            response = make_response(jsonify(error="Group with join code " + join_code + " not found."), 404)
            abort(response)
    except mariadb.Error as e:
        logger.log("Database error while getting group with join code " + join_code + ": " + str(e))
        response = make_response(jsonify(error="A database error occured. Please try again later."), 500)
        abort(response)
    except KeyError as e:
        response = make_response(jsonify(error="Missing required parameter '" + str(e.args[0]) + "'."), 400)
        abort(response)

@group_api.route('/api/groups/join', methods=['POST'])
def join():
    try:
        params = request.get_json()
        if not auth_helper.is_authenticated(params['username'], params['session_key']):
            abort(401)
        elif not group_helper.get_group(params['join_code']):
            abort(404)
        elif group_helper.is_in_group(params['username'], params['join_code']):
            abort(409)
        group_helper.join_group(params['username'], params['join_code'])
        group_data = group_helper.get_group(params['join_code'])
        command_helper.nowplaying(params['join_code'], database=True)
        return jsonify(group_data)
    except mariadb.Error as e:
        logger.log("Database error while joining group " + params['join_code'] + ": " + str(e))
        response = make_response(jsonify(error="A database error occured. Please try again later."), 500)
        abort(response)
    except KeyError as e:
        response = make_response(jsonify(error="Missing required parameter '" + str(e.args[0]) + "'."), 400)
        abort(response)

@group_api.route('/api/groups/<string:join_code>/leave', methods=['POST'])
def leave(join_code):
    try:
        params = request.get_json()
        if not auth_helper.is_authenticated(params['username'], params['session_key']):
            abort(401)
        group_helper.leave_group_or_kick(params['username'], join_code)
        return jsonify({'data': 'success'})
    except mariadb.Error as e:
        logger.log("Database error while getting group with join code " + join_code + ": " + str(e))
        response = make_response(jsonify(error="A database error occured. Please try again later."), 500)
        abort(response)
    except KeyError as e:
        response = make_response(jsonify(error="Missing required parameter '" + str(e.args[0]) + "'."), 400)
        abort(response)

@group_api.route('/api/groups/<string:join_code>/delete', methods=['POST'])
def delete(join_code):
    try:
        params = request.get_json()
        if not auth_helper.is_authenticated(params['username'], params['session_key']) or not group_helper.is_in_group(params['username'], join_code):
            abort(401)
        group_helper.delete_group(join_code)
        return jsonify({'data': 'success'})
    except mariadb.Error as e:
        logger.log("Database error while getting group with join code " + join_code + ": " + str(e))
        response = make_response(jsonify(error="A database error occured. Please try again later."), 500)
        abort(response)
    except KeyError as e:
        response = make_response(jsonify(error="Missing required parameter '" + str(e.args[0]) + "'."), 400)
        abort(response)

@group_api.route('/api/groups/<string:join_code>/kick', methods=['POST'])
def kick(join_code):
    try:
        params = request.get_json()
        if not auth_helper.is_authenticated(params['username'], params['session_key']):
            abort(401)
        elif not group_helper.get_group(join_code):
            abort(404)
        elif not group_helper.get_group(join_code)['owner'] == params['username']:
            abort(401)
        elif group_helper.get_group(join_code)['owner'] == params['user_to_kick']:
            abort(400)
        group_helper.leave_group_or_kick(params['user_to_kick'], join_code)
        return group_helper.get_group(join_code)
    except mariadb.Error as e:
        logger.log("Database error while getting group with join code " + join_code + ": " + str(e))
        response = make_response(jsonify(error="A database error occured. Please try again later."), 500)
        abort(response)
    except KeyError as e:
        response = make_response(jsonify(error="Missing required parameter '" + str(e.args[0]) + "'."), 400)
        abort(response)