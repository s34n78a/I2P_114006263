'''
[TODO HACKATHON 5] 
Try to mimic the menu_scene.py or game_scene.py to create this new scene
'''
import pygame as pg

from src.utils import GameSettings, Logger
from src.sprites import BackgroundSprite
from src.scenes.scene import Scene
from src.interface.components.overlay import OverlayPanel
from src.interface.components import Button
from src.interface.components.checkbox import Checkbox
from src.interface.components.slider import Slider
from src.core.services import scene_manager, sound_manager, input_manager

pg.init()

# untuk ngatur font
pg.font.init()
minecraft_font = pg.font.Font('assets/fonts/Minecraft.ttf', 20) # text size 20
title_font = pg.font.Font('assets/fonts/Minecraft.ttf', 30) # text size 30
pokemon_font = pg.font.Font('assets/fonts/Pokemon Solid.ttf', 20) # text size 20

class SettingScene(Scene):
    def __init__(self):
        super().__init__()
        self.background = BackgroundSprite("backgrounds/background1.png")
        Logger.info("SettingScene initialized")

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

        # Bikin "Back" button
        self.btn_back = Button(
            img_path="UI/button_back.png",
            img_hovered_path="UI/button_back_hover.png",
            x=GameSettings.SCREEN_WIDTH // 2 - 200,
            y=GameSettings.SCREEN_HEIGHT // 2 + 90,
            width=75,
            height=75,
            on_click=self.on_back_clicked
        )
        self.overlay.add_child(self.btn_back)

        # Close button buat overlay
        self.button_x = Button(
            "UI/button_x.png", "UI/button_x_hover.png",
            x=(GameSettings.SCREEN_WIDTH // 2) + 200,
            y=(GameSettings.SCREEN_HEIGHT // 2) - 190,
            width=40,
            height=40,
            on_click=self.on_back_clicked
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
        self.overlay.show()

    def on_back_clicked(self):
        Logger.info("Back to menu clicked")
        scene_manager.change_scene("menu")

    def update(self, dt: float):
        self.btn_back.update(dt)
        self.overlay.update(dt)

        # Update mute setting
        GameSettings.MUTE = self.checkbox_mute.is_checked()

        # Update volume setting
        GameSettings.AUDIO_VOLUME = self.slider_volume.get_value()
        
        sound_manager.apply_settings()

    def draw(self, screen: pg.Surface):
        self.background.draw(screen)

        self.overlay.draw(screen)

        # judul settings
        title_text = title_font.render("Settings", False, (0, 0, 0))
        title_rect = title_text.get_rect(center=(GameSettings.SCREEN_WIDTH // 2 - 180, GameSettings.SCREEN_HEIGHT // 2 - 165))
        screen.blit(title_text, title_rect)

        # Labels buat slider volume
        vol_text = minecraft_font.render(f"Volume: {int(self.slider_volume.get_value() * 100)}%", False, (0, 0, 0))
        screen.blit(vol_text, (GameSettings.SCREEN_WIDTH // 2 - 190,
                                GameSettings.SCREEN_HEIGHT // 2 - 110))