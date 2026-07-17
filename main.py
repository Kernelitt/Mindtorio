'''
Mindtorio Prototype
Authors: Kernelit & Cocos72010
'''
import pygame,os,sys
from advanced_framework import *
from definitions import *

class App():
    def __init__(self):
        pygame.init()
        pygame.mixer.init()
        self.framework = AdvancedFW()
        self.screen = pygame.display.set_mode((int(self.framework.get_config("resolution_width")),int(self.framework.get_config("resolution_height"))))

        self.main_surface = pygame.Surface(DRAWING_RESOLUTION)
        pygame.display.set_caption(GAME_CAPTION_TITLE)
        pygame.display.set_icon(pygame.image.load("data\\icon.png"))
        self.clock = pygame.time.Clock()

        self.asset_loader = AssetLoader('data', self.screen)
        while self.asset_loader.load_all() < 1: pass

        self.audio_manager = AudioManager(self.asset_loader.assets,self.framework.config)
        self.loc_mn = LocalizationManager("data\\localizations.csv",self.framework.get_config("language"))

        self.current_scene = "main_menu"
        self.main_menu_ui = [
            PygameButton(30,800,180,50,self.loc_mn._g("TID_PLAY"),None,self.asset_loader.assets.get("fonts\\BrianneTod.ttf"),callback=lambda:self.change_scene('play_menu')),
            PygameButton(30,860,180,50,self.loc_mn._g("TID_SETTINGS"),None,self.asset_loader.assets.get("fonts\\BrianneTod.ttf"),callback=lambda:self.change_scene('settings_menu')),
            PygameButton(30,920,180,50,self.loc_mn._g("TID_CREDITS"),None,self.asset_loader.assets.get("fonts\\BrianneTod.ttf"),callback=lambda:self.change_scene('credits_menu')),
            PygameButton(30,980,180,50,self.loc_mn._g("TID_QUIT"),None,self.asset_loader.assets.get("fonts\\BrianneTod.ttf"),callback=lambda:self.Quit())
        ]

        self.play_menu_ui = [
            PygameButton(30,1000,130,50,self.loc_mn._g("TID_BACK"),None,self.asset_loader.assets.get("fonts\\BrianneTod.ttf"),callback=lambda:self.change_scene('main_menu')),
            PygameButton( 30,800,180,70,self.loc_mn._g("TID_CONNECT"),None,self.asset_loader.assets.get("fonts\\BrianneTod.ttf")),
            PygameButton(230,800,180,70,self.loc_mn._g("TID_HOST"),None,self.asset_loader.assets.get("fonts\\BrianneTod.ttf")),
            PygameInputField(30,600,300,60,""),
            PygameInputField(30,700,300,60,"5555")
        ]

    def run(self):
        running = True
        while running:

            self.Update()
            self.Draw()

    def change_scene(self, new_scene: str):
        self.current_scene = new_scene
    
    def Update(self):
        if self.clock.get_fps() > 0:
            deltaTime = 1 / self.clock.get_fps()
        virtual_mouse_pos = (DRAWING_RESOLUTION[0] / self.screen.width * pygame.mouse.get_pos()[0],
                             DRAWING_RESOLUTION[1] / self.screen.height* pygame.mouse.get_pos()[1])
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                self.Quit()

        if self.current_scene == "main_menu":
            for btn in self.main_menu_ui:
                btn.update(events,virtual_mouse_pos)
        elif self.current_scene == "play_menu":
            for btn in self.play_menu_ui:
                btn.update(events,virtual_mouse_pos)
        self.clock.tick(int(self.framework.get_config("fps")))

    def Draw(self):     
        if self.current_scene == "main_menu":
            self.main_surface.fill("#770F0F")
            for btn in self.main_menu_ui:
                btn.draw(self.main_surface)
        elif self.current_scene == "play_menu":
            self.main_surface.fill("#770F0F")
            for btn in self.play_menu_ui:
                btn.draw(self.main_surface)
        scaled = pygame.transform.smoothscale(self.main_surface, self.screen.get_size())
        self.screen.blit(scaled, (0, 0))
        pygame.display.flip()

    def Quit(self):
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    app = App()
    app.run()