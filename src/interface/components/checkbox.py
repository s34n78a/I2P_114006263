import pygame as pg
from typing import Optional
from src.core.services import input_manager

pg.init()

class Checkbox:
    def __init__(self, x, y, size, checked=False, label=""):
        self.x = x
        self.y = y
        self.size = size
        self.checked = checked
        self.label = label
        self.font = pg.font.Font('assets/fonts/Minecraft.ttf', 20)

        # Load images
        self.img_off = pg.image.load("assets/images/UI/raw/UI_Flat_ToggleOff01a.png").convert_alpha()
        self.img_on  = pg.image.load("assets/images/UI/raw/UI_Flat_ToggleOn01a.png").convert_alpha()

        self.hitbox = pg.Rect(x, y, size, size)

    def update(self, dt):
        mouse_pos = input_manager.mouse_pos

        if self.hitbox.collidepoint(mouse_pos) and input_manager.mouse_pressed(1):
            self.checked = not self.checked

    def draw(self, screen):
        # Checkbox square
        img = self.img_on if self.checked else self.img_off
        img = pg.transform.scale(img, (self.size, self.size))
        screen.blit(img, (self.x, self.y))

        # Label
        txt = self.font.render(self.label, True, (0, 0, 0))
        screen.blit(txt, (self.x + self.size + 15, self.y + (self.size - txt.get_height()) // 2))
    
    def is_checked(self):
        return self.checked
