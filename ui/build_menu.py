"""
Окно выбора зданий для строительства
"""
import pygame
from typing import Optional, List, Dict, Tuple
from enum import Enum

class BuildMenuState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    PLACING = "placing"

class BuildMenu:
    """Окно выбора зданий"""
    
    def __init__(self, screen_width: int = 1280, screen_height: int = 720):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.state = BuildMenuState.CLOSED
        self.selected_building: Optional[Dict] = None
        self.scroll_offset = 0
        self.max_visible = 8
        self.font = None
        self.font_small = None
        self.font_title = None
        
        # Доступные для строительства здания
        self.buildings = [
            {
                "id": "turret_mg",
                "name": "Пулемётная турель",
                "description": "Базовая турель с высоким темпом стрельбы",
                "key": "1",
                "recipe": "machinegun_turret",
                "building_type": "turret_mg",
                "color": (150, 150, 150),
                "size": 30,
                "cost": [
                    {"type": "steel_plate", "amount": 10, "icon": "⬡"},
                    {"type": "copper_wire", "amount": 5, "icon": "≈"}
                ]
            },
            {
                "id": "turret_laser",
                "name": "Лазерная турель",
                "description": "Мощная турель с высокой точностью",
                "key": "2",
                "recipe": "laser_turret",
                "building_type": "turret_laser",
                "color": (200, 50, 50),
                "size": 30,
                "cost": [
                    {"type": "steel_plate", "amount": 15, "icon": "⬡"},
                    {"type": "lens", "amount": 2, "icon": "◈"},
                    {"type": "energy_cell", "amount": 3, "icon": "⚡"}
                ]
            },
            {
                "id": "turret_flamer",
                "name": "Огнемётная турель",
                "description": "Наносит урон по площади",
                "key": "3",
                "recipe": "flamer_turret",
                "building_type": "turret_flamer",
                "color": (255, 100, 0),
                "size": 30,
                "cost": [
                    {"type": "steel_plate", "amount": 12, "icon": "⬡"},
                    {"type": "fuel", "amount": 20, "icon": "🔥"},
                    {"type": "servo", "amount": 1, "icon": "⚙"}
                ]
            },
            {
                "id": "turret_mortar",
                "name": "Миномётная турель",
                "description": "Дальнобойная турель с высоким уроном",
                "key": "4",
                "recipe": "mortar_turret",
                "building_type": "turret_mortar",
                "color": (100, 50, 0),
                "size": 30,
                "cost": [
                    {"type": "titanium_alloy", "amount": 8, "icon": "✦"},
                    {"type": "servo", "amount": 3, "icon": "⚙"},
                    {"type": "pcb", "amount": 2, "icon": "⊞"}
                ]
            },
            {
                "id": "recycler",
                "name": "Рециклер",
                "description": "Перерабатывает ресурсы в компоненты",
                "key": "5",
                "recipe": "recycler",
                "building_type": "recycler",
                "color": (200, 150, 50),
                "size": 35,
                "cost": [
                    {"type": "steel_plate", "amount": 20, "icon": "⬡"},
                    {"type": "servo", "amount": 2, "icon": "⚙"},
                    {"type": "pcb", "amount": 1, "icon": "⊞"}
                ]
            },
            {
                "id": "assembler",
                "name": "Сборочный цех",
                "description": "Создаёт компоненты и здания",
                "key": "6",
                "recipe": "assembler",
                "building_type": "assembler",
                "color": (150, 150, 200),
                "size": 35,
                "cost": [
                    {"type": "steel_plate", "amount": 15, "icon": "⬡"},
                    {"type": "copper_wire", "amount": 10, "icon": "≈"},
                    {"type": "pcb", "amount": 3, "icon": "⊞"}
                ]
            },
            {
                "id": "smelter",
                "name": "Плавильня",
                "description": "Переплавляет руду в слитки",
                "key": "7",
                "recipe": "smelter",
                "building_type": "smelter",
                "color": (200, 100, 50),
                "size": 30,
                "cost": [
                    {"type": "steel_plate", "amount": 10, "icon": "⬡"},
                    {"type": "iron_scrap", "amount": 20, "icon": "⛏"}
                ]
            },
            {
                "id": "chemical_plant",
                "name": "Хим. станция",
                "description": "Производит химические компоненты",
                "key": "8",
                "recipe": "chemical_plant",
                "building_type": "chemical_plant",
                "color": (100, 200, 100),
                "size": 30,
                "cost": [
                    {"type": "steel_plate", "amount": 12, "icon": "⬡"},
                    {"type": "glass", "amount": 10, "icon": "◇"},
                    {"type": "copper_wire", "amount": 5, "icon": "≈"}
                ]
            },
            {
                "id": "power_plant",
                "name": "Энергостанция",
                "description": "Генерирует энергию для других зданий",
                "key": "9",
                "recipe": "power_plant",
                "building_type": "power_plant",
                "color": (0, 150, 255),
                "size": 35,
                "cost": [
                    {"type": "titanium_alloy", "amount": 10, "icon": "✦"},
                    {"type": "energy_cell", "amount": 5, "icon": "⚡"},
                    {"type": "pcb", "amount": 5, "icon": "⊞"}
                ]
            },
            {
                "id": "wall",
                "name": "Стена",
                "description": "Блокирует путь врагам",
                "key": "0",
                "recipe": "wall",
                "building_type": "wall",
                "color": (150, 150, 150),
                "size": 25,
                "cost": [
                    {"type": "steel_plate", "amount": 15, "icon": "⬡"}
                ]
            }
        ]
    
    def toggle(self):
        """Открыть/закрыть меню"""
        if self.state == BuildMenuState.CLOSED:
            self.state = BuildMenuState.OPEN
            self.scroll_offset = 0
        elif self.state == BuildMenuState.OPEN:
            self.state = BuildMenuState.CLOSED
            self.selected_building = None
    
    def open(self):
        """Открыть меню"""
        self.state = BuildMenuState.OPEN
        self.scroll_offset = 0
    
    def close(self):
        """Закрыть меню"""
        self.state = BuildMenuState.CLOSED
        self.selected_building = None
    
    def select_building(self, building_id: str) -> bool:
        """Выбрать здание для строительства"""
        for building in self.buildings:
            if building["id"] == building_id:
                self.selected_building = building
                self.state = BuildMenuState.PLACING
                return True
        return False
    
    def deselect_building(self):
        """Отменить выбор здания"""
        self.selected_building = None
        self.state = BuildMenuState.OPEN
    
    def get_selected_building(self) -> Optional[Dict]:
        """Возвращает выбранное здание"""
        return self.selected_building
    
    def can_afford(self, building: Dict, inventory: List[Dict]) -> bool:
        """Проверяет, хватает ли ресурсов"""
        if not building:
            return False
        
        for cost in building.get("cost", []):
            found = False
            for item in inventory:
                if item["type"] == cost["type"]:
                    if item["amount"] >= cost["amount"]:
                        found = True
                    break
            if not found:
                return False
        return True
    
    def render(self, screen, inventory: List[Dict] = None):
        """Отрисовывает окно выбора зданий"""
        if self.state == BuildMenuState.CLOSED:
            return
        
        # Инициализируем шрифты если ещё нет
        if not self.font:
            self.font = pygame.font.Font(None, 20)
            self.font_small = pygame.font.Font(None, 16)
            self.font_title = pygame.font.Font(None, 28)
        
        # Размеры окна
        window_width = 500
        window_height = 600
        window_x = (self.screen_width - window_width) // 2
        window_y = (self.screen_height - window_height) // 2
        
        # Фон окна
        pygame.draw.rect(screen, (30, 30, 40), (window_x, window_y, window_width, window_height), border_radius=10)
        pygame.draw.rect(screen, (100, 100, 120), (window_x, window_y, window_width, window_height), 2, border_radius=10)
        
        # Заголовок
        if self.state == BuildMenuState.OPEN:
            title = "ВЫБОР ЗДАНИЯ ДЛЯ СТРОИТЕЛЬСТВА"
        else:
            title = f"РАЗМЕЩЕНИЕ: {self.selected_building['name'].upper()}"
        
        title_text = self.font_title.render(title, True, (255, 255, 255))
        title_rect = title_text.get_rect(center=(window_x + window_width//2, window_y + 25))
        screen.blit(title_text, title_rect)
        
        # Разделительная линия
        pygame.draw.line(screen, (80, 80, 100), 
                        (window_x + 20, window_y + 45),
                        (window_x + window_width - 20, window_y + 45), 1)
        
        # Кнопка закрытия
        close_btn = pygame.Rect(window_x + window_width - 35, window_y + 10, 25, 25)
        pygame.draw.rect(screen, (200, 50, 50), close_btn, border_radius=5)
        close_text = self.font.render("✕", True, (255, 255, 255))
        screen.blit(close_text, (close_btn.x + 6, close_btn.y + 2))
        
        # Если режим размещения - показываем инструкцию
        if self.state == BuildMenuState.PLACING:
            info_y = window_y + 60
            info_text = self.font.render(
                f"Клик ЛКМ - разместить {self.selected_building['name']} | ПКМ - отмена",
                True, (255, 255, 100)
            )
            info_rect = info_text.get_rect(center=(window_x + window_width//2, info_y))
            screen.blit(info_text, info_rect)
            
            # Показываем количество размещённых
            return
        
        # Список зданий
        item_height = 60
        padding = 10
        start_y = window_y + 60
        end_y = window_y + window_height - 20
        
        # Прокрутка
        total_items = len(self.buildings)
        visible_items = min(total_items, (end_y - start_y) // item_height)
        
        # Ограничиваем прокрутку
        max_scroll = max(0, total_items - visible_items)
        self.scroll_offset = max(0, min(self.scroll_offset, max_scroll))
        
        # Отрисовка каждого здания
        for idx, building in enumerate(self.buildings):
            item_y = start_y + idx * item_height - self.scroll_offset * item_height
            
            # Пропускаем если вне видимой области
            if item_y + item_height < start_y - 10 or item_y > end_y + 10:
                continue
            
            # Проверяем, можно ли построить
            can_build = True
            if inventory:
                can_build = self.can_afford(building, inventory)
            
            # Фон элемента
            item_rect = pygame.Rect(window_x + 15, item_y, window_width - 30, item_height - 5)
            
            # Цвет фона
            bg_color = (50, 50, 60) if idx % 2 == 0 else (40, 40, 50)
            if self.selected_building and self.selected_building["id"] == building["id"]:
                bg_color = (0, 80, 0)
            elif not can_build:
                bg_color = (60, 30, 30)
            
            pygame.draw.rect(screen, bg_color, item_rect, border_radius=5)
            pygame.draw.rect(screen, (80, 80, 100), item_rect, 1, border_radius=5)
            
            # Клавиша
            key_text = self.font.render(f"[{building['key']}]", True, (200, 200, 200))
            screen.blit(key_text, (item_rect.x + 10, item_rect.y + 8))
            
            # Название
            name_color = (255, 255, 255) if can_build else (150, 150, 150)
            name_text = self.font.render(building["name"], True, name_color)
            screen.blit(name_text, (item_rect.x + 55, item_rect.y + 5))
            
            # Описание
            desc_text = self.font_small.render(building["description"], True, (180, 180, 180))
            screen.blit(desc_text, (item_rect.x + 55, item_rect.y + 25))
            
            # Стоимость
            cost_x = item_rect.x + item_rect.width - 10
            cost_texts = []
            for cost in building["cost"]:
                # Проверяем наличие ресурса в инвентаре
                has_amount = 0
                if inventory:
                    for item in inventory:
                        if item["type"] == cost["type"]:
                            has_amount = item["amount"]
                            break
                
                color = (100, 255, 100) if has_amount >= cost["amount"] else (255, 100, 100)
                cost_str = f"{cost['icon']} {cost['amount']}"
                cost_text = self.font_small.render(cost_str, True, color)
                cost_x -= cost_text.get_width() + 5
                screen.blit(cost_text, (cost_x, item_rect.y + 20))
            
            # Индикатор доступности
            if not can_build:
                no_resources = self.font_small.render("Нет ресурсов!", True, (255, 100, 100))
                screen.blit(no_resources, (item_rect.x + item_rect.width - no_resources.get_width() - 10, 
                                          item_rect.y + 5))
    
    def handle_event(self, event) -> Optional[Dict]:
        """Обрабатывает события мыши и клавиатуры для меню"""
        if self.state == BuildMenuState.CLOSED:
            # Проверяем клавишу открытия меню (B)
            if event.type == pygame.KEYDOWN and event.key == pygame.K_b:
                self.open()
            return None
        
        # Обработка выбора здания по клавишам
        if event.type == pygame.KEYDOWN:
            key_map = {
                pygame.K_1: "1", pygame.K_2: "2", pygame.K_3: "3",
                pygame.K_4: "4", pygame.K_5: "5", pygame.K_6: "6",
                pygame.K_7: "7", pygame.K_8: "8", pygame.K_9: "9",
                pygame.K_0: "0"
            }
            
            if event.key == pygame.K_b:
                if self.state == BuildMenuState.PLACING:
                    self.deselect_building()
                else:
                    self.close()
                return None
            
            if event.key in key_map:
                key = key_map[event.key]
                for building in self.buildings:
                    if building["key"] == key:
                        if self.state == BuildMenuState.OPEN:
                            self.select_building(building["id"])
                            return building
                        elif self.state == BuildMenuState.PLACING:
                            # Если уже в режиме размещения, сменяем здание
                            self.select_building(building["id"])
                            return building
        
        # Обработка кликов мыши
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_x, mouse_y = event.pos
            
            # Проверяем закрытие окна
            if self.state == BuildMenuState.OPEN:
                # Закрытие по клику вне окна
                window_width = 500
                window_height = 600
                window_x = (self.screen_width - window_width) // 2
                window_y = (self.screen_height - window_height) // 2
                
                # Кнопка закрытия
                close_btn = pygame.Rect(window_x + window_width - 35, window_y + 10, 25, 25)
                if close_btn.collidepoint(mouse_x, mouse_y):
                    self.close()
                    return None
                
                # Проверяем клик по зданию
                if window_x + 15 <= mouse_x <= window_x + window_width - 15:
                    item_height = 60
                    start_y = window_y + 60
                    
                    # Определяем индекс кликнутого элемента
                    idx = (mouse_y - start_y) // item_height + self.scroll_offset
                    
                    if 0 <= idx < len(self.buildings):
                        building = self.buildings[idx]
                        # Проверяем, может ли игрок построить
                        # (проверка ресурсов будет позже)
                        self.select_building(building["id"])
                        return building
        
        return None