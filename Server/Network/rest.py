#rest.py

from flask import Flask, jsonify, request
from flask import make_response, abort
import os
import Database.database as db
import json
import Game.GameMain as gm

def Init():
    global _app
    _app = Flask(__name__)

    @_app.route('/newgame/<int:id>', methods=['GET'])
    def get_newgame(id=0):
        if id != 0 and id != 1:
            abort(400)
        if id == 0:
            print("Starting new game")
            db.ClearSave()
            db.NewChar("me", json.dumps({"x":320, "y":240}))
            db.NewChar("enemy0", json.dumps({"x":50, "y":350}))
            db.NewChar("enemy1", json.dumps({"x":475, "y":150}))
            gm.NewGame(id, request.remote_addr, 5006)
            return db.GetCharData(id)
        if id == 1:
            print("Joining a game")
            db.NewChar("you", json.dumps({"x":400, "y":340}))
            gm.NewGame(id, request.remote_addr, 5007)
            print(id)
            return db.GetCharData(id)
    
    @_app.route('/loadgame/<int:id>', methods=['GET'])
    def get_loadgame(id=0):
        if id != 0 and id != 1:
            abort(400)
        if id == 0:
            print("Resuming game")
            gm.NewGame(id, request.remote_addr, 5006)
            return db.GetCharData(id)
    
    #rest api save not used anymore
    @_app.route('/savepos/<int:id>', methods=['POST'])
    def set_savepos(id=0):
        print("Saving game")
        if not request.json or not 'x' in request.json or not 'y' in request.json:
            abort(400)
        db.SetCharPos(id, int(request.json['x']), int(request.json['y']))
        return db.GetCharData(id)
    
def Run():
    global _app
    _app.run(port='5005', threaded=True, host="0.0.0.0")
    