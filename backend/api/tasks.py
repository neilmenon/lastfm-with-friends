from threading import Thread
import time
from flask import *

from . import config
from . import auth_helper
from . import user_helper
from . import api_logger as logger
from . import lastfm_scraper
from . import command_helper
from . import task_helper
from . import group_session_helper
from . import sql_helper
cfg = config.config

task_api = Blueprint('tasks', __name__)

@task_api.route('/api/tasks/globalupdate', methods=['POST'])
def globalupdate():
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
    for u in user_helper.get_users():
        thread = Thread(target=lastfm_scraper.update_user_from_thread, args=(u['username'], full, current_app._get_current_object()))
        thread.start()
        time.sleep(1)
    return jsonify(True)

@task_api.route('/api/tasks/full-scrape-queue', methods=['POST'])
def full_scrape_queue():
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
    response = task_helper.full_scrape_queue()
    return jsonify(response)

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

@task_api.route('/api/tasks/cleanup-artists-albums', methods=['POST'])
def cleanup_artists_albums():
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
    response = task_helper.remove_unused_artists_albums()
    return jsonify(response)

@task_api.route('/api/tasks/demoscrobbler', methods=['POST'])
def demo_scrobbler():
    params = request.get_json()
    if params:
        try:
            secret_key = params['secret_key']
            demo_users = params['demo_users']
        except KeyError as e:
            response = make_response(jsonify(error="Missing required parameter: " + str(e.args[0]) + "."), 400)
            abort(response)
    else:
        response = make_response(jsonify(error="Empty JSON body - no data was sent."), 400)
        abort(response)
    if secret_key != cfg['api']['secret']:
        abort(401)
    
    response = task_helper.insert_demo_scrobbles(demo_users)
    return jsonify(response)

@task_api.route('/api/tasks/app-stats', methods=['POST'])
def app_stats():
    params = request.get_json()
    if params:
        try:
            db_store = params['db_store']
            if db_store:
                secret_key = params['secret_key']
        except KeyError as e:
            response = make_response(jsonify(error="Missing required parameter: " + str(e.args[0]) + "."), 400)
            abort(response)
    else:
        response = make_response(jsonify(error="Empty JSON body - no data was sent."), 400)
        abort(response)
    if db_store and secret_key != cfg['api']['secret']:
        abort(401)
    
    response = task_helper.app_stats(db_store)
    return jsonify(response)

@task_api.route('/api/tasks/group-session-scrobbler', methods=['POST'])
def group_scrobbler():
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
    response = group_session_helper.group_session_scrobbler()
    return jsonify(response)

@task_api.route('/api/tasks/prune-group-sessions', methods=['POST'])
def prune_group_sessions():
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
    response = group_session_helper.prune_sessions()
    return jsonify(response)

@task_api.route('/api/tasks/artist-extra', methods=['POST'])
def artist_extra():
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
    response = lastfm_scraper.scrape_extra_artist_info(full)
    return jsonify(response)

@task_api.route('/api/tasks/artist-images', methods=['POST'])
def artist_images():
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
    lastfm_scraper.scrape_artist_images(full)
    return jsonify(True)

@task_api.route('/api/tasks/personal-stats', methods=['POST'])
def personal_stats():
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
    genres = task_helper.get_popular_genre_filter_list(15)
    personal_stats = []
    for user in user_helper.get_users():
        try:
            personal_stats.append(task_helper.personal_stats(user['username'], genres))
        except Exception as e:
            logger.error("\tAn error occured while trying to generate stat report for {}: {}".format(user['username'], e))

    for data in personal_stats:
        if data:
            sql_helper.execute_db(sql_helper.replace_into("personal_stats", sql_helper.stringify_keys_in_dict(data.copy())), commit=True, pass_on_error=True)
    return jsonify(personal_stats)

@task_api.route('/api/tasks/prune-users', methods=['POST'])
def prune_users():
    params = request.get_json()
    if params:
        try:
            secret_key = params['secret_key']
            dry_run = params['dry_run']
        except KeyError as e:
            response = make_response(jsonify(error="Missing required parameter: " + str(e.args[0]) + "."), 400)
            abort(response)
    else:
        response = make_response(jsonify(error="Empty JSON body - no data was sent."), 400)
        abort(response)
    if secret_key != cfg['api']['secret']:
        abort(401)
    task_helper.prune_inactive_users(dry_run)
    return jsonify(True)