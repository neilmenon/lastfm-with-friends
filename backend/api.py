import flask
from flask_cors import CORS
import json
import requests
import time

app = flask.Flask(__name__)
app.config["DEBUG"] = True
CORS(app)

@app.route('/', methods=['GET'])
def index():
   return flask.jsonify({'data': 'success'})

app.run()