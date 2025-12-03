# checkpoint 2
import pygame as pg
import random

from src.sprites import BackgroundSprite
from src.scenes.scene import Scene
from src.core.services import scene_manager
from src.core.managers.game_manager import GameManager
from src.utils import Logger, loader

from src.interface.components.button import Button

pg.init()

# untuk ngatur font
pg.font.init()
minecraft_font = pg.font.Font('assets/fonts/Minecraft.ttf', 20) # text size 20
title_font = pg.font.Font('assets/fonts/Minecraft.ttf', 30) # text size 30
text_font = pg.font.Font('assets/fonts/Minecraft.ttf', 16) # text size 16
pokemon_font = pg.font.Font('assets/fonts/Pokemon Solid.ttf', 20) # text size 20

# enemy bakal milih random pokemon dari daftar ini
ENEMY_MONSTER_POOL = [
    {"name": "Pikachu", "hp": 40, "max_hp": 40, "level": 5, "sprite_path": "menu_sprites/menusprite3.png", "element": "Grass"},
    {"name": "Charizard", "hp": 60, "max_hp": 60, "level": 8, "sprite_path": "menu_sprites/menusprite9.png", "element": "Fire"},
    {"name": "Blastoise", "hp": 50, "max_hp": 50, "level": 6, "sprite_path": "menu_sprites/menusprite14.png", "element": "Water"},
    {"name": "Venusaur",  "hp": 30,  "max_hp": 30, "level": 4, "sprite_path": "menu_sprites/menusprite16.png", "element": "Grass" }
]

