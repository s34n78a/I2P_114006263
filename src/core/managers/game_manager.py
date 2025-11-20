from __future__ import annotations
from src.utils import Logger, GameSettings, Position, Teleport
import json, os
import pygame as pg
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.maps.map import Map
    from src.entities.player import Player
    from src.entities.enemy_trainer import EnemyTrainer
    from src.data.bag import Bag

class GameManager:
    # Entities
    player: Player | None
    enemy_trainers: dict[str, list[EnemyTrainer]]
    bag: "Bag"
    
    # Map properties
    current_map_key: str
    maps: dict[str, Map]
    
    # Changing Scene properties
    should_change_scene: bool
    next_map: str

    def __init__(self, maps: dict[str, Map], start_map: str,
                 player: Player | None,
                 enemy_trainers: dict[str, list[EnemyTrainer]],
                 bag: Bag | None = None):
        
        from src.data.bag import Bag
        # Game Properties
        self.maps = maps
        self.current_map_key = start_map
        self.previous_map_key = None # Untuk nyimpen map sebelumnya pas teleport [TO DO HACKATHON 6]
        self.teleport_cooldown = 0

        self.player = player
        self.enemy_trainers = enemy_trainers
        self.bag = bag if bag is not None else Bag([], [])

        # buat debugging
        #print("Loaded map keys:", list(self.maps.keys()))

        # Check If you should change scene
        self.should_change_scene = False
        self.next_map = ""

        # Player spawns (buat saving)
        self.player_spawns: dict[str, Position] = {}

        # Pastiin trainers list ada utk tiap map
        for key in self.maps.keys():
            self.enemy_trainers.setdefault(key, [])

    @property
    def current_map(self) -> Map:
        return self.maps[self.current_map_key]

    @property
    def current_enemy_trainers(self) -> list[EnemyTrainer]:
        return self.enemy_trainers[self.current_map_key]

    @property
    def current_teleporter(self) -> list[Teleport]:
        return self.maps[self.current_map_key].teleporters

    def switch_map(self, target: str) -> None:
        if target not in self.maps:
            Logger.warning(f"Map '{target}' not loaded; cannot switch.")
            return
        
        self.next_map = target
        self.should_change_scene = True
        self.previous_map_key = self.current_map_key # Simpen map pas teleport [TO DO HACKATHON 6]

    def try_switch_map(self) -> None:
        # reduce cooldown timer
        if self.teleport_cooldown > 0:
            self.teleport_cooldown -= 1
   
        #if self.should_change_scene:
        #    self.current_map_key = self.next_map
        #    self.next_map = ""
        #    self.should_change_scene = False
            
            # biar teleport ga ke spawn terus [TO DO HACKATHON 6]
            #if self.player:
            #    self.player.position = self.maps[self.current_map_key].spawn

        if not self.should_change_scene:
            return

        # Switch
        old_map = self.current_map_key
        new_map = self.next_map
        self.current_map_key = new_map
        self.next_map = ""
        self.should_change_scene = False

        # Look for return teleporter (new map → previous map)
        return_tp = None
        for tp in self.maps[new_map].teleporters:
            if tp.destination == old_map:
                return_tp = tp
                break

        # Move player safely
        if self.player:
            if return_tp:
                self.player.position = return_tp.pos.copy()
            else:
                # safe fallback: map spawn
                self.player.position = self.maps[new_map].spawn.copy()

            # set cooldown to prevent immediate retrigger
            self.teleport_cooldown = 15    # ~0.25s at 60 FPS

    def check_collision(self, rect: pg.Rect) -> bool:
        if self.current_map.check_collision(rect):
            return True
        for entity in self.current_enemy_trainers:
            if rect.colliderect(entity.animation.rect):
                return True

        return False
    
    def save(self, path: str) -> None:
        try:
            with open(path, "w") as f:
                json.dump(self.to_dict(), f, indent=2)
            Logger.info(f"Game saved to {path}")
        except Exception as e:
            Logger.warning(f"Failed to save game: {e}")

    @classmethod
    def load(cls, path: str) -> "GameManager | None":
        if not os.path.exists(path):
            Logger.error(f"No file found: {path}, ignoring load function")
            return None

        with open(path, "r") as f:
            data = json.load(f)
        return cls.from_dict(data)

    # checkpoint 2
    def to_dict(self) -> dict[str, object]:
        map_blocks: list[dict[str, object]] = []
        for key, m in self.maps.items():
            block = m.to_dict()
            block["path"] = key

            # Save trainers for this map
            block["enemy_trainers"] = [t.to_dict() for t in self.enemy_trainers.get(key, [])]
            #spawn = self.player_spawns.get(key)
            #if spawn: # Simpen posisi spawn player di map ini, dicek pake if biar ga error
            #    block["player"] = {
            #        "x": spawn.x / GameSettings.TILE_SIZE,
            #        "y": spawn.y / GameSettings.TILE_SIZE
            #    }
            #else:
            #    block["player"] = {"x": 0, "y": 0}

            map_blocks.append(block)
            
        return {
            "map": map_blocks,
            "current_map": self.current_map_key,
            "player": self.player.to_dict() if self.player else None,
            "bag": self.bag.to_dict(),
            "audio": {
                "volume": GameSettings.AUDIO_VOLUME,
                "mute": GameSettings.MUTE
            }
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "GameManager":
        from src.maps.map import Map
        from src.entities.player import Player
        from src.entities.enemy_trainer import EnemyTrainer
        from src.data.bag import Bag

        Logger.info("Loading maps")
        maps: dict[str, Map] = {}
        trainers: dict[str, list[EnemyTrainer]] = {}
        player_spawns: dict[str, Position] = {}

        for entry in data["map"]:
            path = entry["path"]
            maps[path] = Map.from_dict(entry)
            sp = entry.get("player")
            if sp:
                player_spawns[path] = Position(
                    sp["x"] * GameSettings.TILE_SIZE,
                    sp["y"] * GameSettings.TILE_SIZE
                )

        current_map = data["current_map"]
        gm = cls( # bikin game manager yg kosong
            maps,
            current_map,
            None, # Player
            trainers,
            bag=None
        )
        gm.player_spawns = player_spawns

        Logger.info("Loading enemy trainers")
        for m in data["map"]:
            raw_data = m.get("enemy_trainers", [])
            gm.enemy_trainers[m["path"]] = [EnemyTrainer.from_dict(t, gm) for t in raw_data]

        # Pastiin semua maps punya trainer list (benerin KeyError)
        for key in gm.maps.keys():
            gm.enemy_trainers.setdefault(key, [])

        Logger.info("Loading Player")
        if data.get("player"):
            gm.player = Player.from_dict(data["player"], gm)

        Logger.info("Loading bag")
        from src.data.bag import Bag as _Bag
        gm.bag = Bag.from_dict(data.get("bag", {})) if data.get("bag") else _Bag([], [])
        # opsi bag
        #if data.get("bag"):
        #    gm.bag = Bag.from_dict(data["bag"])
        #else:
        #    gm.bag = Bag([], [])

        # Load audio
        audio = data.get("audio", {})
        GameSettings.AUDIO_VOLUME = audio.get("volume", 0.5)
        GameSettings.MUTE = audio.get("mute", False)

        return gm
