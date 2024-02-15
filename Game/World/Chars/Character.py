
import pygame
import pymunk
import numpy as np

import World.WorldCommon as WC
from World.WorldObject import WorldObject

import UI.UI as UI

import random
import math
from enum import IntEnum

_charWidth = 120
_charHeight = 100
_numImages = 6
_animFrameLen = 0.1667
_initHealth = 10

class AnimType(IntEnum):
    IDLE = 0
    WALK = 1
    ATTACK = 2 # Added 3rd animtype for attack

class AnimDir(IntEnum):
    DOWN = 0
    LEFT = 1
    UP = 2
    RIGHT = 3

class Character(WorldObject):
    @staticmethod
    def _LdChrSrf(path, folder, name, dir):
        surf = WorldObject._loadSurf(path + '/' + folder + "/Char_" + name + "_" + dir + ".png")
        return surf


    def __init__(self, path, element=None):
        global _charWidth
        global _charHeight
        global _numImages
        global _initHealth

        if element is not None:
            path = element.get("path", "")
        base = path
        if path is not None and path != "":
            path += "/Idle/Char_idle_down.png"

        super().__init__(path, element=element, body_type=pymunk.Body.KINEMATIC, col_rect = pygame.Rect((28, 8), (64, 64)), col_type="capsule", frames=_numImages)

        self.moveDir = np.asfarray([0, 1.0])
        if not WC.ServerMode:
            self.area = pygame.Rect((0, 0), (_charWidth, _charHeight))

            # Outer list: AnimType; Inner list: AnimDir
            # Added additional list for attack
            self.anims = [[self.surf, Character._LdChrSrf(base, "Idle", "idle", "left"), Character._LdChrSrf(base, "Idle", "idle", "up"),Character._LdChrSrf(base, "Idle", "idle", "right")], \
                [Character._LdChrSrf(base, "Walk", "walk", "down"), Character._LdChrSrf(base, "Walk", "walk", "left"), Character._LdChrSrf(base, "Walk", "walk", "up"), Character._LdChrSrf(base, "Walk", "walk", "right")], \
                    [Character._LdChrSrf(base, "Attack", "atk", "down"), Character._LdChrSrf(base, "Attack", "atk", "left"), \
                            Character._LdChrSrf(base, "Attack", "atk", "up"),Character._LdChrSrf(base, "Attack", "atk", "right")]]
            self.animDir = AnimDir.DOWN
            self.animType = AnimType.IDLE
            self.animTime = random.uniform(0, _animFrameLen * _numImages)

            self.walkSound = WorldObject._loadSoundEffect("Data/Footsteps-in-grass-fast-www.fesliyanstudios.com.mp3")
            self.walkChannel = self.walkSound.play(loops=-1)
            self.walkChannel.pause()

            #define defaults for healthbar
            self.healthBar = None
            self.healthBarName = None
            self.healthBarWidth = None
            
        self.health = _initHealth

    def __del__(self):
        self.timeToDestruction = 0.01
        self.CharAlive = False
        if not WC.ServerMode:
            self.walkChannel.pause()
        super().__del__()

    def Update(self, deltaTime):
        global _charHeight
        global _charWidth
        global _animFrameLen
        global _numImages

        if not WC.ServerMode:
            self.animTime += deltaTime
            if self.animTime >= _animFrameLen * _numImages:
                self.animTime -= _animFrameLen * _numImages
            frame = self.animTime // _animFrameLen

            self.area = pygame.Rect((frame*_charWidth, 0), (_charWidth, _charHeight))

            #detect if a healthbar is being used
            if self.healthBarName is not None:
                self.healthBar = UI.GetElementByID(self.healthBarName)
            if self.healthBar is not None:
                self.healthBar._CalcRect()
            if self.health != _initHealth and self.healthBar is not None:
                self.healthBar.visible = True

            if math.fabs(self.moveDir[0]) > math.fabs(self.moveDir[1]):
                if self.moveDir[0] > 0:
                    self.animDir = AnimDir.RIGHT
                else:
                    self.animDir = AnimDir.LEFT
            else:
                if self.moveDir[1] > 0:
                    self.animDir = AnimDir.DOWN
                else:
                    self.animDir = AnimDir.UP

        super().Update(deltaTime)

    def Render(self, screen):
        rect = self.rect.copy()
        rect.x += WC.CameraXY[0]
        rect.y += WC.CameraXY[1]
        screen.blit(self.anims[self.animType][self.animDir], rect, self.area)
        #super().Render(screen)

    #alt function to cause the characters death and end the game
    '''def Death(self):
        self.timeToDestruction = 0.01
        self.CharAlive = False
        self.walkChannel.pause()'''
    
    def DetectCol(self):
        result = WC.PhysicsEngine.shape_query(self.shape)
        for r in result:
            points = r.contact_point_set.points
            if len(points) > 0:
                n = r.contact_point_set.normal * points[0].distance
                p = self.GetCenterPosition()
                p += n
                self.SetCenterPosition(p)

    #function to damage the character and lower their healthbar
    def Damaged(self, dmg):
        self.health -= dmg
        '''if self in WC.Enemies:
            print('yes')
            sck.SendMessage(f"enAct{self.en}", json.dumps({'action':'health', 'value':self.health}))
            sck.SendMessageLocal()'''
        #server contols the health
        if WC.ServerMode:
            if self.health <= 0:
                self.__del__()
                self.health = _initHealth
        #client control healthBar according to server
        if not WC.ServerMode:
            if self.health <= 0:
                self.__del__()
            elif self.healthBar is not None:
                self.healthBar.visible = True
                if self.healthBarWidth is None:
                    self.healthBarWidth = self.healthBar.width
                self.healthBar.width = self.healthBarWidth * (float(self.health) / _initHealth)
                self.healthBar._CalcRect()
    