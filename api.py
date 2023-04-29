import flask
from flask_cors import CORS, cross_origin
import uuid
from pathlib import Path
import pytz
import json
import argparse
import datetime as dt
from luscioustwitch import *
from viplist import *

class DataStore():
  list_manager : VipListManager = None

data = DataStore()

app = flask.Flask(__name__)
cors = CORS(app)
app.config["CORS_HEADERS"] = 'Content-Type'

@app.route('/api/v1/limit', methods=['GET'])
@cross_origin()
def set_limit():
  if 'Nightbot-Response-Url' not in flask.request.headers:
    return "Command must be sent by NightBot!"
  
  if 'limit' not in flask.request.args:
    return "Missing limit. Try \"!limit <N>\" where <N> is a number."
  
  try:
    limit = int(flask.request.args['limit'])
  except:
    return "Input could not be converted to a number. Try \"!limit <N>\" where <N> is a number."
  
  data.list_manager.set_limit(limit)
  
  return f"Limit set to {limit} VIPs."

@app.route('/api/v1/add', methods=['GET'])
@cross_origin()
def add_vip():
  if 'Nightbot-Response-Url' not in flask.request.headers:
    return "Command must be sent by NightBot!"
  
  if 'user' not in flask.request.args:
    return "Missing the username you intend to VIP."
  
  base_response_url = flask.request.headers['Nightbot-Response-Url']
  new_vip = flask.request.args['user']
  
  (return_code, remove_vip) = data.list_manager.add_vip(new_vip)
  
  if return_code == 1:
    if remove_vip: 
      resp1 = requests.post(url = base_response_url, json = {'message': f'/unvip {remove_vip}'})
    return f"/vip {new_vip}"
  else:
    if return_code == -1:
      return f"Failed to find user \"{new_vip}\"."
    elif return_code == -2:
      return f"@{new_vip} is already a VIP!"
    else:
      return f"Unknown error. Unable to VIP {new_vip}."
  

@app.route('/api/v1/undo', methods=['GET'])
@cross_origin()
def undo_vip():
  if 'Nightbot-Response-Url' not in flask.request.headers:
    return "Command must be sent by NightBot!"
  
  base_response_url = flask.request.headers['Nightbot-Response-Url']
  
  return_code, return_vip, remove_vip = data.list_manager.undo()
  
  if return_code == 1:
    if return_vip:
      resp1 = requests.post(url = base_response_url, json = {'message': f'/vip {return_vip}'})
      print(f'/vip {return_vip}')
    return f"/unvip {remove_vip}"
  else:
    return f"No actions to undo."
  
  

if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument('--host', '-i', default="127.0.0.1", help="API Host IP")
  parser.add_argument('--port', '-p', type=int, default=8080, help="API Port")
  parser.add_argument('--secrets', '-s', default="./secrets.json", help="JSON file with credentials")
  
  args = parser.parse_args()

  with open(args.secrets) as cred_file:
    cred_data = json.load(cred_file)
    data.list_manager = VipListManager(TwitchAPI(cred_data["TWITCH"]))

  app.run(host=args.host, port=args.port, debug=True)