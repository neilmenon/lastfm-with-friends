import flask
from flask_cors import CORS
import json
import requests
import time

import api.config as config
from api.users import user_api
from api.groups import group_api
from api.commands import command_api

cfg = config.config

app = flask.Flask(__name__)
app.config["DEBUG"] = True
app.register_blueprint(user_api)
app.register_blueprint(group_api)
app.register_blueprint(command_api)
CORS(app)

@app.route('/', methods=['GET'])
def index():
   return flask.jsonify({'data': 'success'})

if __name__ == "__main__":
   # localhost or server?
   if cfg['server']:
      app.run(host='0.0.0.0')
   else:
    app.run()
