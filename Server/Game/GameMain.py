#GameMain.py

import pygame
import Network.mySocket as sck
import threading
import time
import Database.database as db
import json

import sys
sys.path.append("../Game")
import World.world as World
import World.WorldCommon as WC
sys.path.pop()

_disconnect = True

def GameLoop():
    global _disconnect

    _gTickLastFrame = pygame.time.get_ticks()
    _gDeltaTime = 0.0
    _enemy = None
    
    while True:
        if not (sck.IsConnected(0) or sck.IsConnected(1)):
            _disconnect = True
            World.Cleanup()
            break

        World.Update(_gDeltaTime)

        SavePos(0) # for host player
        SavePos(1) # for second player

        SaveEnPos(0) # for first enemy
        #SaveEnPos(1) # for second enemy
        
        #server sends chat message right back if it recieves it
        ChatMes = sck.GetMessage("SendChatMes")
        if ChatMes is not None:
            sck.SendMessage("ReturnChatMes", str(ChatMes))

        t = pygame.time.get_ticks()
        _gDeltaTime = (t - _gTickLastFrame) / 1000.0
        _gTickLastFrame = t

def NewGameThread(remote_addr, remote_port):
    global _disconnect

    #sends positions of enemies to clients
    enp0 = db.GetCharPos(id=2)
    sck.SendMessage("enPos0", json.dumps({"x":enp0[0], "y":enp0[1]}))
    sck.SendMessageLocal("enPos0", json.dumps({"x":enp0[0], "y":enp0[1]}))
    '''enp1 = db.GetCharPos(id=3)
    sck.SendMessage("enPos1", json.dumps({"x":enp1[0], "y":enp1[1]}))
    sck.SendMessageLocal("enPos1", json.dumps({"x":enp1[0], "y":enp1[1]}))'''
    
    pygame.init()
    World.Init(None, None)

    # listen for client
    sck.Init(True, 0, remote_port, remote_addr)
    while True:
        c = sck.IsConnected(0)
        if c is None:
            _disconnect = True
            return
        #if not isinstance(c, bool):
        if c:
            time.sleep(0.1)
            break

    x, y = db.GetCharPos(0)
    m = {"action":"NewPlayer", "name":"me", "x":x, "y":y}
    sck.SendMessageLocal("world", json.dumps(m))
    sck.SendMessage("world", json.dumps(m), target=0)

    #start game loop
    GameLoop()

def JoinGameThread(remote_addr, remote_port):
    global _disconnect

    # listen for client
    sck.Init(True, 1, remote_port, remote_addr)
    while True:
        c = sck.IsConnected(0)
        if c is None:
            _disconnect = True
            return
        #if not isinstance(c, bool):
        if c:
            time.sleep(0.1)
            break

    print("Connected to second client")

    x, y = db.GetCharPos(1)
    m = {"action":"NewPlayer", "name":"you", "x":x, "y":y}
    sck.SendMessageLocal("world", json.dumps(m))
    sck.SendMessage("world", json.dumps(m), target=0)

    #p = WC.Players[0].GetCenterPosition()
    x, y = db.GetCharPos(0)
    m = {"action":"NewPlayer", "name":"me", "x":x, "y":y}
    sck.SendMessage("world", json.dumps(m), target=1)

def NewGame(id, remote_addr, remote_port):
    global _disconnect

    if id == 0:
        if not _disconnect:
            return 
        _disconnect = False

        t = threading.Thread(target=NewGameThread, args=[remote_addr, remote_port])
        t.start()

        #thread for saving position
        s = threading.Thread(target=SavePos, args=[id])
        s.start()

        #thread for saving enemy position
        e0 = threading.Thread(target=SaveEnPos, args=[0])
        e0.start()
        e1 = threading.Thread(target=SaveEnPos, args=[1])
        e1.start()

        #thread for autosave
        a = threading.Thread(target=AutoSave, args=[id])
        a.start()

    if id == 1:
        if _disconnect or sck.IsConnected(1) != None:
            return
        
        t = threading.Thread(target=JoinGameThread, args=[remote_addr, remote_port])
        t.start()

        #thread for saving position
        s = threading.Thread(target=SavePos, args=[id])
        s.start()

        #thread for saving enemy position
        '''e0 = threading.Thread(target=SaveEnPos, args=[0])
        e0.start()
        e1 = threading.Thread(target=SaveEnPos, args=[1])
        e1.start()'''

        #thread for autosave
        a = threading.Thread(target=AutoSaveJoin, args=[id])
        a.start()

def SavePos(id):
    #retrieve position by message
    if id == 0:
        name = "me"
    elif id == 1:
        name = "you"
    mes = sck.GetMessage(f"savepos{name}")
    if mes is not None:
        pos = json.loads(mes)
        db.SetCharPos(id, int(pos['x']), int(pos['y']))

        retPos = db.GetCharPos(id)
        sck.SendMessage(f"setPos{id}", json.dumps({"id":id, "x":retPos[0], "y":retPos[1]}))
        sck.SendMessageLocal(f"setPos{id}", json.dumps({"id":id, "x":retPos[0], "y":retPos[1]}))

def SaveEnPos(i):
    #retrieve enemies position by message
    mes = sck.GetMessage(f"enPos{i}")
    if mes is not None:
        pos = json.loads(mes)
        id = i + 2
        db.SetCharPos(id, int(pos['x']), int(pos['y']))

        enp = db.GetCharPos(id)
        sck.SendMessage(f"enPos{id}", json.dumps({"x":enp[0], "y":enp[1]}))
        sck.SendMessageLocal(f"enPos{id}", json.dumps({"x":enp[0], "y":enp[1]}))

def AutoSave(id):
    while True:
        SavePos(id)
        #print("Autosaving")
        time.sleep(3)

# For player 2
def AutoSaveJoin(id):
    while True:
        SavePos(id)
        #print("Autosaving")
        time.sleep(3)