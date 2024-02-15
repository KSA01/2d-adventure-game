
import pygame
import numpy as np
import World.WorldCommon as WC
from UI.UIImage import UIImage

class UIText(UIImage):
    def __init__(self, element=None):
        if element is not None:
            super().__init__(element)
            
            txt_el = element.find("Font")
            if txt_el is not None:
                self.text = txt_el.get("text", "")
                self.font_name = txt_el.get("font", "arial")
                self.color_name = txt_el.get("color", "white")
                self.size = int(txt_el.get("size", 16))
                self.txt_justify = txt_el.get("justify", "left")
                self.txt_vjustify = txt_el.get("vjustify", "top")

                self.color = pygame.Color(self.color_name)
                self.font = pygame.font.SysFont(self.font_name, self.size)
                self.txt_surf = self.font.render(self.text, True, self.color)
                self.txt_width = self.txt_surf.get_width()
                self.txt_height = self.txt_surf.get_height()
            else:
                self.txt_surf = None
                self.txt_width = 0
                self.txt_height = 0
            self.txt_rect = pygame.Rect((self.x, self.y), (self.txt_width, self.txt_height))

            self._CalcTextRect()

    def _CalcTextRect(self):
        self._CalcRect()

        self.txt_rect.left = self.rect.left
        if self.txt_justify == "right":
            self.txt_rect.left += self.width - self.txt_width
        elif self.txt_justify == "center":
            self.txt_rect.left += (self.width - self.txt_width) // 2

        self.txt_rect.top = self.rect.top
        if self.txt_vjustify == "bottom":
            self.txt_rect.top += self.height - self.txt_height
        elif self.txt_vjustify == "center":
            self.txt_rect.top += (self.height - self.txt_height) // 2

        self.txt_rect.width = self.txt_width
        self.txt_rect.height = self.txt_height

    def Update(self, deltaTime):
        super().Update(deltaTime)

    def Render(self, screen):
        if self.visible:
            super().Render(screen)
            if self.txt_surf is not None:
                screen.blit(self.txt_surf, self.txt_rect)
            