import random,os,json,pygame,csv,configparser
import tkinter as tk
from pathlib import Path
from typing import Dict, Any
from definitions import BASIC_CONFIG

class AssetLoader:
    def __init__(self, data_dir: str, screen: pygame.Surface):
        self.data_dir = Path(data_dir)
        self.assets: Dict[str, Any] = {}
        self.screen = screen
        self.bar_rect = pygame.Rect((0,self.screen.size[1] - 60,self.screen.size[0],60))
        self.bar_color = (100, 200, 100)
        self.bg_color = (50, 50, 50)
        self._asset_types = {
            'textures': (lambda p: pygame.image.load(p).convert_alpha(), ['.png', '.jpg', '.gif']),
            'sfx': (lambda p: pygame.mixer.Sound(p), ['.wav', '.ogg', '.mp3']),
            'music': (lambda p: pygame.mixer.Sound(p), ['.wav', '.ogg', '.mp3']),
            'fonts': (lambda p: pygame.font.Font(str(p), 32), ['.ttf', '.otf'])
        }

    def load_all(self) -> float:
        """Загружает все ассеты, возвращает прогресс (0-1). Вызывай в цикле пока <1."""
        files = []
        for subdir, (loader, exts) in self._asset_types.items():
            dir_path = self.data_dir / subdir
            if dir_path.exists():
                for ext in exts:
                    files.extend(dir_path.glob(f'*{ext}'))

        total = len(files)
        if total == 0:
            return 1.0

        loaded = 0
        for file_path in files:
            key = str(file_path.relative_to(self.data_dir))
            try:
                loader = next((l for s, (l, e) in self._asset_types.items() if file_path.suffix.lower() in e))
                self.assets[key] = loader(file_path)
            except Exception:
                pass  # Пропуск ошибок
            loaded += 1
            progress = loaded / total
            self._draw_progress(progress)
            pygame.display.flip()
            pygame.time.wait(4)  # Не нагружать CPU

        return 1.0  #web:16][web:19]

    def _draw_progress(self, progress: float):
        """Рисует прогрессбар."""
        if self.screen:
            self.screen.fill("#000000")
            pygame.draw.rect(self.screen, self.bg_color, self.bar_rect)
            fill_width = int(self.bar_rect.w * progress)
            pygame.draw.rect(self.screen, self.bar_color, (self.bar_rect.x, self.bar_rect.y, fill_width, self.bar_rect.h))
            # Текст прогресса
            font = pygame.font.Font(None, 36)
            text = font.render(f'Loading... {int(progress*100)}%', True, (255,255,255))
            self.screen.blit(text, (self.bar_rect.x, self.bar_rect.y - 40))

    def get(self, key: str, default=None):
        """Получает ассет по ключу (относительный путь)."""
        return self.assets.get(key, default)
    
class AudioManager:
    def __init__(self, assets, config):
        self.assets = assets
        self.config = config
        self.music_volume = float(self.config.get('GAME', 'volume_music', fallback='0.8'))
        self.sfx_volume = float(self.config.get('GAME', 'volume_sfx', fallback='0.8'))
        pygame.mixer.music.set_volume(self.music_volume)

    def play_music(self, key: str, loops=-1):
        """Play background music by key."""
        if key in self.assets:
            pygame.mixer.music.load(self.assets[key])
            pygame.mixer.music.play(loops)

    def stop_music(self):
        """Stop background music."""
        pygame.mixer.music.stop()

    def play_sfx(self, key: str):
        """Play sound effect by key."""
        if key in self.assets:
            sound = self.assets[key]
            sound.set_volume(self.sfx_volume)
            sound.play()

    def set_music_volume(self, volume: float):
        """Set music volume (0.0 to 1.0)."""
        self.music_volume = volume
        pygame.mixer.music.set_volume(volume)

    def set_sfx_volume(self, volume: float):
        """Set SFX volume (0.0 to 1.0)."""
        self.sfx_volume = volume

    def update_config(self, config):
        """Update volumes from config."""
        self.music_volume = float(config.get('GAME', 'volume_music', fallback='0.8'))
        self.sfx_volume = float(config.get('GAME', 'volume_sfx', fallback='0.8'))
        pygame.mixer.music.set_volume(self.music_volume)

