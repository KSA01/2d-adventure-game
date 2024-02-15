
import pygame
import numpy as np
import World.WorldCommon as WC

class UIImage():
    def __init__(self, element=None):
        if element is not None:
            self.id = element.get("id", None)
            self.path = element.get("path", None)
            self.surf = pygame.image.load(self.path) if self.path is not None else None
            self.x = int(element.get("x", 0))
            self.y = int(element.get("y", 0))
            self.width = int(element.get("width", 0))
            self.height = int(element.get("height", 0))
            if self.surf is not None:
                if self.width > 0 and self.height > 0:
                    self.surf = pygame.transform.scale(self.surf, (self.width, self.height))
                else:
                    self.width = self.surf.get_width()
                    self.height = self.surf.get_height()
            self.rect = pygame.Rect((self.x, self.y), (self.width, self.height))

            #so that it sets the width of the healthBar to this area as the area shortens
            self.area = pygame.Rect((0, 0), (self.width, self.height))

            self.justify = element.get("justify", "left")
            self.vjustify = element.get("vjustify", "top")
            v = element.get("visible", False)
            self.visible = v == "true"

            anchor = element.find("Anchor")
            if anchor is not None:
                self.anchorX = float(anchor.get("x", 0))
                self.anchorY = float(anchor.get("y", 0))
            else:
                self.anchorX = 0
                self.anchorY = 0

        self._CalcRect()

    def _CalcRect(self):
        self.rect.left = self.x + self.anchorX * WC.ScreenSize[0]
        if self.justify == "right":
            self.rect.left -= self.width
        elif self.justify == "center":
            self.rect.left -= self.width // 2

        self.rect.top = self.y + self.anchorY * WC.ScreenSize[1]
        if self.vjustify == "bottom":
            self.rect.top -= self.height
        elif self.vjustify == "center":
            self.rect.top -= self.height // 2

        self.rect.width = self.width
        self.rect.height = self.height

        self.area.width = self.width
        self.area.height = self.height

    def ProcessEvent(self, event):
        return False
    
    def Update(self, deltaTime):
        pass

    def Render(self, screen):
        if self.visible and self.surf is not None:
            screen.blit(self.surf, self.rect, self.area)