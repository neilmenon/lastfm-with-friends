from flask import *
from . import config
from . import auth_helper
from . import user_helper
from . import api_logger as logger
from . import lastfm_scraper
from . import command_helper
cfg = config.config

task_api = Blueprint('tasks', __name__)

@task_api.route('/api/tasks/globalupdate', methods=['POST'])
def globalupdate():
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
    for u in user_helper.get_users():
        response = lastfm_scraper.update_user(u['username'])
    lastfm_scraper.scrape_artist_images()
    if response:
        return jsonify(response)
    else:
        abort(500)

@task_api.route('/api/tasks/album', methods=['POST'])
def albumartwork():
    params = request.get_json()
    if params:
        try:
            secret_key = params['secret_key']
            full = params['full']
        except KeyError as e:
            response = make_response(jsonify(error="Missing required parameter: " + str(e.args[0]) + "."), 400)
            abort(response)
    else:
        response = make_response(jsonify(error="Empty JSON body - no data was sent."), 400)
        abort(response)
    if secret_key != cfg['api']['secret']:
        abort(401)
    response = lastfm_scraper.scrape_album_data(full)
    return jsonify(response)