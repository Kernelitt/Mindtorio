'''
Frontier: Salvage - Объединённый проект с Mindtorio фреймворком
'''
import pygame, os, sys, time, random
from advanced_framework import *
from definitions import *
from game.world import World
from game.save_manager import SaveManager, SaveSystem
from network.network_manager import GameClient
from ui.renderer import GameRenderer
from ui.building_placer import BuildingPlacer, BuildingPlacerUI
from ui.save_menu import SaveMenu

# Импортируем Steam менеджер
try:
    from steam_manager import SteamLobbyManager, SteamManager
    STEAM_AVAILABLE = True
    print("Steam manager loaded successfully")
except ImportError as e:
    STEAM_AVAILABLE = False
    print(f"Steam manager not available - using local mode only")
    
    # Создаём заглушку
    class SteamLobbyManager:
        def __init__(self):
            self.steam = None
            self.lobby_id = None
            self.is_host = False
            self.members = []
            
        def initialize(self):
            print("[Steam] Эмуляция Steam (заглушка)")
            return True
        
        def create_lobby(self):
            self.lobby_id = f"STEAM_LOBBY_{random.randint(1000, 9999)}_{int(time.time())}"
            self.is_host = True
            print(f"[Steam] Лобби создано (заглушка)! ID: {self.lobby_id}")
            return self.lobby_id
        
        def join_lobby(self, lobby_id):
            self.lobby_id = lobby_id
            self.is_host = False
            print(f"[Steam] Присоединились к лобби (заглушка) {lobby_id}")
            return True
        
        def get_lobby_id(self):
            return self.lobby_id
        
        def get_members(self):
            return [{"id": "STEAM_1", "name": "Host", "is_host": True}]
        
        def update(self):
            pass
        
        def shutdown(self):
            pass