class AdvancedFW:
    def __init__(self,key=b'aVV1rKC-_l1OxB2ym3AwR-FsHDW79OJnPr-Ppcr9W9w=',save_base=dict()):
        try:
            from cryptography.fernet import Fernet
            self.key = key  # Замените на ваш сгенерированный ключ
            self.cipher = Fernet(self.key)          
            self.save_base = dict(save_base)
            self.config_path = Path("config.ini")
            self.config = configparser.ConfigParser()
            self._load_config()
        except Exception as e:
            print("error SimpleFW __init__() --",e)

    def generate_name(self,lenght):
        letters = "ABCDEFGHJKLMNOPQRSTUVWXYZ"
        ret_str = str("")
        for i in range(lenght):
            ret_str += str(random.choice(letters))
        return f"{ret_str}-{random.randint(1000, 9999)}"
    
    def random_color(self):
        return (random.randint(0,255),random.randint(0,255),random.randint(0,255))
    
    def screen_dif(self,width1,height1,width2,height2):
        return [round((width1 / width2),1),round((height1 / height2),1)]    

    def load_data(self):
        try:
            if os.path.exists("save_data.data"):
                with open("save_data.data", 'rb') as f:
                    encrypted_data = f.read()
                    decrypted_data = self.cipher.decrypt(encrypted_data)
                    return json.loads(decrypted_data)
            else:  
                return self.save_base
        except Exception as e:
            print("error SimpleFW load_data() --",e)

    def save_data(self, data):
        try:
            existing_data = self.load_data()

            for key, value in data.items():
                if isinstance(value, dict):
                    existing_data[key] = existing_data.get(key, {})
                    existing_data[key].update(value)
                else:
                    existing_data[key] = value
            json_data = json.dumps(existing_data).encode()
            encrypted_data = self.cipher.encrypt(json_data)
            with open("save_data.data", 'wb') as f:
                f.write(encrypted_data)
        except Exception as e:
            print("error SimpleFW save_data() -",e)

    def _load_config(self):
        """Загружает config.ini, создает дефолтный если нет."""
        if self.config_path.exists():
            self.config.read(self.config_path)
        else:
            # Дефолтные настройки для игры
            self.config['Settings'] = BASIC_CONFIG
            self._save_config()

    def _save_config(self):
        """Сохраняет config.ini."""
        with open(self.config_path, 'w') as f:
            self.config.write(f)

    def get_config(self, key, fallback=None):
        """Получает значение из config"""
        return self.config.get('Settings', key, fallback=fallback)

class LocalizationManager():
    def __init__(self, csv_path: str, default_language: str = "en", fallback_language: str = "en"):
        self.csv_path = Path(csv_path)
        self.default_language = default_language
        self.fallback_language = fallback_language
        self.language = default_language
        self._data = {}
        self._languages = set()
        self._load()

    def _load(self):
        with self.csv_path.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            if not reader.fieldnames:
                raise ValueError("CSV file has no headers")

            if "key" not in reader.fieldnames:
                raise ValueError("CSV must contain 'key' column")

            self._languages = set(reader.fieldnames) - {"key"}

            for row in reader:
                key = row["key"]
                if not key:
                    continue

                self._data[key] = {
                    lang: (row.get(lang) or "").strip()
                    for lang in self._languages
                }

    def set_language(self, language: str):
        if language not in self._languages:
            raise ValueError(f"Unknown language: {language}")
        self.language = language

    def _g(self, key: str) -> str:
        # 1) текущий язык
        value = self._data.get(key, {}).get(self.language, "")
        if value:
            return value

        # 2) fallback язык
        value = self._data.get(key, {}).get(self.fallback_language, "")
        if value:
            return value

        # 3) если перевода нет — вернуть сам ключ
        return key
    
