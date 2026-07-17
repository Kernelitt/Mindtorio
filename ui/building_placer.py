"""
Система размещения зданий с выбором места на карте
"""
import pygame
import math
from typing import Optional, List, Dict, Tuple
from enum import Enum

class BuildMode:
    """Режимы строительства"""
    NONE = "none"
    PLACING = "placing"
    PLACED = "placed"

class BuildingPlacer:
    """Система выбора и размещения зданий"""

    # Добавляем в класс BuildingPlacer:

    
    
    def __init__(self):
        self.mode = BuildMode.NONE
        self.selected_building: Optional[Dict] = None
        self.buildings_to_place: List[Dict] = []
        self.preview_positions: List[Tuple[float, float]] = []
        self.is_active = False
        
        # Доступные для строительства здания
        self.available_buildings = {
            "turret_mg": {
                "name": "Пулемётная турель",
                "key": "1",
                "recipe": "machinegun_turret",
                "building_type": "turret_mg",
                "color": (150, 150, 150),
                "size": 30,
                "cost": [{"type": "steel_plate", "amount": 10}, {"type": "copper_wire", "amount": 5}]
            },
            "turret_laser": {
                "name": "Лазерная турель",
                "key": "2",
                "recipe": "laser_turret",
                "building_type": "turret_laser",
                "color": (200, 50, 50),
                "size": 30,
                "cost": [{"type": "steel_plate", "amount": 15}, {"type": "lens", "amount": 2}, {"type": "energy_cell", "amount": 3}]
            },
            "turret_flamer": {
                "name": "Огнемётная турель",
                "key": "3",
                "recipe": "flamer_turret",
                "building_type": "turret_flamer",
                "color": (255, 100, 0),
                "size": 30,
                "cost": [{"type": "steel_plate", "amount": 12}, {"type": "fuel", "amount": 20}, {"type": "servo", "amount": 1}]
            },
            "turret_mortar": {
                "name": "Миномётная турель",
                "key": "4",
                "recipe": "mortar_turret",
                "building_type": "turret_mortar",
                "color": (100, 50, 0),
                "size": 30,
                "cost": [{"type": "titanium_alloy", "amount": 8}, {"type": "servo", "amount": 3}, {"type": "pcb", "amount": 2}]
            },
            "recycler": {
                "name": "Рециклер",
                "key": "5",
                "recipe": "recycler",
                "building_type": "recycler",
                "color": (200, 150, 50),
                "size": 35,
                "cost": [{"type": "steel_plate", "amount": 20}, {"type": "servo", "amount": 2}, {"type": "pcb", "amount": 1}]
            },
            "assembler": {
                "name": "Сборочный цех",
                "key": "6",
                "recipe": "assembler",
                "building_type": "assembler",
                "color": (150, 150, 200),
                "size": 35,
                "cost": [{"type": "steel_plate", "amount": 15}, {"type": "copper_wire", "amount": 10}, {"type": "pcb", "amount": 3}]
            },
            "smelter": {
                "name": "Плавильня",
                "key": "7",
                "recipe": "smelter",
                "building_type": "smelter",
                "color": (200, 100, 50),
                "size": 30,
                "cost": [{"type": "steel_plate", "amount": 10}, {"type": "iron_scrap", "amount": 20}]
            },
            "chemical_plant": {
                "name": "Хим. станция",
                "key": "8",
                "recipe": "chemical_plant",
                "building_type": "chemical_plant",
                "color": (100, 200, 100),
                "size": 30,
                "cost": [{"type": "steel_plate", "amount": 12}, {"type": "glass", "amount": 10}, {"type": "copper_wire", "amount": 5}]
            },
            "power_plant": {
                "name": "Энергостанция",
                "key": "9",
                "recipe": "power_plant",
                "building_type": "power_plant",
                "color": (0, 150, 255),
                "size": 35,
                "cost": [{"type": "titanium_alloy", "amount": 10}, {"type": "energy_cell", "amount": 5}, {"type": "pcb", "amount": 5}]
            },
            "wall": {
                "name": "Стена",
                "key": "0",
                "recipe": "wall",
                "building_type": "wall",
                "color": (150, 150, 150),
                "size": 25,
                "cost": [{"type": "steel_plate", "amount": 15}]
            }
        }
    
    def select_building(self, building_key: str) -> bool:
        """Выбрать здание для строительства"""
        if building_key in self.available_buildings:
            self.selected_building = self.available_buildings[building_key]
            self.mode = BuildMode.PLACING
            self.is_active = True
            self.preview_positions = []
            return True
        return False
    
    def can_afford(self, building: Dict, inventory: List[Dict]) -> bool:
        """Проверяет, хватает ли ресурсов для постройки"""
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

    def render_ui(self, screen, inventory: List[Dict] = None):
        """Отрисовывает UI для выбора зданий (упрощённая версия)"""
        # Эта версия теперь не используется, так как есть полноценное меню
        pass
    
    def deselect_building(self):
        """Отменить выбор здания"""
        self.selected_building = None
        self.mode = BuildMode.NONE
        self.is_active = False
        self.preview_positions = []
    
    def add_placement_position(self, x: float, y: float):
        """Добавить позицию для размещения здания"""
        if self.mode == BuildMode.PLACING and self.selected_building:
            self.preview_positions.append((x, y))
            self.mode = BuildMode.PLACED
    
    def clear_positions(self):
        """Очистить позиции после размещения"""
        self.preview_positions = []
        self.mode = BuildMode.PLACING
    
    def confirm_placement(self) -> List[Dict]:
        """Подтвердить размещение всех зданий"""
        if not self.preview_positions:
            return []
        
        buildings = []
        for x, y in self.preview_positions:
            buildings.append({
                "building_type": self.selected_building["building_type"],
                "recipe": self.selected_building["recipe"],
                "x": x,
                "y": y
            })
        
        self.preview_positions = []
        return buildings
    
    def get_building_at_position(self, pos: Tuple[float, float], 
                                 buildings: List[Dict]) -> bool:
        """Проверяет, нет ли уже здания в этой позиции"""
        x, y = pos
        for b in buildings:
            dx = b.get("x", 0) - x
            dy = b.get("y", 0) - y
            if dx*dx + dy*dy < 400:  # Радиус 20
                return True
        return False
    
    def can_afford(self, building: Dict, inventory: List[Dict]) -> bool:
        """Проверяет, хватает ли ресурсов для постройки"""
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
    
    def get_buildings_by_key(self) -> Dict[str, Dict]:
        """Возвращает словарь зданий по клавишам"""
        return self.available_buildings
    
    def render_preview(self, screen, camera_x: float, camera_y: float, 
                       mouse_x: int, mouse_y: int, buildings: List[Dict]):
        """Отрисовывает предпросмотр размещаемых зданий"""
        if self.mode == BuildMode.NONE or not self.selected_building:
            return
        
        # Преобразуем координаты мыши в мировые
        world_x = mouse_x + camera_x
        world_y = mouse_y + camera_y
        
        # Проверяем, можно ли строить здесь
        can_place = not self.get_building_at_position((world_x, world_y), buildings)
        
        # Отрисовка уже выбранных позиций
        for px, py in self.preview_positions:
            screen_x = int(px - camera_x)
            screen_y = int(py - camera_y)
            size = self.selected_building["size"]
            
            # Зелёный контур для уже размещённых
            pygame.draw.rect(screen, (0, 255, 0), 
                           (screen_x - size//2, screen_y - size//2, size, size), 2)
            pygame.draw.rect(screen, (0, 255, 0, 50), 
                           (screen_x - size//2, screen_y - size//2, size, size), 1)
        
        # Если мы в режиме размещения и не нажали ещё
        if self.mode == BuildMode.PLACING:
            # Отрисовка текущей позиции под курсором
            color = (0, 255, 0) if can_place else (255, 0, 0)
            size = self.selected_building["size"]
            alpha = 100 if can_place else 50
            
            # Создаём поверхность с прозрачностью
            surf = pygame.Surface((size, size), pygame.SRCALPHA)
            pygame.draw.rect(surf, (*color, alpha), (0, 0, size, size))
            pygame.draw.rect(surf, color, (0, 0, size, size), 2)
            screen.blit(surf, (int(world_x - camera_x - size//2), 
                             int(world_y - camera_y - size//2)))
            
            # Подпись
            if self.font:
                name_text = self.font.render(self.selected_building["name"], True, (255, 255, 255))
                screen.blit(name_text, (mouse_x - name_text.get_width()//2, mouse_y - 40))
    
    def render_ui(self, screen, inventory: List[Dict] = None):
        """Отрисовывает UI для выбора зданий"""
        if self.mode != BuildMode.NONE:
            # Показываем активный режим
            font = pygame.font.Font(None, 20)
            text = font.render(f"Строительство: {self.selected_building['name']} (ПКМ - отмена)", 
                              True, (255, 255, 0))
            screen.blit(text, (10, 40))
        
        # Панель выбора зданий
        panel_y = 100
        font = pygame.font.Font(None, 18)
        font_small = pygame.font.Font(None, 14)
        
        # Фон панели
        panel_rect = pygame.Rect(10, panel_y - 10, 200, len(self.available_buildings) * 30 + 20)
        pygame.draw.rect(screen, (0, 0, 0, 180), panel_rect, border_radius=5)
        pygame.draw.rect(screen, (50, 50, 50), panel_rect, 1, border_radius=5)
        
        y = panel_y
        for key, building in self.available_buildings.items():
            # Проверяем, можно ли построить
            can_build = True
            if inventory:
                can_build = self.can_afford(building, inventory)
            
            # Цвет текста
            color = (255, 255, 255) if can_build else (100, 100, 100)
            if self.selected_building and self.selected_building["key"] == key:
                color = (0, 255, 0)
            
            # Клавиша
            key_text = font.render(f"[{key}]", True, (200, 200, 200))
            screen.blit(key_text, (20, y))
            
            # Название
            name_text = font.render(building["name"], True, color)
            screen.blit(name_text, (50, y))
            
            # Стоимость
            cost_str = ""
            for cost in building["cost"]:
                if cost_str:
                    cost_str += " "
                cost_str += f"{cost['amount']}{cost['type'][:3]}"
            cost_text = font_small.render(cost_str, True, (150, 150, 150))
            screen.blit(cost_text, (150 - cost_text.get_width(), y + 4))
            
            y += 30
        
        # Информация о текущем выборе
        if self.mode == BuildMode.PLACING:
            info_y = y + 20
            info_text = font.render("ЛКМ - разместить, ПКМ - отмена", True, (255, 255, 100))
            screen.blit(info_text, (20, info_y))
            
            if self.preview_positions:
                count_text = font.render(f"Размещено: {len(self.preview_positions)}", True, (200, 200, 200))
                screen.blit(count_text, (20, info_y + 25))


class BuildingPlacerUI:
    """Интеграция BuildingPlacer с игровым UI"""
    
    def __init__(self, placer: BuildingPlacer):
        self.placer = placer
        self.font = pygame.font.Font(None, 20)
        self.font_small = pygame.font.Font(None, 16)
        placer.font = self.font_small
    
    def handle_event(self, event, mouse_x: int, mouse_y: int, 
                     camera_x: float, camera_y: float,
                     world_state: dict, player_id: str,
                     client) -> List[Dict]:
        """Обрабатывает события мыши и клавиатуры для строительства"""
        buildings_to_place = []
        
        # Проверяем клавиши выбора зданий
        if event.type == pygame.KEYDOWN:
            # Цифры для выбора зданий
            key_map = {
                pygame.K_1: "1", pygame.K_2: "2", pygame.K_3: "3", 
                pygame.K_4: "4", pygame.K_5: "5", pygame.K_6: "6",
                pygame.K_7: "7", pygame.K_8: "8", pygame.K_9: "9",
                pygame.K_0: "0"
            }
            if event.key in key_map:
                key = key_map[event.key]
                if self.placer.mode == BuildMode.NONE:
                    # Выбираем здание
                    if self.placer.select_building(key):
                        print(f"Выбрано здание: {self.placer.selected_building['name']}")
                else:
                    # Если уже в режиме строительства, меняем на другое
                    if self.placer.select_building(key):
                        print(f"Сменено на: {self.placer.selected_building['name']}")
                    else:
                        # Если нажата клавиша без здания - выходим
                        self.placer.deselect_building()
        
        # Обработка кликов мыши
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.placer.mode != BuildMode.NONE:
                if event.button == 1:  # ЛКМ - разместить
                    # Проверяем, не кликнули ли по UI
                    if mouse_x > 220 or mouse_y < 90:
                        world_x = mouse_x + camera_x
                        world_y = mouse_y + camera_y
                        
                        # Проверяем, можно ли строить здесь
                        if world_state:
                            buildings = [e for e in world_state.get("entities", {}).values() 
                                       if "building_type" in e]
                            can_place = not self.placer.get_building_at_position(
                                (world_x, world_y), buildings
                            )
                            
                            if can_place:
                                self.placer.add_placement_position(world_x, world_y)
                                print(f"Добавлена позиция: ({int(world_x)}, {int(world_y)})")
                
                elif event.button == 3:  # ПКМ - отмена/подтверждение
                    if self.placer.preview_positions:
                        # Если есть размещённые, подтверждаем постройку
                        buildings_to_place = self.placer.confirm_placement()
                        if buildings_to_place:
                            print(f"Подтверждено строительство {len(buildings_to_place)} зданий")
                            # Отправляем все здания на сервер
                            for building in buildings_to_place:
                                if client:
                                    client.send_build(
                                        building["building_type"],
                                        building["x"],
                                        building["y"],
                                        building["recipe"]
                                    )
                        # Очищаем позиции, но остаёмся в режиме строительства
                        self.placer.clear_positions()
                    else:
                        # Если нет размещённых - выходим из режима
                        self.placer.deselect_building()
                        print("Режим строительства отменён")
        
        return buildings_to_place