# checkpoint 2
import pygame as pg
import random

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

# enemy bakal milih random pokemon dari daftar ini
ENEMY_MONSTER_POOL = [
    {"name": "Zubat", "hp": 40, "max_hp": 40, "level": 5, "sprite_path": "menu_sprites/menusprite1.png"},
    {"name": "Geodude", "hp": 60, "max_hp": 60, "level": 8, "sprite_path": "menu_sprites/menusprite2.png"},
    {"name": "Pidgey", "hp": 50, "max_hp": 50, "level": 6, "sprite_path": "menu_sprites/menusprite3.png"},
]

class BattleScene(Scene):

    _pending_enemy = None     # tempat EnemyTrainer disimpen sebelum masuk

    def __init__(self):
        super().__init__()
        self.enemy = None
        self.game_manager = None   # SceneManager bakal inject

        self.background = BackgroundSprite("backgrounds/background1.png")

        # turn state: "player", "enemy", "win", "lose"
        self.turn = "player"

        # monsters (dictionaries)
        self.player_monster = None
        self.enemy_monster = None

        # text di button
        self.btn_run_text = "Run"

        # buttons
        btn_w, btn_h = 150, 50
        y = 600

        self.btn_run = Button(
            img_path="UI/raw/UI_Flat_Button01a_4.png",
            img_hovered_path="UI/raw/UI_Flat_Button01a_1.png",
            x=100, y=y,
            width=btn_w, height=btn_h,
            on_click=self.on_run
        )

        self.btn_attack = Button(
            img_path="UI/raw/UI_Flat_Button01a_4.png",
            img_hovered_path="UI/raw/UI_Flat_Button01a_1.png",
            x=300, y=y,
            width=btn_w, height=btn_h,
            on_click=self.on_attack
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

        # setup player monster (ambil dari game_manager.player.bag)
        self.player_monster = self.game_manager.bag.monsters[0]  # ambil monster pertama

        # choose enemy monster
        self.enemy_monster = random.choice(ENEMY_MONSTER_POOL).copy()

        # log info buat debug
        Logger.info(f"[BATTLE] Player uses {self.player_monster['name']} ({self.player_monster['hp']} HP)")
        Logger.info(f"[BATTLE] Enemy uses {self.enemy_monster['name']} ({self.enemy_monster['hp']} HP)")
    
        self.turn = "player" # dua kali biar aman
    
    def exit(self):
        Logger.info("[BATTLE] Exiting BattleScene")
        self.enemy = None
    
    def on_run(self): # player run
        Logger.info("[BATTLE] Run button clicked, returning to game scene")
        scene_manager.change_scene("game")

    def on_attack(self): # player attack
        if self.turn != "player":
            return  # bukan giliran player

        dmg = 10  # damage tetap 10 biar simpel
        self.enemy_monster['hp'] -= dmg
        Logger.info(f"[BATTLE] Player's {self.player_monster['name']} attacks! Enemy's {self.enemy_monster['name']} takes {dmg} damage (HP left: {self.enemy_monster['hp']})")

        if self.enemy_monster['hp'] <= 0:
            Logger.info(f"[BATTLE] Enemy's {self.enemy_monster['name']} fainted! You win!")
            self.turn = "win"
            return

        # ganti giliran ke enemy
        self.turn = "enemy"
        #self.enemy_attack()

    def enemy_attack_logic(self):
        dmg = 8 # damage tetap 8 biar simpel, lebih kecil biar gampang menang
        self.player_monster["hp"] -= dmg
        Logger.info(f"[BATTLE] Enemy deals {dmg} damage")

        if self.player_monster["hp"] <= 0:
            self.turn = "lose"
            Logger.info("[BATTLE] Player monster fainted!")
            return

        self.turn = "player"

    def update(self, dt):
        
        # enemy turn logic langsung serang
        if self.turn == "enemy":
            self.enemy_attack_logic()
            return

        # buttons muncul kalau player turn
        if self.turn == "player":
            self.btn_run.update(dt)
            self.btn_attack.update(dt)

        if self.turn in ["win", "lose"]:
            self.btn_run.update(dt)  # pake tombol run buat keluar

    def draw_hp_bar(self, screen, x, y, w, h, hp, max_hp):
        ratio = max(hp / max_hp, 0)
        pg.draw.rect(screen, (0, 0, 0), (x, y, w, h), 2)
        pg.draw.rect(screen, (255, 0, 0), (x+2, y+2, int((w-4) * ratio), h-4))


    def draw(self, screen):
        # Gambar background
        self.background.draw(screen)

        # label tombol
        player_text = minecraft_font.render(
            f"{self.player_monster['name']}  HP: {self.player_monster['hp']}",
            True, (255, 255, 255)
        )
        enemy_text = minecraft_font.render(
            f"{self.enemy_monster['name']}  HP: {self.enemy_monster['hp']}",
            True, (255, 255, 255)
        )

        screen.blit(player_text, (50, 350))
        screen.blit(enemy_text, (450, 150))

        # HP bars
        self.draw_hp_bar(screen, 50, 380, 200, 20,
                         self.player_monster["hp"], self.player_monster["max_hp"])
        self.draw_hp_bar(screen, 450, 180, 200, 20,
                         self.enemy_monster["hp"], self.enemy_monster["max_hp"])

        # Gambar tombol
        if self.turn == "player":
            self.btn_run.draw(screen)
            run_label = minecraft_font.render("Run", True, (0, 0, 0))
            screen.blit(run_label, run_label.get_rect(center=self.btn_run.hitbox.center))

            self.btn_attack.draw(screen)
            atk_label = minecraft_font.render("Attack", True, (0, 0, 0))
            screen.blit(atk_label, atk_label.get_rect(center=self.btn_attack.hitbox.center))

        # WIN/LOSE screens
        if self.turn == "win":
            txt = minecraft_font.render("You Win!", True, (255, 255, 0))
            screen.blit(txt, (350, 300))

        if self.turn == "lose":
            txt = minecraft_font.render("You Lose!", True, (255, 0, 0))
            screen.blit(txt, (350, 300))

        if self.turn in ["win", "lose"]:
            self.btn_run.draw(screen) # pake tombol run buat keluar
            run_label = minecraft_font.render("Return", True, (0, 0, 0))
            screen.blit(run_label, run_label.get_rect(center=self.btn_run.hitbox.center))
