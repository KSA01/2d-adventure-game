
import numpy as np
import math

ScreenSize = np.array([640,480])

PhysicsEngine = None

NewWorldObjects = []
DelWorldOjects = False

Players = [None, None]
MyPlayerIndex = -1
Enemies = []

CameraXY = np.array([0, 0])

TogglePause = False
Paused = True

ServerMode = False

def ComputeDir(src, tgt):
    dir = tgt - src
    dir2 = dir * dir
    len = math.sqrt(np.sum(dir2))
    if len != 0:
       dir /= len
    return dir, len

def MoveDir(char, originalDir, target, speed, deltaTime):
    myPos = char.GetCenterPosition()
    dir, len = ComputeDir(myPos, target)

    if len == 0:
        return False
    
    prod = dir * originalDir
    dotPr = np.sum(prod)
    if dotPr < 0:
        return False
    
    char.SetCenterPosition(myPos + speed * dir * deltaTime)

    return True