import sys
from flask import *
import json
import mariadb
import datetime
from . import config
from . import sql_helper
cfg = config.config

user_api = Blueprint('users', __name__)


@user_api.route('/api/users', methods=['POST'])
def create():
    try:
        mdb = mariadb.connect(**(cfg['sql']))
        cursor = mdb.cursor(dictionary=True)
        params = request.get_json()
        data = {
            "username": params['username'],
            "display_name": params['display_name'],
            "registered": params['registered'],
            "profile_image": params['profile_image'],
        }
        sql = sql_helper.insert_into_where_not_exists("users", data, "username")
        # return sql
        result = cursor.execute(sql)
        mdb.commit()
        mdb.close()
        if cursor.rowcount > 0:
            return jsonify({"success": "Successfuly created user " + params['username'] +"."})
        else:
            response = make_response(jsonify(error="User already exists."), 400)
            abort(response)
    except mariadb.Error as e:
        print(f"Error connecting to MariaDB Platform: {e}")
        response = make_response(jsonify(error="Database error: " + str(e)), 500)
        abort(response)
    except KeyError as e:
        response = make_response(jsonify(error="Missing required parameter: " + str(e.args[0]) + "."), 400)
        abort(response)

@user_api.route('/api/users/<int:user_id>', methods=['GET'])
def get(user_id):
    try:
        mdb = mariadb.connect(**(cfg['sql']))
        cursor = mdb.cursor(dictionary=True)
        params = request.args
        cursor.execute("SELECT * FROM users WHERE user_id = " + str(user_id) + ";")
        result = list(cursor)
        mdb.close()
        if result:
            return jsonify(result[0])
        else:
            response = make_response(jsonify(error="User with ID " + str(user_id) + " not found."), 404)
            abort(response)
    except mariadb.Error as e:
        print(f"Error connecting to MariaDB Platform: {e}")
        response = make_response(jsonify(error="Database error: " + str(e)), 500)
        abort(response)
    except KeyError as e:
        response = make_response(jsonify(error="Missing required parameter '" + str(e.args[0]) + "'."), 400)
        abort(response)
