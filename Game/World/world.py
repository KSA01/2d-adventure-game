
import pygame
import numpy as np
import math

import pymunk
import pymunk.pygame_util

import xml.etree.cElementTree as ET

import World.WorldCommon as WC
from World.WorldObject import WorldObject
from World.Chars.Player import Player
from World.Chars.Enemies import Enemy

import sys
sys.path.append("../Server")
import Network.mySocket as sck
sys.path.pop()

import os
import json

def Init(screen_size, screen):
    global _grass
    global _worldObjects
    global _draw_options
    global tilesX
    global tilesY
    global imageWidth
    global imageHeight
    
    if screen_size is None:
        WC.ServerMode = True
    else:
        WC.ScreenSize = np.array(screen_size)

    WC.PhysicsEngine = pymunk.Space()
    WC.PhysicsEngine.gravity = 0, 0
    pymunk.pygame_util.positive_y_is_up = False
    if screen is not None:
        _draw_options = pymunk.pygame_util.DrawOptions(screen)

    '''WC.Players[0] = Player("TinyAdventurePack/Character/Char_one")
    WC.Players[0].SetCenterPosition(WC.ScreenSize / 2.0, teleport=True)
    _worldObjects = [WC.Players[0]]'''
    _worldObjects = []

    tree = ET.parse(os.path.dirname(__file__) + "/../Data/WorldData.xml")
    root = tree.getroot() # "World" element

    objects = root.find("Objects")
    if objects is not None:
        for object in objects.findall("Object"):
            wo = WorldObject(None, element=object)
            _worldObjects.append(wo)

    enemies = root.find("Enemies")
    if enemies is not None:
        for enemy in enemies.findall("Enemy"):
            en = Enemy(None, element=enemy)
            _worldObjects.append(en)
            WC.Enemies.append(en)

    if WC.ServerMode:
        WorldObject._loadedImages = {}
    else:
        _grass = pygame.image.load("TinyAdventurePack/Other/grass.png")
        imageWidth, imageHeight = _grass.get_size()
        tilesX = math.ceil(WC.ScreenSize[0] / imageWidth)    #Used math ceiling to round the numbers to a whole number 
        tilesY = math.ceil(WC.ScreenSize[1] / imageHeight)
        _worldObjects.sort(key=_SortWorldObjects)

def ProcessEvent(event):
    global _worldObjects

    for o in _worldObjects:
        if o.ProcessEvent(event) == True:
            return True
        
    return False

def _SortWorldObjects(worldObject):
    box = worldObject.GetCollisionBox()
    return box.y + box.height

'''def SendServerPos():
    return WC.Players[0].GetCenterPosition()'''

_timeStep = 1.0/60.0
_timeSinceLastFrame = 0

def Update(deltaTime):
    global _worldObjects
    global _timeStep
    global _timeSinceLastFrame

    _timeSinceLastFrame += deltaTime
    while _timeSinceLastFrame >= _timeStep:
        WC.PhysicsEngine.step(_timeStep)
        _timeSinceLastFrame -= _timeStep

    if not WC.ServerMode and WC.Players[0] is not None:
        WC.CameraXY = (WC.ScreenSize / 2) - WC.Players[0].GetCenterPosition()

    for o in _worldObjects:
        o.Update(deltaTime)

    if WC.DelWorldOjects:
        for i in range(len(_worldObjects)-1, -1, -1):
            if _worldObjects[i].timeToDestruction == 0:
                del _worldObjects[i]
        WC.DelWorldOjects = False

    for o in _worldObjects:
        o.DetectCol()

    if len(WC.NewWorldObjects) > 0:
        _worldObjects += WC.NewWorldObjects
        WC.NewWorldObjects.clear()

    while True:
        m = sck.GetMessage("world")
        if m is None:
            break
        j = json.loads(m)
        if "action" in j and j["action"] == "NewPlayer":
            if j["name"] == "me":
                p = Player("TinyAdventurePack/Character/Char_one", id="me")
            else:
                p = Player("TinyAdventurePack/Character/Char_two", id="you")
            p.SetCenterPosition(np.array([j["x"], j["y"]]), teleport=True)
            p.id = j["name"]
            if WC.MyPlayerIndex == -1:
                if p.id == "me":
                    WC.Players[0] = p
                else:
                    WC.Players[1] = p
            elif (p.id == "me" and WC.MyPlayerIndex == 0) or (p.id == "you" and WC.MyPlayerIndex == 1):
                WC.Players[0] = p
            else:
                WC.Players[1] = p
            _worldObjects.append(p)
        #TODO: Check for player disconnect message
        #TODO: Check for rock thrown message

    if not WC.ServerMode:
        _worldObjects.sort(key=_SortWorldObjects)

def Render(screen):
    global _grass
    global _worldObjects
    global tilesX
    global tilesY
    global imageHeight
    global imageWidth
    global _draw_options

    for x in range(tilesX):
        for y in range(tilesY):
            screen.blit(_grass, (x * imageWidth, y * imageHeight))

    for o in _worldObjects:
        o.Render(screen)

    #WC.PhysicsEngine.debug_draw(_draw_options) #shows collision 
    
def Cleanup():
    global _worldObjects

    for i in range(len(_worldObjects)-1, -1, -1):
        del _worldObjects[i]
    _worldObjects

    for i in range(len(WC.Players)-1, -1, -1):
        del WC.Players[i]
    WC.Players = [None, None]
