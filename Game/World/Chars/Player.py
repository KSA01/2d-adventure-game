
import pygame
import numpy as np

import World.WorldCommon as WC
from World.Chars.Character import Character, AnimType

import pymunk
from pymunk.vec2d import Vec2d
from World.WorldObject import WorldObject

import json
import os

import UI.UI as UI

import sys
sys.path.append("../Server")
import Network.mySocket as sck
sys.path.pop()

class Player(Character):
    def __init__(self, path, id):
        super().__init__(path)
        self.speed = 200.0
        self.mousemove = False
        self.vel = np.zeros(2)
        self.press = False
        self.CharAlive = True
        self.attk = False
        if id == "me":
            self.healthBarName = "P1"
        else:
            self.healthBarName = "P2"
        self.cooldown = 0
        self.atkCooldown = 0
        self.deadToggle = False
        self.sendCounter = 0
        self.saveCounter = 0
        self.setCounter = 0
        self.id = id
        if not WC.ServerMode:
            self.walkChannel.pause()

    def ProcessEvent(self, event):
        if not ((self.id == "me" and WC.MyPlayerIndex == 0) or (self.id == "you" and WC.MyPlayerIndex == 1)):
            return False

        if event.type == pygame.MOUSEBUTTONDOWN:
            left, middle, right = pygame.mouse.get_pressed()

            if left:
                self.mouseTarget = np.asfarray(pygame.mouse.get_pos()) - WC.CameraXY
                self.moveDir, len = WC.ComputeDir(self.GetCenterPosition(), self.mouseTarget)
                self.mousemove = True if len != 0 else False
                #sck.SendMessage(f"savepos{self.id}", json.dumps({"id":self.id, "x":self.GetCenterPosition()[0], "y":self.GetCenterPosition()[1]}))
                #sck.SendMessageLocal(f"savepos{self.id}", json.dumps({"id":self.id, "x":self.GetCenterPosition()[0], "y":self.GetCenterPosition()[1]}))
                self.press = False
                self.rock = False
                return True
    
        if event.type == pygame.KEYUP and event.key == pygame.K_SPACE:
            sck.SendMessage("me", "shoot")
            sck.SendMessageLocal("action", "shoot")
            rock = WorldObject("TinyAdventurePack/Other/SmallRock.png", body_type=pymunk.Body.DYNAMIC, rock=True)
            rock.shape.friction = 0
            rock.SetCenterPosition(self.GetCenterPosition() + (self.moveDir * 60))
            dir = Vec2d(self.moveDir[0], self.moveDir[1])
            rock.body.apply_impulse_at_world_point(dir * 2500.0, rock.body.position)
            rock.timeToDestruction = 2.0
            WC.NewWorldObjects.append(rock)
            self.rock = True
            self.press = False
            self.atkCooldown = 1.0
            return True

        #input for key movement
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT or event.key == pygame.K_a:
                self.vel[0] = -self.speed
                self.moveDir[0] = -self.speed
                self.moveDir[1] = 0
                self.press = True
                self.rock = False #stop attack animation when you move again
                return True
            elif event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                self.vel[0] = self.speed
                self.moveDir[0] = self.speed
                self.moveDir[1] = 0
                self.press = True
                self.rock = False
                return True
            elif event.key == pygame.K_UP or event.key == pygame.K_w:
                self.vel[1] = -self.speed
                self.moveDir[1] = -self.speed
                self.moveDir[0] = 0
                self.press = True
                self.rock = False
                return True
            elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                self.vel[1] = self.speed
                self.moveDir[1] = self.speed
                self.moveDir[0] = 0
                self.press = True
                self.rock = False
                return True

        #stop key movement
        if event.type == pygame.KEYUP:
            if event.key in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_a, pygame.K_d):
                self.vel[0] = 0
                self.press = False
            elif event.key in (pygame.K_UP, pygame.K_DOWN, pygame.K_w, pygame.K_s):
                self.vel[1] = 0
                self.press = False
            
            #sck.SendMessage(f"savepos{self.id}", json.dumps({"id":self.id, "x":self.GetCenterPosition()[0], "y":self.GetCenterPosition()[1]}))
            #sck.SendMessageLocal(f"savepos{self.id}", json.dumps({"id":self.id, "x":self.GetCenterPosition()[0], "y":self.GetCenterPosition()[1]}))
             
        return False

    def Update(self, deltaTime):
        if not WC.ServerMode:
            while True:
                m = sck.GetMessage("action")
                if m is None:
                    break
                elif m == "shoot":
                    #moved rock to update for server and clients
                    rock = WorldObject("TinyAdventurePack/Other/SmallRock.png", body_type=pymunk.Body.DYNAMIC, rock=True)
                    rock.shape.friction = 0
                    rock.SetCenterPosition(self.GetCenterPosition() + (self.moveDir * 60))
                    dir = Vec2d(self.moveDir[0], self.moveDir[1])
                    rock.body.apply_impulse_at_world_point(dir * 2500.0, rock.body.position)
                    rock.timeToDestruction = 2.0
                    WC.NewWorldObjects.append(rock)
                    self.rock = True
                    self.press = False
                    self.atkCooldown = 1.0
                if m is not None:
                    print("Action: " + m)
                break

            #checks for a save player position message
            self.setCounter += deltaTime
            if self.setCounter >= 0.5:
                posmes = sck.GetMessage(f"setPos{self.id}")
                if posmes is not None:
                    for pl in WC.Players:
                        pos = json.loads(posmes)
                        if pl and pl.id == pos["id"]:
                            self.SetCenterPosition((pos["x"], pos["y"]))
                            self.setCounter = 0

        if self.mousemove:
            self.mousemove = WC.MoveDir(self, self.moveDir, self.mouseTarget, self.speed, deltaTime)
            if not WC.ServerMode:
                self.animType = AnimType.WALK
                self.walkChannel.unpause()
        elif self.press:
            self.moveDir /= np.linalg.norm(self.moveDir)
            if not WC.ServerMode:
                self.animType = AnimType.WALK
                self.walkChannel.unpause()
                pos = self.GetCenterPosition() + self.vel * deltaTime #update position
                self.SetCenterPosition(pos)
        else:
            if not WC.ServerMode:
                self.animType = AnimType.IDLE
                self.walkChannel.pause()

        if not WC.ServerMode:
            self.sendCounter += deltaTime
            if self.sendCounter >= 0.4:
                sck.SendMessage(f"savepos{self.id}", json.dumps({"id":self.id, "x":self.GetCenterPosition()[0], "y":self.GetCenterPosition()[1]}))
                sck.SendMessageLocal(f"savepos{self.id}", json.dumps({"id":self.id, "x":self.GetCenterPosition()[0], "y":self.GetCenterPosition()[1]}))
                self.sendCounter = 0

        #change annimation type to attack when rock thrown
        if self.rock:
            if self.atkCooldown > 0:
                self.animType = AnimType.ATTACK

        #cooldown decrement for player
        if self.cooldown > 0:
            self.cooldown -= 1

        #cooldown for attack anim
        if self.atkCooldown > 0:
            self.atkCooldown -= deltaTime

        super().Update(deltaTime)

    #feature for player death
    def DetectCol(self):
        super().DetectCol()
        for en in WC.Enemies:
            pts = self.shape.shapes_collide(en.shape).points
            if len(pts) > 0 and self.cooldown <= 0:
                self.Damaged(2)
                self.cooldown = 360
                #print("You are taking damage")

    def Render(self, screen):
        if self.CharAlive:
            super().Render(screen)
        elif not self.deadToggle:
            print("Player 1 has died")
            self.deadToggle = True

    