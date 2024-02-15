
import pygame
import xml.etree.ElementTree as ET
from UI.UIImage import UIImage
from UI.UIText import UIText
from UI.UIButton import UIButton

import UI.Chat as Chat

def GetElementByID(id):
    global _uiIds
    if id not in _uiIds:
        return None
    return _uiIds[id]

def Init():
    global _uiObjects
    global _uiIds
    _uiObjects = []
    _uiIds = {}

    tree = ET.parse("Data/UI.xml")
    root = tree.getroot()
    groups = root.find("Group")
    if groups is not None:
        for element in groups.findall("*"):
            img = None
            if element.tag == "Image":
                img = UIImage(element)
            elif element.tag == "Text":
                img = UIText(element)
            elif element.tag == "Button":
                img = UIButton(element)
            if img is not None:
                id = element.get("id")
                if id is not None:
                    _uiIds[id] = img
                _uiObjects.append(img)
    
    Chat.Init()

def ProcessEvent(event):
    global _uiObjects
    if Chat.ProcessEvent(event):
        return True
    for o in reversed(_uiObjects):
        if o.ProcessEvent(event) == True:
            return True
    return False

def Update(deltaTime):
    global _uiObjects
    Chat.Update(deltaTime)
    for o in _uiObjects:
        o.Update(deltaTime)

def Render(screen):
    global _uiObjects
    for o in _uiObjects:
        o.Render(screen)
    Chat.Render(screen)