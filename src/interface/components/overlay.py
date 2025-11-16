from __future__ import annotations
import pygame as pg
from typing import List
from .component import UIComponent


class OverlayPanel(UIComponent):
    def __init__(
        self,
        x: int, y: int,
        width: int, height: int,
        background_image=None
    ):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.background_image = background_image
        self.rect = pg.Rect(x, y, width, height)
        self.visible = False
        
        # list buat save child component (button, image, etc.)
        self.children: List[UIComponent] = []

    # nambah child UI component (button, image, etc.)
    def add_child(self, component: UIComponent):
        self.children.append(component)

    def show(self):
        self.visible = True

    def hide(self):
        self.visible = False

    def update(self, dt: float) -> None:
        if not self.visible:
            return

        for child in self.children:
            child.update(dt)

    def draw(self, screen: pg.Surface) -> None:
        if not self.visible:
            return

        # Gambar dark background
        dark = pg.Surface(screen.get_size())
        dark.set_alpha(150)
        dark.fill((0, 0, 0))
        screen.blit(dark, (0, 0))

        # Draw overlay panel background image *on top of the dark*
        if self.background_image:
            screen.blit(self.background_image, (self.rect.x, self.rect.y))

        # Gambar semua child element
        for child in self.children:
            child.draw(screen)
