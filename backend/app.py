import flask
from flask_cors import CORS
import json
import requests
import time

from api.users import user_api
from api.groups import group_api

app = flask.Flask(__name__)
app.config["DEBUG"] = True
app.register_blueprint(user_api)
app.register_blueprint(group_api)
CORS(app)

@app.route('/', methods=['GET'])
def index():
   return flask.jsonify({'data': 'success'})

if __name__ == "__main__":
    app.run()
