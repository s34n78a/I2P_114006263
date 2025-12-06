from __future__ import annotations
from src.pathfinding.bfs import bfs_pathfind
from src.utils import Logger, GameSettings, Position, Teleport
import json, os
import pygame as pg
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.maps.map import Map
    from src.entities.player import Player
    from src.entities.enemy_trainer import EnemyTrainer
    from src.entities.shop import ShopKeeper # checkpoint 3
    from src.data.bag import Bag

class GameManager:
    # Entities
    player: Player | None
    enemy_trainers: dict[str, list[EnemyTrainer]]
    shop_keepers: dict[str, list[ShopKeeper]] # checkpoint 3
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
                 shop_keepers: dict[str, list[ShopKeeper]], # checkpoint 3
                 bag: Bag | None = None):
        
        from src.data.bag import Bag
        # Game Properties
        self.maps = maps
        self.current_map_key = start_map
        self.previous_map_key = None # Untuk nyimpen map sebelumnya pas teleport [TO DO HACKATHON 6]
        self.teleport_cooldown = 0

        self.player = player
        self.enemy_trainers = enemy_trainers
        self.shop_keepers = shop_keepers # checkpoint 3
        self.bag = bag if bag is not None else Bag([], [])

        # checkpoint 3
        self.pending_navigation_map: str | None = None
        self.pending_navigation_path: list[tuple[int, int]] | None = None
        self.navigation_active: bool = False
        # self.pending_navigation_current: int = 0
        # self.pending_navigation_route: list | None = None

        # buat debugging
        #print("Loaded map keys:", list(self.maps.keys()))

        # Check If you should change scene
        self.should_change_scene = False
        self.next_map = ""

        # Player spawns (buat saving)
        self.player_spawns: dict[str, Position] = {}

        # Pastiin trainers & shopkeepers list ada utk tiap map
        for key in self.maps.keys():
            self.enemy_trainers.setdefault(key, [])
            self.shop_keepers.setdefault(key, []) # checkpoint 3

    @property
    def current_map(self) -> Map:
        return self.maps[self.current_map_key]

    @property
    def current_enemy_trainers(self) -> list[EnemyTrainer]:
        return self.enemy_trainers[self.current_map_key]
    
    # checkpoint 3
    @property
    def current_shop_keepers(self) -> list[ShopKeeper]:
        return self.shop_keepers[self.current_map_key]

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
        #self.current_map_key = target

    def try_switch_map(self) -> None:
        # reduce cooldown timer
        if self.teleport_cooldown > 0:
            self.teleport_cooldown -= 1
   
        #if self.should_change_scene:
        #    self.current_map_key = self.next_map
        #    self.next_map = ""
        #    self.should_change_scene = False
            
        if not self.should_change_scene:
            return

        # Switch
        old_map = self.current_map_key
        new_map = self.next_map
        Logger.info(f"Switching map: {old_map} -> {new_map}")
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
            if return_tp and not self.navigation_active and self.teleport_cooldown == 0:
                Logger.info(f"Placing player at return teleporter {return_tp.pos} in {new_map}")
                self.player.position = return_tp.pos.copy()
            else:
                # safe fallback: map spawn
                Logger.info(f"No return teleporter found; placing player at spawn in {new_map}")
                self.player.position = self.maps[new_map].spawn.copy()

            # set cooldown to prevent immediate retrigger
            self.teleport_cooldown = 15    # ~0.25s at 60 FPS

    def check_collision(self, rect: pg.Rect) -> bool:
        if self.current_map.check_collision(rect):
            return True
        for entity in self.current_enemy_trainers:
            if rect.colliderect(entity.animation.rect):
                return True
            
        for entity in self.current_shop_keepers: # checkpoint 3
            if rect.colliderect(entity.animation.rect):
                return True

        return False
    
    # checkpoint 3
    def is_blocked_tile(self, tx, ty) -> bool:
        px, py = tx * GameSettings.TILE_SIZE, ty * GameSettings.TILE_SIZE
        rect = pg.Rect(px, py, GameSettings.TILE_SIZE, GameSettings.TILE_SIZE)
        return self.current_map.check_collision(rect) or self.check_collision(rect)

    def navigate_to(self, place_name: str) -> None:
        self.pending_destination_name = place_name
        self.navigation_active = True
        Logger.info(f"Computing navigation to place {place_name} in {self.current_map.path_name}")
        self.compute_navigation_path()

    def compute_navigation_path(self) -> None:
        if not self.navigation_active or not self.pending_destination_name:
            Logger.info("Navigation inactive or no pending destination.")
            return

        destinations = getattr(self.current_map, "navigation_destinations", [])
        dest = next((d for d in destinations if d["place_name"] == self.pending_destination_name), None)
        if not dest:
            Logger.warning(f"Navigation: destination '{self.pending_destination_name}' not found in current map.")
            self.navigation_active = False
            return

        start_tile = (int(self.player.position.x // GameSettings.TILE_SIZE),
                      int(self.player.position.y // GameSettings.TILE_SIZE))
        dest_tile = (dest["x"], dest["y"])

        if start_tile == dest_tile:
            Logger.info(f"Navigation: already at destination '{self.pending_destination_name}'.")
            self.navigation_active = False
            return

        Logger.info(f"Navigation: computing BFS from {start_tile} to {dest_tile}")
        path = bfs_pathfind(self.current_map, start_tile, dest_tile, self.is_blocked_tile)
        if path:
            Logger.info(f"Navigation: BFS path computed (len={len(path)}). Starting auto-walk.")
            self.pending_navigation_path = path
            self.player.set_auto_path(path)
        else:
            Logger.warning("Navigation: path blocked. Cancelling navigation.")
            self.navigation_active = False

    def update_navigation(self) -> None:
        if not self.navigation_active or not self.pending_destination_name:
            return
        if not self.pending_navigation_path or not self.player.auto_path:
            self.compute_navigation_path()
            return

        if not self.player.auto_path:  # Reached destination
            Logger.info(f"Navigation complete to {self.pending_destination_name}")
            self.pending_navigation_path = None
            self.pending_destination_name = None
            self.navigation_active = False

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

            # Save shop keepers for this map (checkpoint 3)
            block["shop_keepers"] = [s.to_dict() for s in self.shop_keepers.get(key, [])]

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
        from src.entities.shop import ShopKeeper # checkpoint 3
        from src.data.bag import Bag

        Logger.info("Loading maps")
        maps: dict[str, Map] = {}
        trainers: dict[str, list[EnemyTrainer]] = {}
        shop_keepers: dict[str, list[ShopKeeper]] = {} # checkpoint 3
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
            shop_keepers, # checkpoint 3
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

        # checkpoint 3
        Logger.info("Loading shop keepers")
        for m in data["map"]:
            raw_data = m.get("shop_keepers", [])
            gm.shop_keepers[m["path"]] = [ShopKeeper.from_dict(s, gm) for s in raw_data]
        
        # Pastiin semua maps punya shop keeper list (benerin KeyError)
        for key in gm.maps.keys():
            gm.shop_keepers.setdefault(key, []) # checkpoint 3

        Logger.info("Loading Player")
        if data.get("player"):
            gm.player = Player.from_dict(data["player"], gm)

        Logger.info("Loading bag")
        from src.data.bag import Bag as _Bag
        gm.bag = Bag.from_dict(data.get("bag", {})) if data.get("bag") else _Bag([], [])

        # Load audio
        audio = data.get("audio", {})
        GameSettings.AUDIO_VOLUME = audio.get("volume", 0.5)
        GameSettings.MUTE = audio.get("mute", False)
            
        return gm
