
import pygame
import numpy as np
import World.WorldCommon as WC
from UI.UIText import UIText

_ButtonActions = {}

def RegisterButtonAction(name, callback):
    _ButtonActions[name] = callback

class UIButton(UIText):
    def __init__(self, element=None):
        if element is not None:
            super().__init__(element)

            btn_el = element.find("Action")
            if btn_el is not None:
                self.action = btn_el.get("onClick", "")
                pressed_path = btn_el.get("pressed", None)

                if pressed_path is None:
                    self.pressed_surf = None
                else:
                    try:
                        self.pressed_surf = pygame.image.load(pressed_path)
                    except:
                        self.pressed_surf = None
                    if self.pressed_surf is not None:
                        self.pressed_surf = pygame.transform.scale(self.pressed_surf, (self.width, self.height))

                self.normal_surf = self.surf
                self.pressed = False

    def ProcessEvent(self, event):
        global _ButtonActions

        if not self.visible:
            return False
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            left, middle, right = pygame.mouse.get_pressed()
            pos = pygame.mouse.get_pos()
            if left == True and self.rect.collidepoint(pos):
                self.pressed = True
                return True
        elif self.pressed and event.type == pygame.MOUSEBUTTONUP:
            left, middle, right = pygame.mouse.get_pressed()
            if left == False:
                self.pressed = False
                pos = pygame.mouse.get_pos()
                if self.rect.collidepoint(pos) and self.action in _ButtonActions:
                    _ButtonActions[self.action]()
                    return True

        return False
    
    def Update(self, deltaTime):
        super().Update(deltaTime)

    def Render(self, screen):
        if self.visible:
            if self.pressed:
                self.surf = self.pressed_surf
            else:
                self.surf = self.normal_surf
            super().Render(screen)