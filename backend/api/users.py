import werkzeug
import sys
from flask import *
import json
import mariadb
from . import config
from . import sql_helper
cfg = config.config

user_api = Blueprint('users', __name__)

mdb = mariadb.connect(**(cfg['sql']))
cursor = mdb.cursor(dictionary=True)

@user_api.route('/api/users', methods=['POST'])
def create():
    try:
        params = request.args
        return "Success"
    except mariadb.Error as e:
        print(f"Error connecting to MariaDB Platform: {e}")
        response = make_response(jsonify(error="Database error: " + str(e)), 500)
        abort(response)
    except KeyError as e:
        response = make_response(jsonify(error="Missing required parameter '" + str(e.args[0]) + "'"), 400)
        abort(response)

@user_api.route('/api/users/<int:user_id>', methods=['GET'])
def get(user_id):
    try:
        params = request.args
        cursor.execute("SELECT * FROM users WHERE user_id = " + str(user_id) + ";")
        result = list(cursor)
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
