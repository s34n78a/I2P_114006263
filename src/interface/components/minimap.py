import pygame as pg
from typing import Optional
from src.utils import GameSettings

class Minimap:
    # minimap dari current_map._surface yang di scale down

    def __init__(self, x: int = 10, y: int = 10, width: int = 200, height: int = 150, padding: int = 4):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.padding = padding
        self.rect = pg.Rect(self.x, self.y, self.width, self.height)

        # cache biar ga scaling every frame
        self._cached_map = None
        self._cached_scaled: Optional[pg.Surface] = None
        self._cached_size = (0, 0)

    def draw(self, screen: pg.Surface, game_manager) -> None:
        if not game_manager:
            return

        cur_map = game_manager.current_map
        if cur_map is None:
            return

        # map pixel size
        map_w = cur_map.tmxdata.width * GameSettings.TILE_SIZE
        map_h = cur_map.tmxdata.height * GameSettings.TILE_SIZE
        if map_w <= 0 or map_h <= 0:
            return

        inner_w = max(1, self.width - self.padding * 2)
        inner_h = max(1, self.height - self.padding * 2)

        # background
        bg_surf = pg.Surface((self.width, self.height), pg.SRCALPHA)
        bg_surf.fill((0, 0, 0, 120))
        screen.blit(bg_surf, (self.x, self.y))

        # bikin map lebih kecil kalau pre-render surface ada
        src_surface = cur_map._surface
        if src_surface:
            # bikin cache baru kalau map instance atau minimap berubah ukuran
            if self._cached_map is not cur_map or self._cached_size != (inner_w, inner_h) or self._cached_scaled is None:
                try:
                    self._cached_scaled = pg.transform.smoothscale(src_surface, (inner_w, inner_h))
                except Exception:
                    s = pg.Surface((inner_w, inner_h))
                    s.fill((40, 40, 40))
                    self._cached_scaled = s
                self._cached_map = cur_map
                self._cached_size = (inner_w, inner_h)

            # blit cached scaled surface
            screen.blit(self._cached_scaled, (self.x + self.padding, self.y + self.padding))
        else:
            inner = pg.Surface((inner_w, inner_h))
            inner.fill((40, 40, 40))
            screen.blit(inner, (self.x + self.padding, self.y + self.padding))

        # border
        pg.draw.rect(screen, (200, 200, 200), self.rect, 1)

        # bikin player dot
        player = game_manager.player
        if player:
            sx = (inner_w) / map_w
            sy = (inner_h) / map_h
            dot_x = int(player.position.x * sx) + self.x + self.padding
            dot_y = int(player.position.y * sy) + self.y + self.padding
            # clamp
            dot_x = max(self.x + self.padding, min(self.x + self.padding + inner_w - 1, dot_x))
            dot_y = max(self.y + self.padding, min(self.y + self.padding + inner_h - 1, dot_y))
            pg.draw.circle(screen, (255, 0, 0), (dot_x, dot_y), 4)