class PygameButton:
    def __init__(
        self,
        x,
        y,
        width,
        height,
        text="",
        texture=None,
        font=None,
        text_color=(255, 255, 255),
        hover_text_color=None,
        bg_color=(70, 70, 70),
        hover_bg_color=(100, 100, 100),
        border_radius=0,
        callback=None
    ):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.texture = texture
        self.font = font or pygame.font.SysFont("Arial", 24)
        self.text_color = text_color
        self.hover_text_color = hover_text_color or text_color
        self.bg_color = bg_color
        self.hover_bg_color = hover_bg_color
        self.border_radius = border_radius
        self.callback = callback

        self.hovered = False
        self.clicked = False
        self.enabled = True

    def update(self, events, virtual_mouse_pos):
        self.hovered = self.rect.collidepoint(virtual_mouse_pos)


        for event in events:
            if self.hovered:
                if event.type == pygame.MOUSEBUTTONUP and self.clicked:
                    if self.callback:
                        self.callback()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self.clicked = True 
            else: 
                self.clicked = False

    def draw(self, screen):
        if self.texture:
            texture = pygame.transform.scale(self.texture, self.rect.size)
            screen.blit(texture, self.rect.topleft)
        else:
            color = self.hover_bg_color if self.hovered else self.bg_color
            pygame.draw.rect(
                screen,
                color,
                self.rect,
                border_radius=self.border_radius
            )

        if self.text:
            color = self.hover_text_color if self.hovered else self.text_color
            text_surf = self.font.render(self.text, True, color)
            text_rect = text_surf.get_rect(center=self.rect.center)
            screen.blit(text_surf, text_rect)

class PygameInputField:
    def __init__(
        self,
        x,
        y,
        width,
        height,
        text="",
        font=None,
        text_color=(255, 255, 255),
        active_color=(120, 120, 120),
        inactive_color=(70, 70, 70),
        border_radius=0,
        max_length=None,
        callback=None
    ):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = font or pygame.font.SysFont("Arial", 24)
        self.text_color = text_color
        self.active_color = active_color
        self.inactive_color = inactive_color
        self.border_radius = border_radius
        self.max_length = max_length
        self.callback = callback

        self.active = False
        self.color = self.inactive_color
        self.text_surf = self.font.render(self.text, True, self.text_color)

    def update(self, events, virtual_mouse_pos):
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self.active = self.rect.collidepoint(virtual_mouse_pos)

            if event.type == pygame.KEYDOWN and self.active:
                if event.key == pygame.K_BACKSPACE:
                    self.text = self.text[:-1]
                elif event.key == pygame.K_RETURN:
                    if self.callback:
                        self.callback(self.text)
                else:
                    if self.max_length is None or len(self.text) < self.max_length:
                        self.text += event.unicode

        self.color = self.active_color if self.active else self.inactive_color
        self.text_surf = self.font.render(self.text, True, self.text_color)

    def draw(self, screen):
        pygame.draw.rect(
            screen,
            self.color,
            self.rect,
            border_radius=self.border_radius
        )

        text_y = self.rect.y + (self.rect.height - self.text_surf.get_height()) // 2
        screen.blit(self.text_surf, (self.rect.x + 8, text_y))

