import pygame as pg
from src.utils import load_sound, GameSettings, Logger

class SoundManager:
    def __init__(self):
        pg.mixer.init()
        pg.mixer.set_num_channels(GameSettings.MAX_CHANNELS)
        self.current_bgm = None
        
    def play_bgm(self, filepath: str):
        if self.current_bgm:
            self.current_bgm.stop()
        audio = load_sound(filepath)
        audio.set_volume(GameSettings.AUDIO_VOLUME)
        audio.play(-1)
        self.current_bgm = audio
        
        # langsung apply global settings
        self.apply_settings()
        
    def pause_all(self):
        pg.mixer.pause()

    def resume_all(self):
        pg.mixer.unpause()
        
    def play_sound(self, filepath, volume=0.7):
        sound = load_sound(filepath)
        sound.set_volume(volume)
        sound.play()

    def stop_all_sounds(self):
        pg.mixer.stop()
        self.current_bgm = None

    def apply_settings(self):
        #Logger.info(f"apply_settings: volume={GameSettings.AUDIO_VOLUME}, mute={GameSettings.MUTE}")
        
        # Apply volume
        if self.current_bgm:
            self.current_bgm.set_volume(GameSettings.AUDIO_VOLUME)

        # Apply mute state
        if GameSettings.MUTE:
            pg.mixer.pause()
        else:
            pg.mixer.unpause()
