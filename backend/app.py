from flask import Flask, jsonify, g, request, abort, make_response
from flask_cors import CORS
import mariadb

import api.config as config
from api.users import user_api
from api.groups import group_api
from api.commands import command_api
from api.tasks import task_api
from api.group_sessions import group_session_api
import api.api_logger as logger
from api.task_helper import task_handler
import datetime

cfg = config.config

app = Flask(__name__)
app.config["DEBUG"] = True
app.register_blueprint(user_api)
app.register_blueprint(group_api)
app.register_blueprint(command_api)
app.register_blueprint(task_api)
app.register_blueprint(group_session_api)
CORS(app)

def reset_running_tasks():
   # logger.info("[reset_running_tasks] Resetting any old running tasks...")
   mdb = mariadb.connect(**(cfg['sql']))
   cursor = mdb.cursor(dictionary=True)
   cursor.execute("UPDATE tasks SET last_finished = '{}' WHERE last_finished IS NULL".format(str(datetime.datetime.utcfromtimestamp(1))))
   mdb.commit()
   mdb.close()

@app.teardown_appcontext
def teardown_app(exception):
   # end a task (if the request is a task, such as nowplaying)
   task = g.pop('task', None)
   if task is not None:
      task_handler(task, "end")
   
   # teardown the database connection
   db = g.pop('db', None)
   if db is not None:
      try:
         db.close()
      except mariadb.Error as e:
         logger.warn("DB connection could not be closed successfully: {}".format(e))

@app.before_request
def start_task():
   task_to_start = None
   if "nowplayingdb" in request.url:
      task_to_start = "nowplaying"
   elif "globalupdate" in request.url:
      task_to_start = "globalupdate"
   elif "group-session-scrobbler" in request.url:
      task_to_start = "group-session-scrobbler"
   elif "prune-group-sessions" in request.url:
      task_to_start = "prune-group-sessions"
   
   # start task
   if task_to_start is not None:
      can_run = task_handler(task_to_start, "start")
      if not can_run:
         abort(make_response(jsonify(error="Cannot process this request: task is already running."), 503))
      logger.info("=====> Starting task: {} <=====".format(task_to_start))
      g.task = task_to_start

@app.route('/api', methods=['GET'])
def index():
   return jsonify({'data': 'success'})

# do this outside the Flask app, we do not want uWSGI running this task every time a worker is spawned.
reset_running_tasks()

if __name__ == "__main__":
   # localhost or server?
   if cfg['server']:
      app.run(host='0.0.0.0')
   else:
      app.run()
