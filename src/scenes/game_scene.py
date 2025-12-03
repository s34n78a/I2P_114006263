import pygame as pg
import threading
import time
import json, os

from src.scenes.scene import Scene
from src.core import GameManager, OnlineManager
from src.utils import Logger, PositionCamera, GameSettings, Position
from src.core.services import sound_manager
from src.sprites import Sprite
from src.interface.components.overlay import OverlayPanel
from src.interface.components import Button
from src.interface.components.checkbox import Checkbox
from src.interface.components.slider import Slider
from src.pathfinding.bfs import bfs_pathfind
from typing import override

pg.init()

# untuk ngatur font
pg.font.init()
minecraft_font = pg.font.Font('assets/fonts/Minecraft.ttf', 20) # text size 20
title_font = pg.font.Font('assets/fonts/Minecraft.ttf', 30) # text size 30
text_overlay_font = pg.font.Font('assets/fonts/Minecraft.ttf', 15) # text size 15
pokemon_font = pg.font.Font('assets/fonts/Pokemon Solid.ttf', 20) # text size 20

class GameScene(Scene):
    game_manager: GameManager
    online_manager: OnlineManager | None
    sprite_online: Sprite
    
    def __init__(self):
        super().__init__()
        # Game Manager
        manager = GameManager.load("saves/game0.json")
        if manager is None:
            Logger.error("Failed to load game manager")
            exit(1)
        self.game_manager = manager
        
        # Online Manager
        if GameSettings.IS_ONLINE:
            self.online_manager = OnlineManager()
        else:
            self.online_manager = None
        self.sprite_online = Sprite("ingame_ui/options1.png", (GameSettings.TILE_SIZE, GameSettings.TILE_SIZE))
        
        # Menu Button buat buka overlay (Checkpoint 2)
        w, h = 570, 550
        x = (GameSettings.SCREEN_WIDTH - w) // 2
        y = (GameSettings.SCREEN_HEIGHT - h) // 2

        # Load background overlay
        self.overlay_bg = pg.image.load(
            "assets/images/UI/raw/UI_Flat_FrameSlot03a.png"
        ).convert_alpha()

        # Scale sampai sesuai ukuran overlay panel
        self.overlay_bg = pg.transform.scale(self.overlay_bg, (w, h))

        # bikin overlay untuk setting
        self.setting_overlay = OverlayPanel(x, y, w, h, background_image=self.overlay_bg)

        # bikin overlay untuk backpack
        self.backpack_overlay = OverlayPanel(x, y, w, h, background_image=self.overlay_bg)

        # bikin overlay untuk shop (checkpoint 3)
        self.shop_overlay = OverlayPanel(x, y, w, h, background_image=self.overlay_bg)

        # bikin overlay untuk navigation (checkpoint 3)
        self.navigation_overlay = OverlayPanel(x, y, w, h, background_image=self.overlay_bg)

        # Button buat buka overlay setting
        self.setting_button = Button(
            "UI/button_setting.png",
            "UI/button_setting_hover.png",
            x=GameSettings.SCREEN_WIDTH - 48,
            y=8,
            width=40,
            height=40,
            on_click=self.open_setting_overlay
        )

        # Button buat buka overlay backpack
        self.backpack_button = Button(
            "UI/button_backpack.png",
            "UI/button_backpack_hover.png",
            x=GameSettings.SCREEN_WIDTH - 96,
            y=8,
            width=40,
            height=40,
            on_click=self.open_backpack_overlay
        )

        # Button buat buka navigation (checkpoint 3)
        self.navigation_button = Button(
            "UI/raw/UI_Flat_Button01a_4.png",
            "UI/raw/UI_Flat_Button01a_1.png",
            x=GameSettings.SCREEN_WIDTH - 205,
            y=8,
            width=100,
            height=40,
            on_click=self.open_navigation_overlay
        )

        # Close button buat overlay setting
        self.button_x_setting = Button(
            "UI/button_x.png", "UI/button_x_hover.png",
            x=(GameSettings.SCREEN_WIDTH // 2) + 200,
            y=(GameSettings.SCREEN_HEIGHT // 2) - 190,
            width=40,
            height=40,
            on_click=self.close_setting_overlay
        )
        self.setting_overlay.add_child(self.button_x_setting)

        # Close button buat overlay backpack
        self.button_x_backpack = Button(
            "UI/button_x.png", "UI/button_x_hover.png",
            x=(GameSettings.SCREEN_WIDTH // 2) + 200,
            y=(GameSettings.SCREEN_HEIGHT // 2) - 210,
            width=40,
            height=40,
            on_click=self.close_backpack_overlay
        )
        self.backpack_overlay.add_child(self.button_x_backpack)

        # Close button buat overlay shop (checkpoint 3)
        self.button_x_shop = Button(
            "UI/button_x.png", "UI/button_x_hover.png",
            x=(GameSettings.SCREEN_WIDTH // 2) + 200,
            y=(GameSettings.SCREEN_HEIGHT // 2) - 230,
            width=40,
            height=40,
            on_click=self.close_shop_overlay
        )
        self.shop_overlay.add_child(self.button_x_shop)

        # Close button buat overlay navigation (checkpoint 3)
        self.button_x_navigation = Button(
            "UI/button_x.png", "UI/button_x_hover.png",
            x=(GameSettings.SCREEN_WIDTH // 2) + 200,
            y=(GameSettings.SCREEN_HEIGHT // 2) - 230,
            width=40,
            height=40,
            on_click=self.close_navigation_overlay
        )
        self.navigation_overlay.add_child(self.button_x_navigation)

        # Save Button
        self.button_save = Button(
            img_path="UI/button_save.png",
            img_hovered_path="UI/button_save_hover.png",
            x=(GameSettings.SCREEN_WIDTH // 2 - 190),
            y=(GameSettings.SCREEN_HEIGHT // 2 + 20),
            width=75,
            height=75,
            on_click=self.save_game
        )
        self.setting_overlay.add_child(self.button_save)

        # Load Button
        self.button_load = Button(
            img_path="UI/button_load.png",
            img_hovered_path="UI/button_load_hover.png",
            x=(GameSettings.SCREEN_WIDTH // 2 - 100),
            y=(GameSettings.SCREEN_HEIGHT // 2 + 20),
            width=75,
            height=75,
            on_click=self.load_game
        )
        self.setting_overlay.add_child(self.button_load)

        # sell button (checkpoint 3)
        self.button_sell = Button(
            img_path="UI/button_shop.png",
            img_hovered_path="UI/button_shop_hover.png",
            x=(GameSettings.SCREEN_WIDTH // 2 - 150),
            y=(GameSettings.SCREEN_HEIGHT // 2 + 200),
            width=45, height=45,
            on_click=self.sell_selected_monster
        )
        self.shop_overlay.add_child(self.button_sell)

        # buy button (checkpoint 3)
        self.button_buy = Button(
            img_path="UI/button_shop.png",
            img_hovered_path="UI/button_shop_hover.png",
            x=(GameSettings.SCREEN_WIDTH // 2 + 150),
            y=(GameSettings.SCREEN_HEIGHT // 2 + 200),
            width=45, height=45,
            on_click=self.buy_selected_item
        )
        self.shop_overlay.add_child(self.button_buy)

        # Checkbox for mute
        self.checkbox_mute = Checkbox(
            x=(GameSettings.SCREEN_WIDTH // 2 - 190),
            y=(GameSettings.SCREEN_HEIGHT // 2 - 40),
            size=24,
            checked=GameSettings.MUTE,
            label="Mute Audio"
        )
        self.setting_overlay.add_child(self.checkbox_mute)

        # Slider for volume
        self.slider_volume = Slider(
            x=(GameSettings.SCREEN_WIDTH // 2 - 190),
            y=(GameSettings.SCREEN_HEIGHT // 2 - 80),
            width=200,
            value=GameSettings.AUDIO_VOLUME
        )
        self.setting_overlay.add_child(self.slider_volume)

        self.show_setting_overlay = False
        self.show_backpack_overlay = False
        self.show_shop_overlay = False
        self.show_navigation_overlay = False

        # Backpack list layout (buat ngegambar, 2 kolom)
        self.monster_column_x = 400
        self.item_column_x = GameSettings.SCREEN_WIDTH // 2 + 40
        self.list_top_y = 200
        self.list_spacing = 60
        self._sprite_cache = {}

        # checkpoint 3
        self.selected_monster_index = None
        self.selected_item_index = None

        self.navigation_buttons = []

    @override
    def enter(self) -> None:
        sound_manager.play_bgm("RBY 103 Pallet Town.ogg")
        if self.online_manager:
            self.online_manager.enter()
        
    @override
    def exit(self) -> None:
        if self.online_manager:
            self.online_manager.exit()
        
    @override
    def update(self, dt: float):
        # checkpoint 3
        self.game_manager.update_navigation()

        # Cek ada next scene ga
        self.game_manager.try_switch_map()

        # Update button setting
        self.setting_button.update(dt)

        # Update button backpack
        self.backpack_button.update(dt)

        # Update button navigation (checkpoint 3)
        self.navigation_button.update(dt)

        # Update overlay button kalau overlay setting dibuka
        if self.show_setting_overlay:
            self.setting_overlay.update(dt)

            # update volume dan mute setting
            GameSettings.AUDIO_VOLUME = self.slider_volume.get_value()
            GameSettings.MUTE = self.checkbox_mute.is_checked()
            sound_manager.apply_settings()
            
            return # biar player ga bisa gerak di belakang overlay
        
        # Update overlay kalau overlay backpack dibuka
        if self.show_backpack_overlay:
            self.backpack_overlay.update(dt)
            return # biar player ga bisa gerak di belakang overlay
        
        # checkpoint 3
        # Update overlay kalau overlay shop dibuka
        if self.show_shop_overlay:
            self.shop_overlay.update(dt)
            return # biar player ga bisa gerak di belakang overlay
        
        # checkpoint 3
        # Update overlay kalau overlay navigation dibuka
        if self.show_navigation_overlay:
            self.navigation_overlay.update(dt)
            return # biar player ga bisa gerak di belakang overlay

        # Update player dan enemy
        if self.game_manager.player:
            self.game_manager.player.update(dt)
        for enemy in self.game_manager.current_enemy_trainers:
            enemy.update(dt)

        # Update shop keepers (checkpoint 3)
        for shop_keeper in self.game_manager.current_shop_keepers:
            shop_keeper.update(dt)
            
        # Update others
        self.game_manager.bag.update(dt)
        
        if self.game_manager.player is not None and self.online_manager is not None:
            _ = self.online_manager.update(
                self.game_manager.player.position.x, 
                self.game_manager.player.position.y,
                self.game_manager.current_map.path_name
            )
    
    # buka tutup overlay
    def open_setting_overlay(self):
        if self.show_backpack_overlay or self.show_shop_overlay or self.show_navigation_overlay:
            return

        self.show_setting_overlay = True
        self.setting_overlay.show()
        
        # Sync overlay UI dari global settings
        self.slider_volume.value = GameSettings.AUDIO_VOLUME
        self.checkbox_mute.checked = GameSettings.MUTE

    def open_backpack_overlay(self):
        if self.show_setting_overlay or self.show_shop_overlay or self.show_navigation_overlay:
            return

        self.show_backpack_overlay = True
        self.backpack_overlay.show()

    # checkpoint 3
    def open_shop_overlay(self):
        if self.show_setting_overlay or self.show_backpack_overlay or self.show_navigation_overlay:
            return

        self.show_shop_overlay = True
        self.shop_overlay.show()

    def open_navigation_overlay(self):
        if self.show_setting_overlay or self.show_backpack_overlay or self.show_shop_overlay:
            return
        
        self.show_navigation_overlay = True
        self.navigation_overlay.show()

        # Clear tombol
        self.navigation_overlay.children = []
        self.navigation_overlay.add_child(self.button_x_navigation)

        gm = self.game_manager
        current_map = gm.current_map
        #Logger.info(f"Loading navigation destinations in {current_map.path_name} for overlay")

        bx = self.navigation_overlay.x + 40
        by = self.navigation_overlay.y + 80
        bw, bh = 300, 40

        # Load destinations untuk *current* map
        destinations = current_map.navigation_destinations
        #Logger.info(f"Found {len(destinations)} navigation destinations")

        for dest in destinations:
            place_name = dest["place_name"]

            label = text_overlay_font.render(place_name, False, (0, 0, 0))
            label_rect = label.get_rect(topleft=(bx + 10, by + 10))

            def make_handler(name=place_name):
                def handler():
                    self.start_navigation_to_place(name)
                return handler

            btn = Button(
                "UI/raw/UI_Flat_Button01a_4.png",
                "UI/raw/UI_Flat_Button01a_1.png",
                x=bx,
                y=by,
                width=bw,
                height=bh,
                on_click=make_handler()
            )

            self.navigation_overlay.add_child(btn)
            self.navigation_overlay.add_child([label, label_rect])
            self.navigation_buttons.append(btn)

            by += bh + 12

    def close_setting_overlay(self):
        self.show_setting_overlay = False
        self.setting_overlay.hide()

        # Sync overlay UI dari global settings
        self.slider_volume.value = GameSettings.AUDIO_VOLUME
        self.checkbox_mute.checked = GameSettings.MUTE

    def close_backpack_overlay(self):
        self.show_backpack_overlay = False
        self.backpack_overlay.hide()

    def close_shop_overlay(self):
        self.show_shop_overlay = False
        self.shop_overlay.hide()

    def close_navigation_overlay(self):
        self.show_navigation_overlay = False
        self.navigation_overlay.hide()

    @override
    def draw(self, screen: pg.Surface):        
        if self.game_manager.player:
            '''
            [TODO HACKATHON 3]
            Implement the camera algorithm logic here
            Right now it's hard coded, you need to follow the player's positions
            you may use the below example, but the function still incorrect, you may trace the entity.py
            
            camera = self.game_manager.player.camera
            '''
            camera = self.game_manager.player.camera
            self.game_manager.current_map.draw(screen, camera)
            self.game_manager.player.draw(screen, camera)
        else:
            camera = PositionCamera(0, 0)
            self.game_manager.current_map.draw(screen, camera)

        for enemy in self.game_manager.current_enemy_trainers:
            enemy.draw(screen, camera)

        for shop_keeper in self.game_manager.current_shop_keepers: # checkpoint 3
            shop_keeper.draw(screen, camera)

        self.game_manager.bag.draw(screen)
        
        if self.online_manager and self.game_manager.player:
            list_online = self.online_manager.get_list_players()
            for player in list_online:
                if player["map"] == self.game_manager.current_map.path_name:
                    cam = self.game_manager.player.camera
                    pos = cam.transform_position_as_position(Position(player["x"], player["y"]))
                    self.sprite_online.update_pos(pos)
                    self.sprite_online.draw(screen)

        # selalu bikin setting button
        self.setting_button.draw(screen)

        # selalu bikin backpack button
        self.backpack_button.draw(screen)

        # selalu bikin navigation button (checkpoint 3)
        self.navigation_button.draw(screen)
        navigation_label = minecraft_font.render("Nav List", False, (0, 0, 0))
        screen.blit(navigation_label, (GameSettings.SCREEN_WIDTH - 195, 18))

        # Bikin layar overlay setting kalo dibuka
        if self.show_setting_overlay:
            self.setting_overlay.draw(screen)

            # judul settings
            title_text = title_font.render("Settings", False, (0, 0, 0))
            title_rect = title_text.get_rect(center=(GameSettings.SCREEN_WIDTH // 2 - 180, GameSettings.SCREEN_HEIGHT // 2 - 165))
            screen.blit(title_text, title_rect)

            # Labels buat slider volume
            vol_text = minecraft_font.render(f"Volume: {int(self.slider_volume.get_value() * 100)}%", False, (0, 0, 0))
            screen.blit(vol_text, (GameSettings.SCREEN_WIDTH // 2 - 190,
                                GameSettings.SCREEN_HEIGHT // 2 - 110))
            
        # Bikin layar overlay backpack kalo dibuka
        elif self.show_backpack_overlay:
            self.backpack_overlay.draw(screen)

            # judul backpack
            title_text = title_font.render("Backpack", False, (0, 0, 0))
            title_rect = title_text.get_rect(center=(GameSettings.SCREEN_WIDTH // 2 - 160, GameSettings.SCREEN_HEIGHT // 2 - 190))
            screen.blit(title_text, title_rect)

            # gambar list monster
            self.draw_monster_list(screen)

            # gambar list item
            self.draw_item_list(screen)

        # bikin layar overlay shop kalo dibuka (checkpoint 3)
        elif self.show_shop_overlay:
            self.shop_overlay.draw(screen)

            # judul shop
            title_text = title_font.render("Shop", False, (0, 0, 0))
            title_rect = title_text.get_rect(center=(GameSettings.SCREEN_WIDTH // 2 - 200, GameSettings.SCREEN_HEIGHT // 2 - 210))
            screen.blit(title_text, title_rect)

            # gambar list monster
            self.draw_monster_list(screen)

            # gambar list item
            self.draw_item_list(screen)

            # label sell/buy
            sell_label = text_overlay_font.render("Sell", False, (0, 0, 0))
            screen.blit(sell_label, (GameSettings.SCREEN_WIDTH // 2 - 200, GameSettings.SCREEN_HEIGHT // 2 + 210))
            buy_label = text_overlay_font.render("Buy", False, (0, 0, 0))
            screen.blit(buy_label, (GameSettings.SCREEN_WIDTH // 2 + 100, GameSettings.SCREEN_HEIGHT // 2 + 210))

        # bikin layar overlay navigation kalo dibuka (checkpoint 3)
        elif self.show_navigation_overlay:
            self.navigation_overlay.draw(screen)

            # judul navigation
            title_text = title_font.render("Navigation", False, (0, 0, 0))
            title_rect = title_text.get_rect(center=(GameSettings.SCREEN_WIDTH // 2 - 150, GameSettings.SCREEN_HEIGHT // 2 - 210))
            screen.blit(title_text, title_rect)

    def _get_bag_lists(self):
        """
        Return tuple (monsters_list, items_list).
        Handles:
         - bag as dict with keys "monsters"/"items"
         - bag as object with attributes .monsters / .items
         - bag as object with method to_dict()
         - bag as object with get_monsters()/get_items()
        Always returns lists (possibly empty).
        """
        bag = getattr(self.game_manager, "bag", None)

        # None
        if bag is None:
            return [], []

        # kalau bentuk dict dari JSON
        if isinstance(bag, dict):
            monsters = bag.get("monsters", []) or []
            items = bag.get("items", []) or []
            return monsters, items

        # kalau to_dict yang return dict
        if hasattr(bag, "to_dict") and callable(getattr(bag, "to_dict")):
            try:
                d = bag.to_dict()
                if isinstance(d, dict):
                    monsters = d.get("monsters", []) or []
                    items = d.get("items", []) or []
                    return monsters, items
            except Exception:
                pass

        # Kalau atribut monsters/items
        if hasattr(bag, "monsters") or hasattr(bag, "items"):
            monsters = getattr(bag, "monsters", []) or []
            items = getattr(bag, "items", []) or []
            return monsters, items

        # Kalau object expose getter methods
        if hasattr(bag, "get_monsters") or hasattr(bag, "get_items"):
            try:
                monsters = bag.get_monsters() if hasattr(bag, "get_monsters") else []
                items = bag.get_items() if hasattr(bag, "get_items") else []
                return monsters or [], items or []
            except Exception:
                pass

        return monsters, items
    
    def _load_cached_sprite(self, path, size):
        if not path:
            return None

        key = f"{path}:{size}"
        if key in self._sprite_cache:
            return self._sprite_cache[key]

        # load dari: assets/images/<path_from_json>
        full_path = f"assets/images/{path}"

        try:
            surf = pg.image.load(full_path).convert_alpha()
            surf = pg.transform.scale(surf, size)
            self._sprite_cache[key] = surf
            print("[LOADED SPRITE]", full_path)
            return surf
        except Exception as e:
            # Print gagal sekali aja
            seen = getattr(self, "_failed_sprites", set())
            if path not in seen:
                seen.add(path)
                setattr(self, "_failed_sprites", seen)
                print("[FAILED TO LOAD SPRITE]", full_path, "error:", e)
            return None

    def draw_monster_list(self, screen):
        monsters, _ = self._get_bag_lists()

        x = self.monster_column_x
        y = self.list_top_y

        # kalau ga ada monster
        if not monsters:
            hint = text_overlay_font.render("(no monsters)", False, (100, 100, 100))
            screen.blit(hint, (x, y))
            return
        
        # load mini banner once
        mini_banner = self._load_cached_sprite("UI/raw/UI_Flat_Banner03a.png", (200, 50))

        for m in monsters:
            if isinstance(m, dict): # takutnya bukan dict
                sprite_path = m.get("sprite_path")
                name = m.get("name", "Unknown")
                level = m.get("level", "?")
                hp = m.get("hp", "?")
                max_hp = m.get("max_hp", "?")
            else:
                sprite_path = getattr(m, "sprite_path", None)
                name = getattr(m, "name", "Unknown")
                level = getattr(m, "level", "?")
                hp = getattr(m, "hp", "?")
                max_hp = getattr(m, "max_hp", "?")
            
            # gambar mini banner di belakang
            if mini_banner:
                screen.blit(mini_banner, (x, y))
            
            sprite = self._load_cached_sprite(sprite_path, (40, 40))
            if sprite:
                screen.blit(sprite, (x+10, y))

            # name + level
            name_text = text_overlay_font.render(f"{name}  Lv:{level}", False, (0, 0, 0))
            screen.blit(name_text, (x + 60, y + 5))

            # HP
            hp_text = text_overlay_font.render(f"HP: {hp}/{max_hp}", False, (0, 0, 0))
            screen.blit(hp_text, (x + 60, y + 25))

            # checkpoint 3
            # highlight selected monster
            row_rect = pg.Rect(self.monster_column_x, y, 200, 50)
            
            if row_rect.collidepoint(pg.mouse.get_pos()):
                highlight_surf = pg.Surface((200, 50), pg.SRCALPHA)
                highlight_surf.fill((255, 255, 0, 50))  # yellow highlight with alpha
                screen.blit(highlight_surf, (self.monster_column_x, y))
                
                if pg.mouse.get_pressed()[0]:  # left click
                    self.selected_monster_index = monsters.index(m)

            y += self.list_spacing

    def draw_item_list(self, screen):
        _, items = self._get_bag_lists()

        x = self.item_column_x
        y = self.list_top_y

        # kalau ga ada item
        if not items:
            hint = text_overlay_font.render("(no items)", False, (100, 100, 100))
            screen.blit(hint, (x, y))
            return

        for it in items:
            if isinstance(it, dict):
                sprite_path = it.get("sprite_path")
                name = it.get("name", "Unknown")
                count = it.get("count", 0)
            else:
                sprite_path = getattr(it, "sprite_path", None)
                name = getattr(it, "name", "Unknown")
                count = getattr(it, "count", 0)

            sprite = self._load_cached_sprite(sprite_path, (40, 40))
            if sprite:
                screen.blit(sprite, (x, y))

            text = text_overlay_font.render(f"{name} x{count}", False, (0, 0, 0))
            screen.blit(text, (x + 50, y + 10))
            y += self.list_spacing

            # checkpoint 3
            # highlight selected item
            row_rect = pg.Rect(self.item_column_x, y - self.list_spacing, 200, 50)
            
            if row_rect.collidepoint(pg.mouse.get_pos()):
                highlight_surf = pg.Surface((200, 50), pg.SRCALPHA)
                highlight_surf.fill((255, 255, 0, 50))  # yellow highlight with alpha
                screen.blit(highlight_surf, (self.item_column_x, y - self.list_spacing))
                
                if pg.mouse.get_pressed()[0]:  # left click
                    self.selected_item_index = items.index(it)

    def save_game(self):
        # Save game state
        self.game_manager.save("saves/game0.json")
        
        # Save global settings kaya volume/mute
        settings_data = {
            "volume": GameSettings.AUDIO_VOLUME,
            "mute": GameSettings.MUTE
        }
        with open("saves/settings.json", "w") as f:
            import json
            json.dump(settings_data, f, indent=2)
        
        Logger.info("Game and settings saved!")

    def load_game(self):
        # Load game state
        manager = GameManager.load("saves/game0.json")
        if manager:
            self.game_manager = manager
            Logger.info("Game loaded successfully!")
        
        # Load global settings
        settings_path = "saves/settings.json"
        if os.path.exists(settings_path):
            with open(settings_path, "r") as f:
                settings_data = json.load(f)
            GameSettings.AUDIO_VOLUME = settings_data.get("volume", 0.5)
            GameSettings.MUTE = settings_data.get("mute", False)
            sound_manager.apply_settings()
            # Update overlay UI sliders/checkbox
            self.slider_volume.value = GameSettings.AUDIO_VOLUME
            self.checkbox_mute.checked = GameSettings.MUTE
            Logger.info("Settings loaded successfully!")

    # chekpoint 3
    def sell_selected_monster(self):
        monsters, _ = self._get_bag_lists()
        idx = self.selected_monster_index

        if idx is None or idx < 0 or idx >= len(monsters):
            Logger.warning("No monster selected.")
            return

        if len(monsters) == 1:
            return # minimal 1 monster harus ada

        monster = monsters[idx]

        # Sell value = level * 10 coins
        level = monster["level"] if isinstance(monster, dict) else monster.level
        coins_earned = level * 10

        # Ilangin monster
        if isinstance(self.game_manager.bag.monsters, list):
            self.game_manager.bag.monsters.pop(idx)
        else:
            Logger.error("Bag monsters structure unexpected.")

        # Tambah coins
        self.game_manager.bag.add_item("Coins", coins_earned, "ingame_ui/coin.png")

        Logger.info(f"Sold {monster['name']} for {coins_earned} coins!")

        self.selected_monster_index = None

    def buy_selected_item(self):
        _, items = self._get_bag_lists()
        idx = self.selected_item_index

        if idx is None or idx < 0 or idx >= len(items):
            Logger.info("No item selected.")
            return
        
        item = items[idx]
        item_name = item["name"] if isinstance(item, dict) else item.name
        
        if item_name == "Coins":
            Logger.info("Cannot buy Coins!")
            return

        # Cari coins
        coin_item = None
        for it in items:
            name = it["name"] if isinstance(it, dict) else it.name
            if name == "Coins":
                coin_item = it
                break

        if coin_item is None:
            Logger.warning("You have no Coins!")
            return

        coins = coin_item["count"] if isinstance(coin_item, dict) else coin_item.count
        cost = 20  # potion cost

        if coins < cost:
            Logger.warning("Not enough coins!")
            return

        # Kurangin coins
        if isinstance(coin_item, dict):
            coin_item["count"] -= cost
        else:
            coin_item.count -= cost

        # Kasih item
        if item_name[-6:] == "Potion":
            sprite_path = "ingame_ui/potion.png"
        else:
            sprite_path = "ingame_ui/ball.png"
        self.game_manager.bag.add_item(item_name, 1, sprite_path)

        Logger.info("Bought 1 Potion for 20 coins!")

    def start_navigation_to_place(self, place_name: str):
        gm = self.game_manager
        #Logger.info(f"Start navigation to place {place_name} in {gm.current_map.path_name}")

        gm.navigate_to(place_name)

        self.close_navigation_overlay()