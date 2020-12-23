import flask

user_api = flask.Blueprint('users', __name__)

@user_api.route('/api/users')
def users():
    return flask.jsonify("{'users': 0}")