class App:
    def __init__(self):
        pygame.init()
        pygame.mixer.init()
        
        # Фреймворк
        self.framework = AdvancedFW()
        
        # Настройки экрана
        self.screen_resolution = (int(self.framework.get_config("resolution_width",BASE_RESOLUTION[0])),
                                int(self.framework.get_config("resolution_height",BASE_RESOLUTION[1])))
        self.fullscreen = self.framework.get_config("fullscreen") == "True"
        self.screen = pygame.display.set_mode(self.screen_resolution)
        # Создаём окно
        if self.fullscreen: self.toggle_fullscreen(1)
        
        # Основная поверхность для рендеринга
        self.main_surface = pygame.Surface(BASE_RESOLUTION)
        pygame.display.set_caption(GAME_CAPTION_TITLE)
        
        try:
            pygame.display.set_icon(pygame.image.load("data/icon.png"))
        except:
            pass
        
        self.clock = pygame.time.Clock()
        
        # Загрузка ассетов
        self.asset_loader = AssetLoader('data', self.screen)
        while self.asset_loader.load_all() < 1: pass
        
        # Аудио и локализация
        self.audio_manager = AudioManager(self.asset_loader.assets, self.framework.config)
        
        self.loc_mn = LocalizationManager("data/localizations.csv", self.framework.get_config("language") or "en")
        
        # Игровые компоненты
        self.client = None
        self.renderer = None
        self.placer = None
        self.placer_ui = None
        self.game_running = False
        
        # Состояние сцены
        self.player_name = "Игрок"
        self.player_role = "engineer"
        self.server_host = None
        self.port = 7777
        self.host_type = "local"
        self.server_id = None
        self.steam_lobby_manager = None
        self.show_server_id = False
        self.server_id_display = ""
        self.server_id_timer = 0
        self.copy_button_rect = None
        self.use_steam = False
        
        # Создаём UI
        self._create_ui()
        
        # Загрузка сохранений
        self.save_manager = SaveManager()
        
        # Меню сохранения
        self.save_menu = SaveMenu(self.screen, self.save_manager, self.loc_mn)
        self.save_menu.set_world_state_callback(self._get_world_state_for_save)
        
        # Переменная для мира
        self.world = None

    def _create_ui(self):
        font_path = self.asset_loader.assets.get("fonts\\BrianneTod.ttf")
        self.font = font_path if font_path else pygame.font.SysFont("Arial", 24)

        self.main_ui = {
        "main_menu_ui": [
            PygameButton(30, 800, 220, 50, self.loc_mn._g("TID_PLAY"), None, self.font,
                        callback=lambda: self.change_scene('play_menu')),
            PygameButton(30, 860, 220, 50, self.loc_mn._g("TID_SETTINGS"), None, self.font,
                        callback=lambda: self.change_scene('settings_menu')),
            PygameButton(30, 920, 220, 50, self.loc_mn._g("TID_CREDITS"), None, self.font,
                        callback=lambda: self.change_scene('credits_menu')),
            PygameButton(30, 980, 220, 50, self.loc_mn._g("TID_QUIT"), None, self.font,
                        callback=lambda: self.Quit())
        ],
        "play_menu_ui":[
            PygameButton(30, 750, 220, 50, self.loc_mn._g("TID_HOST"), None, self.font,
                        callback=lambda: self.change_scene("host_type_menu")),
            PygameButton(260, 750, 220, 50, self.loc_mn._g("TID_CONNECT"), None, self.font,
                        callback=lambda: self.change_scene("connect_menu")),
            PygameButton(30, 1000, 130, 50, self.loc_mn._g("TID_BACK"), None, self.font,
                        callback=lambda: self.change_scene('main_menu')),
        ],
        
        # Меню выбора типа хоста
        "host_type_menu_ui":[
            PygameButton(30, 750, 300, 50, self.loc_mn._g("TID_HOST_LOCAL"), None, self.font,
                        callback=lambda: self._start_host("local")),
            PygameButton(340, 750, 300, 50, self.loc_mn._g("TID_HOST_STEAM"), None, self.font,
                        callback=lambda: self._start_host("steam")),
            PygameButton(30, 1000, 130, 50, self.loc_mn._g("TID_BACK"), None, self.font,
                        callback=lambda: self.change_scene("play_menu")),
        ],
        
        # Меню подключения
        "connect_menu_ui":[
            PygameLabel(400, 450, self.loc_mn._g("TID_CONNECT_BY_ID"), self.font, color=(200, 200, 200)),
            PygameInputField(400, 500, 500, 50, self.loc_mn._g("TID_ENTER_SERVER_ID"), self.font,
                            callback=lambda x: setattr(self, 'server_id', x)),
            PygameButton(400, 600, 200, 50, self.loc_mn._g("TID_CONNECT"), None, self.font,
                        callback=lambda: self._connect_by_id()),
            PygameButton(30, 1000, 130, 50, self.loc_mn._g("TID_BACK"), None, self.font,
                        callback=lambda: self.change_scene('play_menu')),
        ],
        
        # Меню настроек
        "settings_menu_ui":[
            PygameLabel(160, 200, self.loc_mn._g("TID_MUSIC_VOLUME"), self.font, center=True),
            PygameSlider(100, 240, 500, 30, 0, 100, int(self.audio_manager.music_volume * 100), 
                        callback=lambda x: self.audio_manager.set_music_volume(x/100)),
            PygameLabel(160, 320, self.loc_mn._g("TID_SFX_VOLUME"), self.font, center=True),
            PygameSlider(100, 360, 500, 30, 0, 100, int(self.audio_manager.sfx_volume * 100),
                        callback=lambda x: self.audio_manager.set_sfx_volume(x/100)),
            PygameLabel(180, 440, self.loc_mn._g("TID_LANGUAGE"), self.font, center=True),
            PygameButton(300, 440, 80, 40, "EN", None, self.font,
                        callback=lambda: self._set_language("en")),
            PygameButton(400, 440, 80, 40, "RU", None, self.font,
                        callback=lambda: self._set_language("ru")),
            PygameCheckbox(30, 550, 30, self.loc_mn._g("TID_FULLSCREEN"), 
                          self.fullscreen, callback=lambda x: self.toggle_fullscreen(x)),
            PygameButton(30, 1000, 130, 50, self.loc_mn._g("TID_BACK"), None, self.font,
                        callback=lambda: self.change_scene('main_menu')),
            PygameLabel(120, 630, self.loc_mn._g("TID_RESOLUTION"), self.font, center=True),
            PygameButton(30, 700, 130, 50, "1280x720", None, self.font,
                        callback=lambda: self.change_resolution(720)),
            PygameButton(170, 700, 130, 50, "1366x768", None, self.font,
                        callback=lambda: self.change_resolution(768)),
            PygameButton(310, 700, 130, 50, "1600x900", None, self.font,
                        callback=lambda: self.change_resolution(900)),
            PygameButton(450, 700, 130, 50, "1920x1080", None, self.font,
                        callback=lambda: self.change_resolution(1080)),
            PygameButton(590, 700, 130, 50, "2560x1440", None, self.font,
                        callback=lambda: self.change_resolution(1440)),
            PygameButton(730, 700, 130, 50, "3840x2160", None, self.font,
                        callback=lambda: self.change_resolution(2160)),
        ],
        }

        self.change_scene("main_menu")
        
    def _set_language(self, lang):
        self.loc_mn.set_language(lang)
        self.framework.set_config('language', lang)
        self._create_ui()

    def _connect_by_id(self):
        if not self.server_id or len(self.server_id.strip()) < 3:
            self._show_error_message("Введите корректный ID сервера!")
            return
        
        server_id = self.server_id.strip()
        
        if server_id.startswith("STEAM_LOBBY") or server_id.startswith("STEAM_"):
            self.use_steam = True
            self._connect_steam_by_id(server_id)
        else:
            self.use_steam = False
            self.start_game(connect=True, server_id=server_id)

    def _connect_steam_by_id(self, steam_id):
        try:
            print(f"Подключение к Steam лобби: {steam_id}")
            
            self.steam_lobby_manager = SteamLobbyManager()
            if not self.steam_lobby_manager.initialize():
                self._show_error_message("Не удалось инициализировать Steam!")
                return
            
            if self.steam_lobby_manager.join_lobby(steam_id):
                print(f"Успешно подключены к Steam лобби: {steam_id}")
                self.start_game(connect=True, server_id=steam_id, use_steam=True)
            else:
                self._show_error_message("Не удалось присоединиться к лобби!")
                
        except Exception as e:
            print(f"Ошибка подключения к Steam: {e}")
            self._show_error_message(f"Ошибка: {str(e)[:50]}")

    def _start_host(self, host_type):
        self.host_type = host_type
        self.use_steam = (host_type == "steam")
        
        if host_type == "steam":
            try:
                print("Создание Steam лобби...")
                
                self.steam_lobby_manager = SteamLobbyManager()
                if not self.steam_lobby_manager.initialize():
                    self._show_error_message("Не удалось инициализировать Steam!")
                    print("Переключение на локальный хост...")
                    self._start_host("local")
                    return
                
                lobby_id = self.steam_lobby_manager.create_lobby()
                if lobby_id:
                    self.server_id = lobby_id
                    self.show_server_id = True
                    self.server_id_display = f"Steam Lobby ID: {lobby_id}"
                    self.server_id_timer = pygame.time.get_ticks() + 20000
                    print(f"Steam лобби создано! ID: {lobby_id}")
                    
                    self.start_game(connect=False, server_id=lobby_id, use_steam=True)
                    return
                else:
                    self._show_error_message("Не удалось создать Steam лобби!")
                    print("Переключение на локальный хост...")
                    self._start_host("local")
                    return
                    
            except Exception as e:
                print(f"Ошибка создания Steam лобби: {e}")
                self._show_error_message(f"Ошибка: {str(e)[:50]}")
                print("Переключение на локальный хост...")
                self._start_host("local")
                return
        
        # Локальный хост
        self.server_id = f"LOCAL_{random.randint(1000, 9999)}_{int(time.time())}"
        self.show_server_id = True
        self.server_id_display = f"Local Server ID: {self.server_id}"
        self.server_id_timer = pygame.time.get_ticks() + 15000
        print(f"Локальный сервер создан! ID: {self.server_id}")
        
        self.start_game(connect=False, server_id=self.server_id, use_steam=False)

    def _show_error_message(self, message):
        self.error_message = message
        self.audio_manager.play_sfx("sfx\\error.ogg")
        self.error_timer = pygame.time.get_ticks() + 3000

    def toggle_fullscreen(self, checked):
        self.fullscreen = checked
        self.framework.set_config('fullscreen', str(checked))
        if self.fullscreen:
            self.screen_resolution = pygame.display.get_desktop_sizes()[0]
        else:
            self.screen_resolution = (int(self.framework.get_config("resolution_width",BASE_RESOLUTION[1])),
                        int(self.framework.get_config("resolution_height",BASE_RESOLUTION[1])))
            
        pygame.display.set_mode(self.screen_resolution)
        if self.fullscreen: pygame.display.toggle_fullscreen()

    def start_game(self, connect=True, server_id=None, use_steam=False):
        if connect:
            if not self.server_host:
                self.server_host = "127.0.0.1"
            self.client = GameClient(server_host=self.server_host, server_port=self.port)
            self.client.load_save = None
            self.client.server_id = server_id
            self.client.connect(self.player_name, self.player_role)
        else:
            self.client = GameClient()
            self.client.load_save = None
            self.client.server_id = server_id or f"local_{int(pygame.time.get_ticks())}"
            self.client.connect(self.player_name, self.player_role)
        
        wait_start = pygame.time.get_ticks()
        while not self.client.player_id:
            pygame.time.wait(50)
            if pygame.time.get_ticks() - wait_start > 5000:
                print(self.loc_mn._g("TID_CONNECTION_ERROR"))
                return
        
        self.renderer = GameRenderer(self.main_surface, self.client)
        self.placer = BuildingPlacer()
        self.placer_ui = BuildingPlacerUI(self.placer)
        self.game_running = True
        self.current_scene = "game"
        
        print(self.loc_mn._g("TID_CONNECTED"))
        print(f"Server ID: {self.client.server_id}")
        if use_steam:
            print("Режим: Steam Multiplayer")
        print(self.loc_mn._g("TID_MOVE"))
        print(self.loc_mn._g("TID_MINE"))
        print(self.loc_mn._g("TID_BUILD"))
        print(self.loc_mn._g("TID_SAVE_MENU"))
        print(self.loc_mn._g("TID_LOAD_MENU"))
        print(self.loc_mn._g("TID_QUIT_GAME"))

    def _get_world_state_for_save(self):
        if self.client and self.client.local_server and self.client.local_server.world:
            return self.client.local_server.world.to_dict()
        return {}

    def run(self):
        running = True
        while running:
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    running = False
            
            if self.steam_lobby_manager and self.use_steam:
                try:
                    self.steam_lobby_manager.update()
                except:
                    pass
            
            if self.current_scene == "game" and self.game_running:                    
                self._update_game(events)
                self._draw_game()
                if self.save_menu.active:
                    self.save_menu.update(events)
                    self.save_menu.draw(self.screen)
            else:
                self._update_menu(events)
                self._draw_menu()
            
            self.clock.tick(int(self.framework.get_config("fps", 60)))
        
        self.Quit()

    def _update_game(self, events):
        if not self.client or not self.client.world_state:
            return
        
        dt = 1 / max(1, self.clock.get_fps())
        
        keys = pygame.key.get_pressed()
        dx = dy = 0
        if keys[pygame.K_w] or keys[pygame.K_UP]: dy = -1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]: dy = 1
        if keys[pygame.K_a] or keys[pygame.K_LEFT]: dx = -1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]: dx = 1
        
        if dx != 0 or dy != 0:
            self.client.send_move(dx, dy)
        
        for event in events:
            if event.type == pygame.KEYDOWN:
                match event.key:
                    case pygame.K_ESCAPE:
                        if self.client.local_server and self.client.local_server.world:
                            self.client.local_server.world.quick_save()
                        self.game_running = False
                        self.change_scene("main_menu")
                        self.client.disconnect()
                    
                    case pygame.K_F5:
                        self.save_menu.open("save")
                    
                    case pygame.K_F9:
                        self.save_menu.open("load")
                    
                    case pygame.K_SPACE:
                        self.client.send_mine()
                    
                    case pygame.K_TAB:
                        if self.client.can_switch_roles:
                            roles = ["engineer", "mechanic", "defender"]
                            if self.client.world_state:
                                player_data = self.client.world_state["entities"].get(self.client.player_id)
                                if player_data:
                                    current_role = player_data.get("role", "engineer")
                                    next_idx = (roles.index(current_role) + 1) % len(roles)
                                    self.client.send_switch_role(roles[next_idx])
                    
                    case pygame.K_b:
                        if self.client.world_state:
                            player_data = self.client.world_state["entities"].get(self.client.player_id)
                            if player_data:
                                self.client.send_build(
                                    "turret_mg",
                                    player_data["x"] + 50,
                                    player_data["y"],
                                    "machinegun_turret"
                                )

    def _draw_game(self):
        if not self.client:
            return
        
        self.renderer.render(1/60)
        self._scale_and_display()

    def _scale_and_display(self):
        screen_w, screen_h = self.screen.get_size()
        surf_w, surf_h = self.main_surface.get_size()
        
        scale_w = screen_w / surf_w
        scale_h = screen_h / surf_h
        scale = min(scale_w, scale_h)
        
        new_w = int(surf_w * scale)
        new_h = int(surf_h * scale)
        
        scaled = pygame.transform.smoothscale(self.main_surface, (new_w, new_h))
        
        x = (screen_w - new_w) // 2
        y = (screen_h - new_h) // 2
        
        self.screen.fill((0, 0, 0))
        self.screen.blit(scaled, (x, y))
        pygame.display.flip()

    def _update_menu(self, events):
        scale_x = BASE_RESOLUTION[0] / self.screen_resolution[0]
        scale_y = BASE_RESOLUTION[1] / self.screen_resolution[1]
        mouse_x, mouse_y = pygame.mouse.get_pos()
        virtual_mouse_pos = (mouse_x * scale_x, mouse_y * scale_y)
        
        for btn in self.current_menu_ui:
            if hasattr(btn, 'update'):
                btn.update(events, virtual_mouse_pos)

    def _draw_menu(self):
        self.main_surface.fill("#1a1a2e")

        if self.current_scene == "main_menu": 
            self.main_surface.blit(self.asset_loader.assets.get("textures\\logo.png"),(10,600))
        
        if self.show_server_id and self.server_id_display:
            server_font = pygame.font.Font(None, 28)
            server_text = server_font.render(self.server_id_display, True, (100, 255, 100))
            server_rect = server_text.get_rect(center=(BASE_RESOLUTION[0]//2, 320))
            self.main_surface.blit(server_text, server_rect)
            
            copy_btn = PygameButton(
                BASE_RESOLUTION[0]//2 + 250, 305, 80, 30,
                "COPY", None, self.font,
                bg_color=(60, 60, 80), hover_bg_color=(100, 100, 140),
                callback=self._copy_server_id
            )
            copy_btn.draw(self.main_surface)
            self.copy_button_rect = copy_btn.rect
            
            if self.server_id_timer and pygame.time.get_ticks() > self.server_id_timer:
                self.show_server_id = False
        
        for btn in self.current_menu_ui:
            if hasattr(btn, 'draw'):
                btn.draw(self.main_surface)
        
        if hasattr(self, 'error_message') and self.error_message:
            error_font = pygame.font.Font(None, 30)
            error_text = error_font.render(self.error_message, True, (255, 100, 100))
            error_rect = error_text.get_rect(center=(BASE_RESOLUTION[0]//2, 600))
            self.main_surface.blit(error_text, error_rect)
            if hasattr(self, 'error_timer') and pygame.time.get_ticks() > self.error_timer:
                self.error_message = ""
        
        self._scale_and_display()

    def _copy_server_id(self):
        if self.server_id:
            try:
                import pyperclip
                pyperclip.copy(self.server_id)
                print(f"Server ID скопирован: {self.server_id}")
                self._show_error_message("ID скопирован в буфер обмена!")
            except ImportError:
                print(f"Server ID: {self.server_id}")
                self._show_error_message(f"ID: {self.server_id}")

    def change_scene(self, new_scene: str):
        self.current_scene = new_scene
        self.current_menu_ui = self.main_ui.get(new_scene+"_ui")

    def change_resolution(self,height):
        width = round(height / 9 * 16)
        self.framework.set_config('resolution_width', str(width))
        self.framework.set_config('resolution_height', str(height))
        self.screen_resolution = (width,height)
        pygame.display.set_mode(self.screen_resolution)
        if self.fullscreen: self.toggle_fullscreen(self.fullscreen)

    def Quit(self):
        if self.client:
            self.client.disconnect()
        if self.steam_lobby_manager:
            try:
                self.steam_lobby_manager.shutdown()
            except:
                pass
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    app = App()
    app.run()