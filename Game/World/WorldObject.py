
import pygame
import pymunk
import numpy as np

import World.WorldCommon as WC

import os

class WorldObject():
    _loadedImages = {}
    _loadedSoundEffects = {}

    @staticmethod
    def _loadSoundEffect(path):
        if path in WorldObject._loadedSoundEffects:
            return WorldObject._loadedSoundEffects[path]
        
        try:
            sound = pygame.mixer.Sound(path)
            if sound is None:
                return None
        except:
            return None
        
        WorldObject._loadedSoundEffects[path] = sound
        return sound

    @staticmethod
    def _loadSurf(path):
        key = os.path.dirname(__file__) + "/../" + path
        if key in WorldObject._loadedImages:
            return WorldObject._loadedImages[key]
        
        try:
            surf = pygame.image.load(key)
            if surf is None:
                return None
        except:
            return None
        
        WorldObject._loadedImages[key] = surf
        return surf

    def __init__(self, path, element=None, body_type=pymunk.Body.STATIC, col_rect=None, col_type="box", frames=1, rock=False):
        self.body = None
        self.path = path if path is not None or element is None else element.get("path")
        self.surf = WorldObject._loadSurf(self.path)
        self.size = np.asfarray([self.surf.get_width() / frames, self.surf.get_height()])
        self.pos = np.asfarray([0,0])
        self.rock = rock
        self.cooldown = 0

        if WC.ServerMode:
            self.surf = None

        if element is not None:
            self.SetCenterPosition(np.asfarray([float(element.get("x",0)), float(element.get("y",0))]))

        self.rect = pygame.Rect(self.pos, self.size)

        self.col_type = col_type
        self.col_rect = col_rect if col_rect is not None else pygame.Rect((0, 0), self.size)
        if element is not None:
            col_elem = element.find("Col")
            if col_elem is not None:
                self.col_rect = pygame.Rect((int(col_elem.get("xoff")), int(col_elem.get("yoff"))), (int(col_elem.get("w")), int(col_elem.get("h"))))
                self.col_type = col_elem.get("type")

        mass = 10
        moment = 10

        self.body = pymunk.Body(mass, moment, body_type)
        center = self.GetCollisionBoxCenter()
        self.body.position = center[0], center[1]
        WC.PhysicsEngine.reindex_shapes_for_body(self.body) #rule: physics engine knows to update properly
        box = self.GetCollisionBox()

        w, h = box.width, box.height
        if self.col_type == "box":
            self.shape = pymunk.Poly.create_box(self.body, box.size)
        elif self.col_type == "oval":
            #creates an oval by plotting many points to create
            self.shape = pymunk.Poly(self.body, [(0, -h/2), (w*0.3, -h*0.45), (w*0.4, -h*0.4), (w*0.45, -h*0.3), \
                                                 (w/2, 0), (w*0.45, h*0.3), (w*0.4, h*0.4), (w*0.3, h*0.45), \
                                                    (0, h/2), (-w*0.3, h*0.45), (-w*0.4, h*0.4), (-w*0.45, h*0.3), \
                                                        (-w/2, 0), (-w*0.45, -h*0.3), (-w*0.4, -h*0.4), (-w*0.3, -h*0.45)])
        elif self.col_type == "capsule":
            #creates a capsule by plotting many points to create a rectangle with to hemispheres, on top and bottom
            self.shape = pymunk.Poly(self.body, [(0, -h/2), (w*0.2, -h*0.48), (w*0.32, -h*0.42), (w*0.4, -h*0.35), (w*0.48, -h*0.24), \
                                                 (w/2, -h/4), (w/2, h/4), (w*0.48, h*0.24), (w*0.4, h*0.35), (w*0.32, h*0.42), (w*0.2, h*0.48), \
                                                    (0, h/2), (-w*0.2, h*0.48), (-w*0.32, h*0.42), (-w*0.4, h*0.35), (-w*0.48, h*0.24), \
                                                        (-w/2, h/4), (-w/2, -h/4), (-w/2, -h/4), (-w*0.48, -h*0.24), (-w*0.4, -h*0.35), (-w*0.32, -h*0.42), (-w*0.2, -h*0.48)])


        WC.PhysicsEngine.add(self.body, self.shape)

        self.timeToDestruction = -1

    def __del__(self):
        if self.body is not None:
            WC.PhysicsEngine.remove(self.shape, self.body)

    def SetCenterPosition(self, pos, teleport=False):
        self.pos = pos - (self.size / 2.0)

        if teleport:
            self.rect.x = self.pos[0]
            self.rect.y = self.pos[1]

        if self.body is not None:
            center = self.GetCollisionBoxCenter()
            self.body.position = center[0], center[1]
            WC.PhysicsEngine.reindex_shapes_for_body(self.body)

    def GetCenterPosition(self):
        return self.pos + (self.size / 2.0)
    
    def GetCollisionBox(self):
        return pygame.Rect(self.pos + np.asfarray(self.col_rect.topleft), self.col_rect.size)
    
    def GetCollisionBoxCenter(self):
        box = self.GetCollisionBox()
        return np.asfarray([box.x + (box.w / 2), box.y + (box.h / 2)])
    
    def ProcessEvent(self, event):
        return False

    def Update(self, deltaTime):
        if self.body.body_type == pymunk.Body.DYNAMIC:
            center = self.GetCollisionBoxCenter()
            self.pos[0] = self.body.position[0] - (center[0] - self.pos[0])
            self.pos[1] = self.body.position[1] - (center[1] - self.pos[1])

        self.rect.x = self.pos[0]
        self.rect.y = self.pos[1]

        if self.timeToDestruction != -1:
            self.timeToDestruction -= deltaTime
            if self.timeToDestruction <= 0:
                self.timeToDestruction = 0
                WC.DelWorldOjects = True
        
        if self.cooldown > 0:
            self.cooldown -= 1

    #passes to function in Character
    '''def Damaged(self, dmg):
        pass'''

    def DetectCol(self):
        if self.rock:
            #feature for enemy death by rock
            for en in WC.Enemies:
                if len(self.shape.shapes_collide(en.shape).points) > 0 and self.cooldown <= 0:
                    en.Damaged(2)
                    self.cooldown = 60
                    self.timeToDestruction = 0.01
                    #print("You have damaged an enemy")

    def Render(self, screen):
        rect = self.rect.copy()
        rect.x += WC.CameraXY[0]
        rect.y += WC.CameraXY[1]
        screen.blit(self.surf, rect)
