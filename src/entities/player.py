from __future__ import annotations
import pygame as pg

#from src.core.managers import scene_manager
#from src.core.managers.scene_manager import SceneManager
from .entity import Entity
from src.core.services import input_manager, scene_manager
from src.utils import Position, PositionCamera, GameSettings, Logger
from src.core import GameManager
import math
from typing import override

class Player(Entity):
    speed: float = 4.0 * GameSettings.TILE_SIZE
    game_manager: GameManager

    def __init__(self, x: float, y: float, game_manager: GameManager) -> None:
        super().__init__(x, y, game_manager)
        self.last_teleport_pos = None # biar ga teleport terus
        self.in_teleport = False

        # checkpoint 3
        self.auto_path = None
        self.auto_speed = 4.0 * GameSettings.TILE_SIZE

    # cek collision sama enemy trainers lain
    def check_collision_with_enemies(self, rect:pg.Rect) -> bool:
        for enemy in self.game_manager.current_enemy_trainers:
            enemy_rect = pg.Rect(enemy.position.x, enemy.position.y,
                                GameSettings.TILE_SIZE, GameSettings.TILE_SIZE)
            if rect.colliderect(enemy_rect):
                return True
        return False

    # checkpoint 3
    # cek collision sama shop keepers lain
    def check_collision_with_shop_keepers(self, rect:pg.Rect) -> bool:
        for shop_keeper in self.game_manager.current_shop_keepers:
            shop_keeper_rect = pg.Rect(shop_keeper.position.x, shop_keeper.position.y,
                                GameSettings.TILE_SIZE, GameSettings.TILE_SIZE)
            if rect.colliderect(shop_keeper_rect):
                return True
        return False

    @override
    def update(self, dt: float) -> None:
        dis = Position(0, 0)
        '''
        [TODO HACKATHON 2]
        Calculate the distance change, and then normalize the distance
        
        [TODO HACKATHON 4]
        Check if there is collision, if so try to make the movement smooth
        Hint #1 : use entity.py _snap_to_grid function or create a similar function
        Hint #2 : Beware of glitchy teleportation, you must do
                    1. Update X
                    2. If collide, snap to grid
                    3. Update Y
                    4. If collide, snap to grid
                  instead of update both x, y, then snap to grid
        
        if input_manager.key_down(pg.K_LEFT) or input_manager.key_down(pg.K_a):
            dis.x -= ...
        if input_manager.key_down(pg.K_RIGHT) or input_manager.key_down(pg.K_d):
            dis.x += ...
        if input_manager.key_down(pg.K_UP) or input_manager.key_down(pg.K_w):
            dis.y -= ...
        if input_manager.key_down(pg.K_DOWN) or input_manager.key_down(pg.K_s):
            dis.y += ...
        
        self.position = ...
        '''
        
        if self.auto_path: # checkpoint 3
            # calculate movement direction for this frame
            #self._auto_move_step(dt)

            # override WASD
            #dis = Position(self._auto_dx, self._auto_dy)

            if self.auto_path:
                next_tx, next_ty = self.auto_path[0]

                target_px = next_tx * GameSettings.TILE_SIZE
                target_py = next_ty * GameSettings.TILE_SIZE

                dx = target_px - self.position.x
                dy = target_py - self.position.y

                #dis = Position(dx* self.auto_speed * dt, dy* self.auto_speed * dt)

                # If close → snap
                close_enough = self.auto_speed / GameSettings.TILE_SIZE
                if abs(dx) < close_enough and abs(dy) < close_enough:
                    self.position.x = target_px
                    self.position.y = target_py
                    self.auto_path.pop(0)

                    if not self.auto_path:
                        self.auto_path = None

                    # IMPORTANT: give no direction after snapping
                    dis = Position(0, 0)
                else:
                    # NORMALIZED direction → this is the "WASD" replacement
                    dist = math.hypot(dx, dy)
                    dis = Position(dx / dist, dy / dist)

                
                # Move horizontally first (only if not aligned)
                # if abs(self.position.x - target_px) > 1:
                #     direction = 1 if target_px > self.position.x else -1
                #     new_x = self.position.x + direction * self.auto_speed * dt
                    
                #     # prevent overshoot
                #     if (direction == 1 and new_x > target_px) or (direction == -1 and new_x < target_px):
                #         new_x = target_px

                #     # test collision
                #     rect = pg.Rect(new_x, self.position.y, GameSettings.TILE_SIZE, GameSettings.TILE_SIZE)
                #     if not self.game_manager.current_map.check_collision(rect):
                #         self.position.x = new_x
                #         #dis = Position(direction * self.auto_speed * dt, 0)
                #         return  # stay in auto mode

                # # Move vertically second
                # if abs(self.position.y - target_py) > 1:
                #     direction = 1 if target_py > self.position.y else -1
                #     new_y = self.position.y + direction * self.auto_speed * dt

                #     # prevent overshoot
                #     if (direction == 1 and new_y > target_py) or (direction == -1 and new_y < target_py):
                #         new_y = target_py

                #     rect = pg.Rect(self.position.x, new_y, GameSettings.TILE_SIZE, GameSettings.TILE_SIZE)
                #     if not self.game_manager.current_map.check_collision(rect):
                #         self.position.y = new_y
                #         #dis = Position(0, direction * self.auto_speed * dt)
                #         return  # stay in auto mode
    
                # # SNAP and go to next tile
                # self.position.x = target_px
                # self.position.y = target_py
                # self.auto_path.pop(0)

                # # finished entire path
                # if not self.auto_path:
                #     self.auto_path = None

                # dis = Position(0, 0)

        else:
            # manual input
            dis = Position(0, 0)
            if input_manager.key_down(pg.K_LEFT) or input_manager.key_down(pg.K_a):
                dis.x -= 1
            if input_manager.key_down(pg.K_RIGHT) or input_manager.key_down(pg.K_d):
                dis.x += 1
            if input_manager.key_down(pg.K_UP) or input_manager.key_down(pg.K_w):
                dis.y -= 1
            if input_manager.key_down(pg.K_DOWN) or input_manager.key_down(pg.K_s):
                dis.y += 1


        length = math.hypot(dis.x, dis.y)
        if length != 0:
            dis.x = dis.x / length
            dis.y = dis.y / length

        # Hitung movement dlm pixels di delta time dt
        move_x = dis.x * self.speed * dt
        move_y = dis.y * self.speed * dt

        # --- Collision handling ---
        tile_size = GameSettings.TILE_SIZE
        rect = pg.Rect(self.position.x, self.position.y, tile_size, tile_size)
        
        # buat debugging
        # Logger.debug(f"Player rect: {rect}")

        # geser X
        rect.x += move_x
        if not self.game_manager.current_map.check_collision(rect) and not self.check_collision_with_enemies(rect) and not self.check_collision_with_shop_keepers(rect):
            self.position.x += move_x
        else:
            # Snap to grid biar ga overlap
            if move_x > 0:
                self.position.x = rect.x // tile_size * tile_size
            elif move_x < 0:
                self.position.x = rect.x // tile_size * tile_size + tile_size

        # geser Y
        rect.y += move_y
        if not self.game_manager.current_map.check_collision(rect) and not self.check_collision_with_enemies(rect) and not self.check_collision_with_shop_keepers(rect):
            self.position.y += move_y
        else:
            if move_y > 0:
                self.position.y = rect.y // tile_size * tile_size
            elif move_y < 0:
                self.position.y = rect.y // tile_size * tile_size + tile_size

        # Cek teleportasi [hackathon 5]
        tp = self.game_manager.current_map.check_teleport(self.position)
        
        if tp:
            if not self.in_teleport:  # player masuk
                self.in_teleport = True
                self.game_manager.previous_map_key = self.game_manager.current_map_key
                self.game_manager.switch_map(tp.destination)
            # else: player masih di dalem → do nothing
        else:
            # player keluar dari teleporter → reset
            self.in_teleport = False

        # Wild bush (check point 2)
        #scene_manager = SceneManager()
        if self.game_manager.current_map.check_bush(self.position) and self.auto_path is None:
            # prevent retrigger spam by storing last bush tile
            if not getattr(self, "_in_bush", False):
                self._in_bush = True
                from src.scenes.battle_scene import BattleScene
                BattleScene.prepare_wild(game_manager=self.game_manager)
                scene_manager.change_scene("battle")
        else:
            self._in_bush = False


        super().update(dt)

    @override
    def draw(self, screen: pg.Surface, camera: PositionCamera) -> None:
        super().draw(screen, camera)
        
    @override
    def to_dict(self) -> dict[str, object]:
        return super().to_dict()
    
    @classmethod
    @override
    def from_dict(cls, data: dict[str, object], game_manager: GameManager) -> Player:
        return cls(data["x"] * GameSettings.TILE_SIZE, data["y"] * GameSettings.TILE_SIZE, game_manager)

    # checkpoint 3
    def set_auto_path(self, tile_path):
        # auto walk mengikuti path tile list
        self.auto_path = tile_path[1:]  # skip current tile 

    def _auto_move_step(self, dt):
        if not self.auto_path:
            return

        next_tx, next_ty = self.auto_path[0]

        target_px = next_tx * GameSettings.TILE_SIZE
        target_py = next_ty * GameSettings.TILE_SIZE

        dx = target_px - self.position.x
        dy = target_py - self.position.y

        dist = math.hypot(dx, dy)
        if dist < 0.5:
            # Snap to tile
            self.position.x = target_px
            self.position.y = target_py
            self.auto_path.pop(0)

            if not self.auto_path:
                self.auto_path = None

            return

        # Normalized movement
        vx = (dx / dist) * self.auto_speed * dt
        vy = (dy / dist) * self.auto_speed * dt

        # Move without overriding manual collision
        rect = pg.Rect(self.position.x + vx, self.position.y, GameSettings.TILE_SIZE, GameSettings.TILE_SIZE)
        if not self.game_manager.current_map.check_collision(rect):
            self.position.x += vx

        rect = pg.Rect(self.position.x, self.position.y + vy, GameSettings.TILE_SIZE, GameSettings.TILE_SIZE)
        if not self.game_manager.current_map.check_collision(rect):
            self.position.y += vy

