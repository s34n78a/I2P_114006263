import pygame as pg

from src.sprites import BackgroundSprite
from src.scenes.scene import Scene
from src.core.services import scene_manager
from src.utils import Logger

from src.interface.components.button import Button

pg.init()

# untuk ngatur font
pg.font.init()
minecraft_font = pg.font.Font('assets/fonts/Minecraft.ttf', 20) # text size 20
title_font = pg.font.Font('assets/fonts/Minecraft.ttf', 30) # text size 30
pokemon_font = pg.font.Font('assets/fonts/Pokemon Solid.ttf', 20) # text size 20

class BattleScene(Scene):

    _pending_enemy = None     # tempat EnemyTrainer disimpen sebelum masuk

    def __init__(self):
        super().__init__()
        self.enemy = None
        self.battle_manager = None
        self.game_manager = None   # SceneManager bakal inject

        # Battle message
        self.battle_text = "BATTLE!"
        self.background = BackgroundSprite("backgrounds/background1.png")

        # text di button
        self.btn_back_text = "Run"

        # Button
        btn_width, btn_height = 150, 50
        
        # button run
        btn_x = (800 - btn_width) // 2  # adjust according to screen width
        btn_y = 600  # bottom of the screen
        self.btn_back = Button(
            img_path="UI/raw/UI_Flat_Button01a_4.png",
            img_hovered_path="UI/raw/UI_Flat_Button01a_1.png",
            x=btn_x, y=btn_y,
            width=btn_width, height=btn_height,
            on_click=self.on_back_clicked
        )

    # nanti dipanggil EnemyTrainer sebelum scene switch
    @classmethod
    def prepare(cls, enemy_trainer):
        cls._pending_enemy = enemy_trainer

    # nanti dipanggil SceneManager setelah pindah ke scene ini
    def enter(self):
        Logger.info("[BATTLE] Entering BattleScene")

        # ambil enemy yang pending
        self.enemy = BattleScene._pending_enemy
        BattleScene._pending_enemy = None

        if self.enemy is None:
            Logger.error("[BATTLE] ERROR — no enemy passed into BattleScene")
            scene_manager.change_scene("game")
            return

        # ambil game_manager dari enemy
        self.game_manager = self.enemy.game_manager
        Logger.info(f"[BATTLE] Battle started vs enemy at ({self.enemy.position.x}, {self.enemy.position.y})")

    def exit(self):
        Logger.info("[BATTLE] Exiting BattleScene")
        self.enemy = None
    
    def on_back_clicked(self):
        Logger.info("[BATTLE] Back button clicked, returning to game scene")
        scene_manager.change_scene("game")

    def update(self, dt):
        self.btn_back.update(dt)

        if self.enemy:
            self.enemy.animation.update(dt)

    def draw(self, screen):

        # Draw background
        self.background.draw(screen)

        # Draw battle text
        txt = minecraft_font.render(self.battle_text, True, (255, 255, 255))
        screen.blit(txt, (100, 100))

        # Draw button
        self.btn_back.draw(screen)
        btn_text_surf = minecraft_font.render(self.btn_back_text, True, (0, 0, 0))
        btn_text_rect = btn_text_surf.get_rect(center=self.btn_back.hitbox.center)
        screen.blit(btn_text_surf, btn_text_rect)