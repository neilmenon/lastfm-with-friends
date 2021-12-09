from flask import Flask, jsonify, g
from flask_cors import CORS

import api.config as config
from api.users import user_api
from api.groups import group_api
from api.commands import command_api
from api.tasks import task_api
from api.group_sessions import group_session_api

cfg = config.config

app = Flask(__name__)
app.config["DEBUG"] = True
app.register_blueprint(user_api)
app.register_blueprint(group_api)
app.register_blueprint(command_api)
app.register_blueprint(task_api)
app.register_blueprint(group_session_api)
CORS(app)

@app.teardown_appcontext
def teardown_db():
   db = g.pop('db', None)
   if db is not None:
      db.close()

@app.route('/api', methods=['GET'])
def index():
   return jsonify({'data': 'success'})

if __name__ == "__main__":
   # localhost or server?
   if cfg['server']:
      app.run(host='0.0.0.0')
   else:
    app.run()
