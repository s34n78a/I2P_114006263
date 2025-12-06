import pygame as pg
import json
from src.utils import GameSettings
from src.utils.definition import Monster, Item


class Bag:
    _monsters_data: list[Monster]
    _items_data: list[Item]

    def __init__(self, monsters_data: list[Monster] | None = None, items_data: list[Item] | None = None):
        self._monsters_data = monsters_data if monsters_data else []
        self._items_data = items_data if items_data else []

    def update(self, dt: float):
        pass

    def draw(self, screen: pg.Surface):
        pass

    def to_dict(self) -> dict[str, object]:
        return {
            "monsters": list(self._monsters_data),
            "items": list(self._items_data)
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "Bag":
        monsters = data.get("monsters") or []
        items = data.get("items") or []
        bag = cls(monsters, items)
        return bag
    
    # checkpoint 2
    @property
    def monsters(self) -> list[Monster]:
        return self._monsters_data
    
    @property
    def items(self) -> list[Item]:
        return self._items_data
    
    def use_item(self, item_name: str) -> bool:
        # ngurangin 1 item kalau used, return True kalau berhasil
        for item in self._items_data:
            if item["name"] == item_name and item.get("count", 0) > 0:
                item["count"] -= 1
                return True
        return False
    
    def add_item(self, name: str, count: int = 1, sprite_path: str | None = None):
        # cari dari item yg ada
        for item in self._items_data:
            if item["name"] == name:
                item["count"] += count
                return

        # kalau ga ketemu, bikin entry baru (takutnya ada salah)
        self._items_data.append({
            "name": name,
            "count": count,
            "sprite_path": "ingame_ui/potion.png" if sprite_path is None else sprite_path
        })