class PygameSlider:
    def __init__(
        self,
        x,
        y,
        width,
        height=20,
        min_value=0,
        max_value=100,
        value=50,
        track_color=(90, 90, 90),
        fill_color=(120, 180, 255),
        knob_color=(240, 240, 240),
        border_color=None,
        callback=None,
        show_value=True,
        font=None
    ):
        self.rect = pygame.Rect(x, y, width, height)
        self.min_value = min_value
        self.max_value = max_value
        self.value = max(min_value, min(max_value, value))

        self.track_color = track_color
        self.fill_color = fill_color
        self.knob_color = knob_color
        self.border_color = border_color
        self.callback = callback
        self.show_value = show_value
        self.font = font or pygame.font.SysFont("Arial", 20)

        self.dragging = False
        self.hovered = False

        self.knob_radius = max(8, height // 2 + 4)
        self._update_knob_pos()

    def _clamp_value(self, v):
        return max(self.min_value, min(self.max_value, v))

    def _value_from_mouse(self, mouse_x):
        rel = (mouse_x - self.rect.x) / self.rect.width
        rel = max(0.0, min(1.0, rel))
        return self.min_value + rel * (self.max_value - self.min_value)

    def _update_knob_pos(self):
        if self.max_value == self.min_value:
            self.knob_x = self.rect.x
        else:
            t = (self.value - self.min_value) / (self.max_value - self.min_value)
            self.knob_x = self.rect.x + int(t * self.rect.width)

        self.knob_y = self.rect.centery

    def set_value(self, value):
        new_value = self._clamp_value(value)
        changed = new_value != self.value
        self.value = new_value
        self._update_knob_pos()
        if changed and self.callback:
            self.callback(self.value)

    def update(self, events, virtual_mouse_pos=None):
        if virtual_mouse_pos is None:
            virtual_mouse_pos = pygame.mouse.get_pos()

        self.hovered = self.rect.collidepoint(virtual_mouse_pos)

        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.rect.collidepoint(event.pos):
                    self.dragging = True
                    self.set_value(self._value_from_mouse(event.pos[0]))

            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                self.dragging = False

            elif event.type == pygame.MOUSEMOTION and self.dragging:
                self.set_value(self._value_from_mouse(event.pos[0]))

    def draw(self, screen):
        track_y = self.rect.centery - self.rect.height // 4
        track_h = self.rect.height // 2
        track_rect = pygame.Rect(self.rect.x, track_y, self.rect.width, track_h)

        pygame.draw.rect(screen, self.track_color, track_rect, border_radius=track_h // 2)

        fill_width = 0
        if self.max_value != self.min_value:
            fill_width = int(
                (self.value - self.min_value) / (self.max_value - self.min_value) * self.rect.width
            )

        fill_rect = pygame.Rect(self.rect.x, track_y, fill_width, track_h)
        pygame.draw.rect(screen, self.fill_color, fill_rect, border_radius=track_h // 2)

        knob_pos = (self.knob_x, self.knob_y)
        pygame.draw.circle(screen, self.knob_color, knob_pos, self.knob_radius)

        if self.border_color is not None:
            pygame.draw.rect(screen, self.border_color, self.rect, 2, border_radius=track_h // 2)

        if self.show_value:
            value_text = self.font.render(str(int(self.value)), True, (255, 255, 255))
            screen.blit(value_text, (self.rect.right + 10, self.rect.centery - value_text.get_height() // 2))

class PygameCheckbox:
    def __init__(
        self,
        x,
        y,
        size=24,
        text="",
        checked=False,
        font=None,
        text_color=(255, 255, 255),
        box_color=(70, 70, 70),
        box_hover_color=(90, 90, 90),
        check_color=(255, 255, 255),
        border_color=(200, 200, 200),
        border_width=2,
        callback=None,
        text_offset=10
    ):
        self.box_rect = pygame.Rect(x, y, size, size)
        self.text = text
        self.checked = checked
        self.font = font or pygame.font.SysFont("Arial", 24)

        self.text_color = text_color
        self.box_color = box_color
        self.box_hover_color = box_hover_color
        self.check_color = check_color
        self.border_color = border_color
        self.border_width = border_width
        self.callback = callback
        self.text_offset = text_offset

        self.hovered = False

    def toggle(self):
        self.checked = not self.checked
        if self.callback:
            self.callback(self.checked)

    def update(self, events, virtual_mouse_pos=None):
        if virtual_mouse_pos is None:
            virtual_mouse_pos = pygame.mouse.get_pos()

        self.hovered = self.box_rect.collidepoint(virtual_mouse_pos)

        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.box_rect.collidepoint(event.pos):
                    self.toggle()

    def draw(self, screen):
        box_fill = self.box_hover_color if self.hovered else self.box_color

        pygame.draw.rect(screen, box_fill, self.box_rect)
        pygame.draw.rect(screen, self.border_color, self.box_rect, self.border_width)

        if self.checked:
            padding = self.box_rect.width // 4
            inner_rect = self.box_rect.inflate(-padding * 2, -padding * 2)
            pygame.draw.rect(screen, self.check_color, inner_rect)

        if self.text:
            text_surf = self.font.render(self.text, True, self.text_color)
            text_y = self.box_rect.centery - text_surf.get_height() // 2
            screen.blit(text_surf, (self.box_rect.right + self.text_offset, text_y))