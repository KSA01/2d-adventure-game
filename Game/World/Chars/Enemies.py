
import pygame
import numpy as np
from World.Chars.Character import Character
from World.Chars.NPCState import State
import World.WorldCommon as WC

import json
import os

import sys
sys.path.append("../Server")
import Network.mySocket as sck
sys.path.pop()

_id = 0
interval = 0.2

class Enemy(Character):
    def __init__(self, path, element=None):
        global _id

        super().__init__(path, element=element)
        #assigning an id to each enemy initialized for messaging purpose
        self.en = _id
        _id += 1

        if WC.ServerMode:
            self.counter = 0

        self.curState = None
        self.stateList = {}
        if element is not None:
            ai = element.find("AI")
            if ai is not None:
                for state in ai.findall("State"):
                    s = State(state)
                    self.stateList[s.name] = s
                    if self.curState is None:
                        self.curState = s.name
                        s.action.Enter(self)
            self.healthBarName = element.get("healthBar") #retrieves the <enemy> healthBar name in xml related to the <id> of the healthBar image

    #added a del here to properly remove the enemies collision box after death
    def __del__(self):
        super().__del__()
        if self in WC.Enemies:
            WC.Enemies.remove(self)

    def Update(self, deltaTime):
        #gets message for enemy position and sets center position
        #if not WC.ServerMode:
        posmes = sck.GetMessage(f"enPos{self.en}")
        if posmes is not None:
            pos = json.loads(posmes)  
            self.SetCenterPosition((pos["x"], pos["y"]))
        
        if WC.ServerMode: #sever to client
            if self.curState is not None: #server gets here...
                result = self.stateList[self.curState].Update(self, deltaTime)
                if result is not None:
                    self.curState = result
                    self.stateList[self.curState].action.Enter(self)

            #counter so it sends messages every so often not every update call
            self.counter += deltaTime
            if self.counter >= interval:
                #send msg to and local client with enemy pos
                sck.SendMessage(f"enPos{self.en}", json.dumps({'x':self.GetCenterPosition()[0], 'y':self.GetCenterPosition()[1]}))
                sck.SendMessageLocal(f"enPos{self.en}", json.dumps({'x':self.GetCenterPosition()[0], 'y':self.GetCenterPosition()[1]}))
                if self.curState is not None:
                    #sends message to all and local on updating current enemy state
                    sck.SendMessage(f"enAct{self.en}", str(self.curState))
                    sck.SendMessageLocal(f"enAct{self.en}", str(self.curState))
                self.counter = 0        

        if not WC.ServerMode: #client to server
            #get msg
            actMes = sck.GetMessage(f"enAct{self.en}")
            if actMes is not None:
                #msg action = idle
                if actMes == "Idle":
                    self.curState = "Idle"
                    self.stateList[self.curState].action.Enter(self)
                    if self.healthBar is not None:
                        self.healthBar.visible = False
                #msg action = move
                if actMes == "Chase":
                    self.curState = "Chase"
                    self.stateList[self.curState].action.Enter(self)
                    if self.healthBar is not None:
                        self.healthBar.visible = True

                #msg action = health
                '''if actMes[action] == "health":
                    self.health = int(actMes[value])
                    if self.health <= 0:
                        self.healthBar.visible = False'''

            if self.curState != "Chase":
                self.walkChannel.pause()
                
        super().Update(deltaTime)