from __future__ import annotations
import pygame
from enum import Enum
from dataclasses import dataclass
from typing import override

from .entity import Entity
from src.sprites import Sprite
from src.core import GameManager
from src.core.services import input_manager, scene_manager
from src.utils import GameSettings, Direction, Position, PositionCamera, Logger

from src.scenes.battle_scene import BattleScene 
from src.sprites import Animation

class EnemyTrainerClassification(Enum):
    STATIONARY = "stationary"

@dataclass
class IdleMovement:
    def update(self, enemy: "EnemyTrainer", dt: float) -> None:
        return

class EnemyTrainer(Entity):
    classification: EnemyTrainerClassification
    max_tiles: int
    _movement: IdleMovement
    warning_sign: Sprite
    detected: bool
    los_direction: Direction

    animation: Animation

    @override
    def __init__(
        self,
        x: float,
        y: float,
        game_manager: GameManager,
        classification: EnemyTrainerClassification = EnemyTrainerClassification.STATIONARY,
        max_tiles: int = 2,
        facing: Direction | None = None,
    ) -> None:
        super().__init__(x, y, game_manager)
        self.classification = classification
        self.max_tiles = max_tiles
        if classification == EnemyTrainerClassification.STATIONARY:
            self._movement = IdleMovement()
            if facing is None:
                raise ValueError("Idle EnemyTrainer requires a 'facing' Direction at instantiation")
            self._set_direction(facing)
        else:
            raise ValueError("Invalid classification")
        self.warning_sign = Sprite("exclamation.png", (GameSettings.TILE_SIZE // 2, GameSettings.TILE_SIZE // 2))
        self.warning_sign.update_pos(Position(x + GameSettings.TILE_SIZE // 4, y - GameSettings.TILE_SIZE // 2))
        self.detected = False

        self.animation = Animation(
            "character/ow4.png", ["down", "left", "right", "up"], 4,
            (GameSettings.TILE_SIZE, GameSettings.TILE_SIZE)
        )
        self._set_direction(facing)
        self.animation.update_pos(self.position)

    @override
    def update(self, dt: float) -> None:
        self._movement.update(self, dt)
        self._has_los_to_player()
        if self.detected and input_manager.key_pressed(pygame.K_SPACE):
            # checkpoint 3, player ga boleh lagi teleport atau auto path pas battle
            # Logger.info(f"Player teleport: {self.game_manager.player.in_teleport}")
            # Logger.info(f"Player auto path: {self.game_manager.player.auto_path}")
            if self.game_manager.player.in_teleport or self.game_manager.player.auto_path is not None:
                Logger.info("[ENEMY TRAINER] Player cannot battle while teleporting or auto pathing.")
                return

            # checkpoint 2
            Logger.info("[ENEMY TRAINER] Player detected by enemy trainer, initiating battle!")
            BattleScene.prepare(self)
            scene_manager.change_scene("battle")
        self.animation.update_pos(self.position)

    @override
    def draw(self, screen: pygame.Surface, camera: PositionCamera) -> None:
        super().draw(screen, camera)
        if self.detected:
            self.warning_sign.draw(screen, camera)
        if GameSettings.DRAW_HITBOXES:
            los_rect = self._get_los_rect()
            if los_rect is not None:
                pygame.draw.rect(screen, (255, 255, 0), camera.transform_rect(los_rect), 1)

    def _set_direction(self, direction: Direction) -> None:
        self.direction = direction
        if direction == Direction.RIGHT:
            self.animation.switch("right")
        elif direction == Direction.LEFT:
            self.animation.switch("left")
        elif direction == Direction.DOWN:
            self.animation.switch("down")
        else:
            self.animation.switch("up")
        self.los_direction = self.direction

    def _get_los_rect(self) -> pygame.Rect | None:
        '''
        TODO: Create hitbox to detect line of sight of the enemies towards the player
        '''
        size = GameSettings.TILE_SIZE

        # checkpoint 2
        # LOS panjangnya max_tiles & lebar 1 tile dari posisi enemy trainer ke atas kiri kanan bawah
        if self.los_direction == Direction.UP:
            return pygame.Rect(
                self.position.x,
                self.position.y - size * self.max_tiles,
                size,
                size * self.max_tiles
            )
        elif self.los_direction == Direction.DOWN:
            return pygame.Rect(
                self.position.x,
                self.position.y + size,
                size,
                size * self.max_tiles
            )
        elif self.los_direction == Direction.LEFT:
            return pygame.Rect(
                self.position.x - size * self.max_tiles,
                self.position.y,
                size * self.max_tiles,
                size
            )
        elif self.los_direction == Direction.RIGHT:
            return pygame.Rect(
                self.position.x + size,
                self.position.y,
                size * self.max_tiles,
                size
            )
        return None

    def _has_los_to_player(self) -> None:
        player = self.game_manager.player
        if player is None:
            self.detected = False
            return
        los_rect = self._get_los_rect()
        if los_rect is None:
            self.detected = False
            return
        '''
        TODO: Implement line of sight detection
        If it's detected, set self.detected to True
        '''

        # checkpoint 2
        if los_rect.colliderect(player.animation.rect):
            self.detected = True
        else:
            self.detected = False

    @classmethod
    @override
    def from_dict(cls, data: dict, game_manager: GameManager) -> "EnemyTrainer":
        classification = EnemyTrainerClassification(data.get("classification", "stationary"))
        max_tiles = data.get("max_tiles")
        facing_val = data.get("facing")
        facing: Direction | None = None
        if facing_val is not None:
            if isinstance(facing_val, str):
                facing = Direction[facing_val]
            elif isinstance(facing_val, Direction):
                facing = facing_val
        if facing is None and classification == EnemyTrainerClassification.STATIONARY:
            facing = Direction.DOWN
        return cls(
            data["x"] * GameSettings.TILE_SIZE,
            data["y"] * GameSettings.TILE_SIZE,
            game_manager,
            classification,
            max_tiles,
            facing,
        )

    @override
    def to_dict(self) -> dict[str, object]:
        base: dict[str, object] = super().to_dict()
        base["classification"] = self.classification.value
        base["facing"] = self.direction.name
        base["max_tiles"] = self.max_tiles
        return base