import pygame as pg

class Slider:
    def __init__(self, x, y, width, value=0.5):
        self.x = x
        self.y = y
        self.width = width
        self.value = value  # 0.0 to 1.0
        self.dragging = False

        self.bar_rect = pg.Rect(x, y, width, 6)
        self.knob_rect = pg.Rect(x + value * width - 8, y - 6, 16, 16)

    def update(self, dt):
        mouse = pg.mouse.get_pos()
        click = pg.mouse.get_pressed()[0]

        # Start dragging
        if self.knob_rect.collidepoint(mouse) and click:
            self.dragging = True

        # Stop dragging
        if not click:
            self.dragging = False

        # Drag update
        if self.dragging:
            rel_x = mouse[0] - self.x
            rel_x = max(0, min(self.width, rel_x))
            self.value = rel_x / self.width
            self.knob_rect.x = self.x + rel_x - 8

    def draw(self, screen):
        # Bar
        pg.draw.rect(screen, (40, 40, 40), self.bar_rect)
        # Knob
        pg.draw.rect(screen, (0, 0, 0), self.knob_rect)

    def get_value(self):
        return self.value

