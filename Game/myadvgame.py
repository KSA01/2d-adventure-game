#main.py

import pygame
import threading
import requests
import json
import numpy as np
import time

import sys
sys.path.append("../Server")
import Network.mySocket as sck
sys.path.pop()

pygame.init()  
size = width, height = 640, 480  
screen = pygame.display.set_mode(size)
pygame.mixer.init(frequency=22050, size=16, channels=2, buffer=4096)
pygame.mixer.music.load("Data/bensound-epic.ogg")
pygame.mixer.music.set_volume(0.1)

import World.world as World
World.Init(size, screen)
import World.WorldCommon as WC

import UI.UI as UI
UI.Init()

from UI.UIButton import RegisterButtonAction

#starts game with player at previous position
def LoadPrevGame(id):
    try:
        r = requests.get(url = "http://localhost:5005/loadgame/" + str(id))
        if r.status_code == requests.codes.ok:
            data = r.json()
            #WC.Players[0].SetCenterPosition(np.asfarray([data['x'], data['y']]), teleport=True)
            WC.MyPlayerIndex = id
            sck.Init(False, 0, 5006 + id, '127.0.0.1')
            while True:
                c = sck.IsConnected(0)
                if c is None:
                    print("Error: Failed to connect")
                    break
                if c:
                    break
        else:
            print("Error: Status code: " + str(r.status_code))
    except:
        print("Error: Server probably not running")
    WC.TogglePause = True

#starts new game with player at default position
def StartForRealThisTime(id):
    try:
        r = requests.get(url = "http://localhost:5005/newgame/" + str(id))
        if r.status_code == requests.codes.ok:
            data = r.json()
            #WC.Players[0].SetCenterPosition(np.asfarray([data['x'], data['y']]), teleport=True)
            WC.MyPlayerIndex = id
            sck.Init(False, 0, 5006 + id, '127.0.0.1')
            while True:
                c = sck.IsConnected(0)
                if c is None:
                    print("Error: Failed to connect")
                    break
                if c:
                    break
        else:
            print("Error: Status code: " + str(r.status_code))
    except:
        print("Error: Server probably not running")
    WC.TogglePause = True

#function that starts the game by threading a function that load previous game position
def LoadGame(id):
    for b in ["startButton", "volume-", "volume+", "newgame", "loadgame", "joinButton"]:
        button = UI.GetElementByID(b)
        if button:
            button.visible = False
    t = threading.Thread(target=LoadPrevGame, args=[id])
    t.daemon = True
    t.start()
    #a = threading.Thread(target=AutoSave)   # Old auto save
    #a.start()

#function starts the game by threading a function that starts a new game
def StartGame(id):
    for b in ["startButton", "volume-", "volume+", "newgame", "loadgame", "joinButton"]:
        button = UI.GetElementByID(b)
        if button:
            button.visible = False
    t = threading.Thread(target=StartForRealThisTime, args=[id])
    t.daemon = True
    t.start()
    #a = threading.Thread(target=AutoSave)  # Old auto save
    #a.start()

#saves the players position every 3 seconds
'''def AutoSave():
    while True:
        if not WC.Paused:
            savePos = WC.Players[0].GetCenterPosition()
            r = requests.post(url = "http://localhost:5005/savepos/0", json={
                "x": savePos[0],
                "y": savePos[1]
            })
            if r.status_code == requests.codes.ok:
                #print(f"Status Code: {r.status_code}, Response: {r.json()}")
                print("Game Position Saved")
            else:
                print("Save Failed")
        time.sleep(3)'''

#when newgame button is clicked it calls StartGame func
RegisterButtonAction("NewGame", lambda: StartGame(0))
#when loadgame button is clicked it calls loadgame func
RegisterButtonAction("LoadGame", lambda: LoadGame(0))
#when joingame button is clicked in join player 2
RegisterButtonAction("JoinGame", lambda: StartGame(1))


def VolumeUp():
    volume = pygame.mixer.music.get_volume()
    if volume < 1:
        volume += 0.1
        if volume > 1:
            volume = 1
        pygame.mixer.music.set_volume(volume)
        SaveSettings()

RegisterButtonAction("Volume+", VolumeUp)

def VolumeDown():
    volume = pygame.mixer.music.get_volume()
    if volume > 0:
        volume -= 0.1
        if volume < 0:
            volume = 0.0
        pygame.mixer.music.set_volume(volume)
        SaveSettings()

RegisterButtonAction("Volume-", VolumeDown)

pygame.mixer.music.play(loops=-1)

try:
    with open("SettingsFile.txt", 'r') as setFile:
        for line in setFile:
            if line.startswith("volume "):
                try:
                    volume = float(line[7:])
                    if volume > 1:
                        volume = 1
                    if volume < 0:
                        volume = 0
                    pygame.mixer.music.set_volume(volume)
                except:
                    pass
                continue

            if line.startswith("END\n"):
                break
except:
    pass

SettingsFile = open('SettingsFile.txt', 'w')
def SaveSettings():
    volume = pygame.mixer.music.get_volume()
    SettingsFile.write("volume " + str(volume) + "\n")
    SettingsFile.write("END\n")
    SettingsFile.flush()
    SettingsFile.seek(0,0)
SaveSettings()

def Update(deltaTime):
    if WC.TogglePause:
        WC.Paused = not WC.Paused
        WC.TogglePause = False

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            return False
        if UI.ProcessEvent(event) == True:
            continue
        if WC.Paused:
            continue
        if World.ProcessEvent(event) == True:
            continue
        
    if not WC.Paused:
        World.Update(deltaTime)
    UI.Update(deltaTime)

    return True

def Render(screen):
    screen.fill((0, 0, 0))

    World.Render(screen)
    UI.Render(screen)

    pygame.display.flip()

# Main loop
_gTicksLastFrame = pygame.time.get_ticks()
_gDeltaTime = 0.0
running = True

#while Update(_gDeltaTime):
while running:
    running = Update(_gDeltaTime)
    Render(screen)

    t = pygame.time.get_ticks()
    _gDeltaTime = (t - _gTicksLastFrame) / 1000.0
    _gTicksLastFrame = t

SettingsFile.close()
World.Cleanup()
pygame.quit()   # Added to properly close window with close button again
sys.exit()