import pygame as pg
import threading
import time

from src.scenes.scene import Scene
from src.core import GameManager, OnlineManager
from src.utils import Logger, PositionCamera, GameSettings, Position
from src.core.services import sound_manager
from src.sprites import Sprite
from src.interface.components.overlay import OverlayPanel
from src.interface.components import Button
from src.interface.components.checkbox import Checkbox
from src.interface.components.slider import Slider
from typing import override

pg.init()

# untuk ngatur font
pg.font.init()
minecraft_font = pg.font.Font('assets/fonts/Minecraft.ttf', 20) # text size 20
title_font = pg.font.Font('assets/fonts/Minecraft.ttf', 30) # text size 30
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
        
        # Menu Button buat buka overlay (Checkpoint 2 To do 01)
        w, h = 560, 450
        x = (GameSettings.SCREEN_WIDTH - w) // 2
        y = (GameSettings.SCREEN_HEIGHT - h) // 2

        # Load background overlay
        self.overlay_bg = pg.image.load(
            "assets/images/UI/raw/UI_Flat_FrameSlot03a.png"
        ).convert_alpha()

        # Scale sampai sesuai ukuran overlay panel
        self.overlay_bg = pg.transform.scale(self.overlay_bg, (w, h))

        self.overlay = OverlayPanel(x, y, w, h, background_image=self.overlay_bg)

        self.setting_button = Button(
            "UI/button_setting.png",
            "UI/button_setting_hover.png",
            x=GameSettings.SCREEN_WIDTH - 48,
            y=8,
            width=40,
            height=40,
            on_click=self.open_overlay
        )

        # Close button buat overlay
        self.button_x = Button(
            "UI/button_x.png", "UI/button_x_hover.png",
            x=(GameSettings.SCREEN_WIDTH // 2) + 200,
            y=(GameSettings.SCREEN_HEIGHT // 2) - 190,
            width=40,
            height=40,
            on_click=self.close_overlay
        )
        self.overlay.add_child(self.button_x)

        # Checkbox for mute
        self.checkbox_mute = Checkbox(
            x=(GameSettings.SCREEN_WIDTH // 2 - 190),
            y=(GameSettings.SCREEN_HEIGHT // 2 - 40),
            size=24,
            checked=GameSettings.MUTE,
            label="Mute Audio"
        )
        self.overlay.add_child(self.checkbox_mute)

        # Slider for volume
        self.slider_volume = Slider(
            x=(GameSettings.SCREEN_WIDTH // 2 - 190),
            y=(GameSettings.SCREEN_HEIGHT // 2 - 80),
            width=200,
            value=GameSettings.AUDIO_VOLUME
        )
        self.overlay.add_child(self.slider_volume)

        self.show_overlay = False

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
        # Check if there is assigned next scene
        self.game_manager.try_switch_map()

        # Update button menu
        self.setting_button.update(dt)

        # Update overlay button kalau overlay dibuka
        if self.show_overlay:
            self.overlay.update(dt)

            # update volume dan mute setting
            GameSettings.AUDIO_VOLUME = self.slider_volume.get_value()
            GameSettings.MUTE = self.checkbox_mute.is_checked()
            sound_manager.apply_settings()
            
            return # biar player ga bisa gerak di belakang overlay

        # Update player and other data
        if self.game_manager.player:
            self.game_manager.player.update(dt)
        for enemy in self.game_manager.current_enemy_trainers:
            enemy.update(dt)
            
        # Update others
        self.game_manager.bag.update(dt)
        
        if self.game_manager.player is not None and self.online_manager is not None:
            _ = self.online_manager.update(
                self.game_manager.player.position.x, 
                self.game_manager.player.position.y,
                self.game_manager.current_map.path_name
            )

    
    # buka tutup overlay
    def open_overlay(self):
        self.show_overlay = True
        self.overlay.show()
        
        # Sync overlay UI to current global settings
        self.slider_volume.value = GameSettings.AUDIO_VOLUME
        self.checkbox_mute.checked = GameSettings.MUTE

    def close_overlay(self):
        self.show_overlay = False
        self.overlay.hide()

        # Sync overlay UI to current global settings
        self.slider_volume.value = GameSettings.AUDIO_VOLUME
        self.checkbox_mute.checked = GameSettings.MUTE
        
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

        self.game_manager.bag.draw(screen)
        
        if self.online_manager and self.game_manager.player:
            list_online = self.online_manager.get_list_players()
            for player in list_online:
                if player["map"] == self.game_manager.current_map.path_name:
                    cam = self.game_manager.player.camera
                    pos = cam.transform_position_as_position(Position(player["x"], player["y"]))
                    self.sprite_online.update_pos(pos)
                    self.sprite_online.draw(screen)

        # selalu bikin menu button
        self.setting_button.draw(screen)

        # Bikin layar overlay kalo dibuka
        if self.show_overlay:
            self.overlay.draw(screen)

            # judul settings
            title_text = title_font.render("Settings", False, (0, 0, 0))
            title_rect = title_text.get_rect(center=(GameSettings.SCREEN_WIDTH // 2 - 180, GameSettings.SCREEN_HEIGHT // 2 - 165))
            screen.blit(title_text, title_rect)

            # Labels buat slider volume
            vol_text = minecraft_font.render(f"Volume: {int(self.slider_volume.get_value() * 100)}%", False, (0, 0, 0))
            screen.blit(vol_text, (GameSettings.SCREEN_WIDTH // 2 - 190,
                                GameSettings.SCREEN_HEIGHT // 2 - 110))