class BattleScene(Scene):

    _pending_enemy = None     # tempat EnemyTrainer disimpen sebelum masuk

    def __init__(self):
        super().__init__()
        self.enemy = None
        self.game_manager: GameManager | None = None   # SceneManager bakal inject

        self.background = BackgroundSprite("backgrounds/background1.png")
        self.menu_background = BackgroundSprite("UI/raw/UI_Flat_FrameMarker01a.png")
        self.txt1_x = 100
        self.txt1_y = 550
        self.txt1 = ''
        self.txt2_x = 100
        self.txt2_y = 575
        self.txt2 = ''

        # turn state: "player", "enemy", "win", "lose", "no monsters", "item"
        self.turn = "player"

        # monsters (dictionaries)
        self.player_monster = None
        self.enemy_monster = None

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

        self.btn_catch = Button(
            img_path="UI/raw/UI_Flat_Button01a_4.png",
            img_hovered_path="UI/raw/UI_Flat_Button01a_1.png",
            x=500, y=y,
            width=btn_w, height=btn_h,
            on_click=self.on_catch
        )

        self.btn_switch = Button(
            img_path="UI/raw/UI_Flat_Button01a_4.png",
            img_hovered_path="UI/raw/UI_Flat_Button01a_1.png",
            x=500, y=y,
            width=btn_w, height=btn_h,
            on_click=self.on_switch
        )

        # checkpoint 3
        self.btn_item = Button(
            img_path="UI/raw/UI_Flat_Button01a_4.png",
            img_hovered_path="UI/raw/UI_Flat_Button01a_1.png",
            x=700, y=y,
            width=btn_w, height=btn_h,
            on_click=self.on_item
        )

        self.btn_back = Button(
            img_path="UI/raw/UI_Flat_Button01a_4.png",
            img_hovered_path="UI/raw/UI_Flat_Button01a_1.png",
            x=100, y=y,
            width=btn_w, height=btn_h,
            on_click=self.on_back
        )

        self.btn_health_potion = Button(
            img_path="UI/raw/UI_Flat_Button01a_4.png",
            img_hovered_path="UI/raw/UI_Flat_Button01a_1.png",
            x=300, y=y,
            width=btn_w+20, height=btn_h,
            on_click=self.on_health_potion
        )

        self.btn_strength_potion = Button(
            img_path="UI/raw/UI_Flat_Button01a_4.png",
            img_hovered_path="UI/raw/UI_Flat_Button01a_1.png",
            x=520, y=y,
            width=btn_w+20, height=btn_h,
            on_click=self.on_strength_potion
        )

        self.btn_defense_potion = Button(
            img_path="UI/raw/UI_Flat_Button01a_4.png",
            img_hovered_path="UI/raw/UI_Flat_Button01a_1.png",
            x=740, y=y,
            width=btn_w+20, height=btn_h,
            on_click=self.on_defense_potion
        )

        self.already_catch = False

        # checkpoint 3
        self.player_damage_boost = 0
        self.player_defense_boost = 0
        self.enemy_damage_boost = 0
        self.enemy_defense_boost = 0

        self.change_menu_cooldown = 0.001  # seconds
        self.reset_menu_cooldown = 0.001
        self.ignore_mouse_until_release = False  # block input until the mouse button is released after menu changes

    # nanti dipanggil EnemyTrainer sebelum scene switch
    @classmethod
    def prepare(cls, enemy_trainer):
        cls._pending_enemy = enemy_trainer

    @classmethod
    def prepare_wild(cls, game_manager):
        cls._pending_enemy = "wild" # buat bush
        cls._game_manager = game_manager

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
        if self.enemy == "wild":
            # bush battle
            if not hasattr(BattleScene, "_game_manager") or BattleScene._game_manager is None:
                Logger.error("[BATTLE] Cannot start wild battle — no game manager provided!")
                scene_manager.change_scene("game")
                return
            self.game_manager = BattleScene._game_manager
            BattleScene._game_manager = None  # clear after use
            Logger.info("[BATTLE] Wild encounter started!")
        else:
            # trainer battle
            self.game_manager = self.enemy.game_manager
            Logger.info(f"[BATTLE] Battle started vs trainer at ({self.enemy.position.x}, {self.enemy.position.y})")

        # setup player monster (ambil dari game_manager.player.bag)
        if len(self.game_manager.bag.monsters) == 0: # cek ada monster gak
            Logger.info("[BATTLE] Warning — player has no monsters in bag")
            self.txt1 = 'You have no monsters!'
            self.txt2 = ''
            self.turn = "no monsters"
            return
        
        monster_id = 0  # untuk sekarang, ambil monster pertama
        self.player_monster = self.game_manager.bag.monsters[monster_id]  # ambil monster
        while self.player_monster['hp'] <= 0:  # kalo HP 0, cari monster hidup berikutnya
            monster_id += 1
            if monster_id >= len(self.game_manager.bag.monsters):
                Logger.info("[BATTLE] warning — all player monsters are fainted")
                self.txt1 = 'All your monsters are fainted!'
                self.txt2 = ''
                self.turn = "no monsters"
                return
            self.player_monster = self.game_manager.bag.monsters[monster_id]

        # choose enemy monster
        self.enemy_monster = random.choice(ENEMY_MONSTER_POOL).copy()

        # log info buat debug
        Logger.info(f"[BATTLE] Player uses {self.player_monster['name']} ({self.player_monster['hp']} HP)")
        Logger.info(f"[BATTLE] Enemy uses {self.enemy_monster['name']} ({self.enemy_monster['hp']} HP)")
        
        if self.enemy == "wild":
            self.txt1 = f"A wild {self.enemy_monster['name']} appears!"
        else:
            self.txt1 = f"Enemy uses {self.enemy_monster['name']}"
        self.txt2 = ''
    
        self.turn = "player" # dua kali biar aman
        self.already_catch = False # belum nangkep
    
    def exit(self):
        Logger.info("[BATTLE] Exiting BattleScene")
        self.enemy = None
    
    def on_run(self): # player run
        Logger.info("[BATTLE] Run button clicked, returning to game scene")
        scene_manager.change_scene("game")
        
        # reset boost
        self.player_damage_boost = 0
        self.player_defense_boost = 0
        self.enemy_damage_boost = 0
        self.enemy_defense_boost = 0

    def on_attack(self): # player attack
        if self.turn != "player" and self.change_menu_cooldown > 0:
            return  # bukan giliran player

        its_effective = False
        dmg = int(10 * (100 + self.player_monster['level'])/ 100)  # base damage 10

        if self.player_monster['element'] == "Fire" and self.enemy_monster['element'] == "Grass":
            self.player_damage_boost += 5
            its_effective = True
        elif self.player_monster['element'] == "Water" and self.enemy_monster['element'] == "Fire":
            self.player_damage_boost += 5
            its_effective = True
        elif self.player_monster['element'] == "Grass" and self.enemy_monster['element'] == "Water":
            self.player_damage_boost += 5
            its_effective = True

        elif self.player_monster['element'] == "Grass" and self.enemy_monster['element'] == "Fire":
            self.enemy_defense_boost += 5
        elif self.player_monster['element'] == "Fire" and self.enemy_monster['element'] == "Water":
            self.enemy_defense_boost += 5
        elif self.player_monster['element'] == "Water" and self.enemy_monster['element'] == "Grass":
            self.enemy_defense_boost += 5        

        total_dmg = dmg + self.player_damage_boost - self.enemy_defense_boost

        if total_dmg < 0:
            total_dmg = 0

        self.enemy_monster['hp'] -= total_dmg
        Logger.info(f"[BATTLE] Player's {self.player_monster['name']} attacks! Enemy's {self.enemy_monster['name']} takes {total_dmg} damage (HP left: {self.enemy_monster['hp']})")
        self.txt1 = f"{self.player_monster['name']} attacks! Enemy's {self.enemy_monster['name']} takes {dmg}"
        
        if self.player_damage_boost > 0:
            Logger.info(f"[BATTLE] Player's damage boost of {self.player_damage_boost} applied.")
            self.txt1 += f" + {self.player_damage_boost}"

        if self.enemy_defense_boost > 0:
            Logger.info(f"[BATTLE] Enemy's defense boost of {self.enemy_defense_boost} applied.")
            self.txt1 += f" - {self.enemy_defense_boost}"

        self.txt1 += f" = {total_dmg} damage."

        if its_effective:
            self.txt1 += " It's super effective!"

        self.player_damage_boost = 0  # reset boost setelah dipake
        self.enemy_defense_boost = 0  # reset boost setelah dipake

        if self.enemy_monster['hp'] <= 0:
            self.enemy_monster['hp'] = 0
            Logger.info(f"[BATTLE] Enemy's {self.enemy_monster['name']} fainted! You win!")
            
            if self.enemy == "wild":
                self.txt2 = f"Enemy {self.enemy_monster['name']} fainted! Press Catch to capture."
            else:
                self.txt2 = f"Enemy {self.enemy_monster['name']} fainted! You win!"

            self.turn = "win"
            self.change_menu_cooldown = self.reset_menu_cooldown

            if self.enemy != "wild":
                return  # gak dapet exp kalo lawan wild
            
            # bagi exp ke player monster
            self.player_monster['level'] += 1  # naikin level
            Logger.info(f"[BATTLE] Player's {self.player_monster['name']} leveled up to {self.player_monster['level']}!")
            self.txt2 += f" Your {self.player_monster['name']} leveled up to level {self.player_monster['level']}!"

            return

        # ganti giliran ke enemy
        self.turn = "enemy"
        
    def on_catch(self):
        if self.turn != "win" and self.already_catch and self.change_menu_cooldown > 0:
            return
        
        # check kalau bag udh ada 6 monsters
        if len(self.game_manager.bag.monsters) >= 6:
            Logger.info("[BATTLE] Cannot catch — party is full (6 monsters)")
            self.txt1 = "You can't catch more! Your party is full."
            self.txt2 = ""
            return

        # cek jumlah pokeball
        if not self.game_manager.bag.use_item("Pokeball"):
            Logger.info("[BATTLE] No Pokeballs left!")
            self.txt1 = "No Pokeballs left!"
            self.txt2 = ""
            return

        # clone enemy monster terus restore HP
        caught = self.enemy_monster.copy()
        caught["hp"] = caught["max_hp"]

        # add to bag
        self.game_manager.bag.monsters.append(caught)

        Logger.info(f"[BATTLE] Player caught {self.enemy_monster['name']}!")
        self.txt1 = f"You caught {caught['name']}!"
        self.txt2 = ""
        self.already_catch = True

        self.change_menu_cooldown = self.reset_menu_cooldown

    def on_switch(self):
        if self.turn != "player":
            return  # bukan giliran player

        # cari monster hidup berikutnya
        current_index = self.game_manager.bag.monsters.index(self.player_monster)
        next_index = (current_index + 1) % len(self.game_manager.bag.monsters)
        searched = 0
        while searched < len(self.game_manager.bag.monsters):
            candidate = self.game_manager.bag.monsters[next_index]
            if candidate['hp'] > 0:
                self.player_monster = candidate
                Logger.info(f"[BATTLE] Player switched to {self.player_monster['name']}")
                self.txt1 = f"You switched to {self.player_monster['name']}."
                self.txt2 = ''
                return
            next_index = (next_index + 1) % len(self.game_manager.bag.monsters)
            searched += 1

        Logger.info("[BATTLE] No other alive monsters to switch to!")
        self.txt1 = "No other alive monsters to switch to!"
        self.txt2 = ""

    # checkpoint 3
    def on_item(self):
        if self.turn != "player" and self.change_menu_cooldown > 0:
            return  # bukan giliran player
        
        self.change_menu_cooldown = self.reset_menu_cooldown
        self.turn = "item"
        self.ignore_mouse_until_release = True

        Logger.info("[BATTLE] Item button clicked — Open item menu")
        self.txt1 = "No items implemented yet."
        self.txt2 = ""

    def on_back(self):
        if self.turn != "item" and self.change_menu_cooldown > 0:
            return  # bukan buka item
        
        self.change_menu_cooldown = self.reset_menu_cooldown
        self.turn = "player"
        self.ignore_mouse_until_release = True

        Logger.info("[BATTLE] Back button clicked — Back to battle")
        self.txt1 = "Back to battle."
        self.txt2 = ""

    def on_health_potion(self):
        if self.turn != "item" and self.change_menu_cooldown > 0:
            return  # bukan buka item

        # cek health potion di bag
        if not self.game_manager.bag.use_item("Health Potion"):
            Logger.info("[BATTLE] No Health Potions left!")
            self.txt1 = "No Health Potions left!"
            self.txt2 = ""
            return

        # heal 20 HP
        heal_amount = 20
        self.player_monster['hp'] += heal_amount
        if self.player_monster['hp'] > self.player_monster['max_hp']:
            self.player_monster['hp'] = self.player_monster['max_hp']

        Logger.info(f"[BATTLE] Used Health Potion on {self.player_monster['name']}, healed {heal_amount} HP (current HP: {self.player_monster['hp']})")
        self.txt1 = f"Used Health Potion on {self.player_monster['name']}, healed {heal_amount} HP."
        self.txt2 = ""

    def on_strength_potion(self):
        if self.turn != "item" and self.change_menu_cooldown > 0:
            return  # bukan buka item

        # cek strength potion di bag
        if not self.game_manager.bag.use_item("Strength Potion"):
            Logger.info("[BATTLE] No Strength Potions left!")
            self.txt1 = "No Strength Potions left!"
            self.txt2 = ""
            return

        # naikin level 1
        self.player_damage_boost += 5

        Logger.info(f"[BATTLE] Used Strength Potion on {self.player_monster['name']} (total boost: {self.player_damage_boost})")
        self.txt1 = f"Used Strength Potion on {self.player_monster['name']}, damage increased by total of {self.player_damage_boost}."
        self.txt2 = ""

    def on_defense_potion(self):
        if self.turn != "item" and self.change_menu_cooldown > 0:
            return  # bukan buka item

        # cek defense potion di bag
        if not self.game_manager.bag.use_item("Defense Potion"):
            Logger.info("[BATTLE] No Defense Potions left!")
            self.txt1 = "No Defense Potions left!"
            self.txt2 = ""
            return

        # naikin level 1
        self.player_defense_boost += 5

        Logger.info(f"[BATTLE] Used Defense Potion on {self.player_monster['name']} (total boost: {self.player_defense_boost})")
        self.txt1 = f"Used Defense Potion on {self.player_monster['name']}, defense increased by total of {self.player_defense_boost}."
        self.txt2 = ""

    def enemy_attack_logic(self):
        its_effective = False
        dmg = int(8 * (100 + self.enemy_monster['level']) / 100) # base damage 8, lebih kecil biar gampang menang

        if self.enemy_monster['element'] == "Fire" and self.player_monster['element'] == "Grass":
            self.enemy_damage_boost += 5
            its_effective = True
        elif self.enemy_monster['element'] == "Water" and self.player_monster['element'] == "Fire":
            self.enemy_damage_boost += 5
            its_effective = True
        elif self.enemy_monster['element'] == "Grass" and self.player_monster['element'] == "Water":
            self.enemy_damage_boost += 5
            its_effective = True

        elif self.enemy_monster['element'] == "Grass" and self.player_monster['element'] == "Fire":
            self.player_defense_boost += 5
        elif self.enemy_monster['element'] == "Fire" and self.player_monster['element'] == "Water":
            self.player_defense_boost += 5
        elif self.enemy_monster['element'] == "Water" and self.player_monster['element'] == "Grass":
            self.player_defense_boost += 5
        
        total_dmg = dmg + self.enemy_damage_boost - self.player_defense_boost

        if total_dmg < 0:
            total_dmg = 0

        self.player_monster["hp"] -= total_dmg
        Logger.info(f"[BATTLE] Enemy deals {total_dmg} damage")
        self.txt2 = f"Enemy attacks! Your {self.player_monster['name']} takes {dmg}"

        if self.enemy_damage_boost > 0:
            Logger.info(f"[BATTLE] Enemy's damage boost of {self.enemy_damage_boost} applied.")
            self.txt2 += f" + {self.enemy_damage_boost}"

        if self.player_defense_boost > 0:
            Logger.info(f"[BATTLE] Player's defense boost of {self.player_defense_boost} applied.")
            self.txt2 += f" - {self.player_defense_boost}"

        self.txt2 += f" = {total_dmg} damage."

        if its_effective:
            self.txt2 += " It's super effective!"

        self.player_defense_boost = 0  # reset boost setelah dipake
        self.enemy_damage_boost = 0  # reset boost setelah dipake

        if self.player_monster["hp"] <= 0:
            self.player_monster["hp"] = 0
            self.turn = "lose"
            Logger.info("[BATTLE] Player monster fainted!")
            self.txt2 += f" Your {self.player_monster['name']} fainted! You lose!"
            return

        self.turn = "player"

    def update(self, dt):
        Logger.info(f"cooldown: {self.change_menu_cooldown}")

        # If we just changed menus, wait until the mouse button is released before processing further input.
        # This prevents a single click from activating an overlapping button in the newly opened menu.
        if self.ignore_mouse_until_release:
            if pg.mouse.get_pressed()[0]:  # left mouse still pressed
                return
            else:
                self.ignore_mouse_until_release = False

        # enemy turn logic langsung serang
        if self.turn == "enemy":
            self.enemy_attack_logic()
            return
        
        # cooldown change menu
        self.change_menu_cooldown -= dt
        if self.change_menu_cooldown < 0:
            self.change_menu_cooldown = 0
        else:
            return

        # buttons muncul kalau player turn
        if self.turn == "player" and self.change_menu_cooldown == 0:
            self.btn_run.update(dt)
            self.btn_attack.update(dt)
            self.btn_switch.update(dt)
            self.btn_item.update(dt)

        # checkpoint 3
        if self.turn == "item" and self.change_menu_cooldown == 0:
            self.btn_back.update(dt)
            self.btn_health_potion.update(dt)
            self.btn_strength_potion.update(dt)
            self.btn_defense_potion.update(dt)

        if self.turn in ["win", "lose", "no monsters"]:
            self.btn_run.update(dt)  # pake tombol run buat keluar

        if self.turn == "win" and self.enemy == "wild":
            self.btn_catch.update(dt)

    def draw_hp_bar(self, screen, x, y, w, h, hp, max_hp):
        ratio = max(hp / max_hp, 0)
        pg.draw.rect(screen, (0, 0, 0), (x, y, w, h), 2)
        pg.draw.rect(screen, (255, 0, 0), (x+2, y+2, int((w-4) * ratio), h-4))


    def draw(self, screen):
        # Gambar background
        self.background.draw(screen)

        # Gambar menu
        self.menu_background.image = pg.transform.scale(
            self.menu_background.image,
            (screen.get_width(), 200)
        )
        screen.blit(self.menu_background.image, (0, 500))

        # Gambar monster
        player_sprite = loader.load_img(self.player_monster["sprite_path"])
        enemy_sprite = loader.load_img(self.enemy_monster["sprite_path"])
        player_sprite = pg.transform.scale(player_sprite, (200, 200))
        enemy_sprite = pg.transform.scale(enemy_sprite, (200, 200))
        screen.blit(player_sprite, (300, 250))
        screen.blit(enemy_sprite, (750, 100))

        # nameplate banner
        banner_width = 240
        banner_height = 80
        banner = loader.load_img("UI/raw/UI_Flat_Banner03a.png")
        banner = pg.transform.scale(banner, (banner_width, banner_height))
        screen.blit(banner, (25, 340))
        screen.blit(banner, (975, 140))

        # label monster
        player_text = minecraft_font.render(
            f"{self.player_monster['name']}  HP: {self.player_monster['hp']}",
            True, (0, 0, 0)
        )
        enemy_text = minecraft_font.render(
            f"{self.enemy_monster['name']}  HP: {self.enemy_monster['hp']}",
            True, (0, 0, 0)
        )

        screen.blit(player_text, (50, 350))
        screen.blit(enemy_text, (1000, 150))

        # HP bars
        self.draw_hp_bar(screen, 50, 380, 200, 20,
                         self.player_monster["hp"], self.player_monster["max_hp"])
        self.draw_hp_bar(screen, 1000, 180, 200, 20,
                         self.enemy_monster["hp"], self.enemy_monster["max_hp"])

        # Gambar tombol
        if self.turn == "player":
            self.btn_run.draw(screen)
            run_label = minecraft_font.render("Run", True, (0, 0, 0))
            screen.blit(run_label, run_label.get_rect(center=self.btn_run.hitbox.center))

            self.btn_attack.draw(screen)
            atk_label = minecraft_font.render("Attack", True, (0, 0, 0))
            screen.blit(atk_label, atk_label.get_rect(center=self.btn_attack.hitbox.center))

            self.btn_switch.draw(screen)
            switch_label = minecraft_font.render("Switch", True, (0, 0, 0))
            screen.blit(switch_label, switch_label.get_rect(center=self.btn_switch.hitbox.center))

            self.btn_item.draw(screen)
            item_label = minecraft_font.render("Item", True, (0, 0, 0))
            screen.blit(item_label, item_label.get_rect(center=self.btn_item.hitbox.center))

        if self.turn == "item":
            self.btn_back.draw(screen)
            back_label = minecraft_font.render("Back", True, (0, 0, 0))
            screen.blit(back_label, back_label.get_rect(center=self.btn_back.hitbox.center))

            self.btn_health_potion.draw(screen)
            hp_potion_item_label = minecraft_font.render("Health Potion", True, (0, 0, 0))
            screen.blit(hp_potion_item_label, hp_potion_item_label.get_rect(center=self.btn_health_potion.hitbox.center))

            self.btn_strength_potion.draw(screen)
            str_potion_item_label = minecraft_font.render("Strength Potion", True, (0, 0, 0))
            screen.blit(str_potion_item_label, str_potion_item_label.get_rect(center=self.btn_strength_potion.hitbox.center))

            self.btn_defense_potion.draw(screen)
            def_potion_item_label = minecraft_font.render("Defense Potion", True, (0, 0, 0))
            screen.blit(def_potion_item_label, def_potion_item_label.get_rect(center=self.btn_defense_potion.hitbox.center))

        # print text, termasuk WIN/LOSE screens
        screen.blit(text_font.render(self.txt1, True, (0, 0, 0)), (self.txt1_x, self.txt1_y))
        screen.blit(text_font.render(self.txt2, True, (0, 0, 0)), (self.txt2_x, self.txt2_y))
            
        if self.turn in ["win", "lose", "no monsters"]:
            self.btn_run.draw(screen) # pake tombol run buat keluar
            run_label = minecraft_font.render("Return", True, (0, 0, 0))
            screen.blit(run_label, run_label.get_rect(center=self.btn_run.hitbox.center))

        if self.turn == "win" and self.enemy == "wild" and not self.already_catch:
            self.btn_catch.draw(screen)
            catch_label = minecraft_font.render("Catch", True, (0, 0, 0))
            screen.blit(catch_label, catch_label.get_rect(center=self.btn_catch.hitbox.center))
