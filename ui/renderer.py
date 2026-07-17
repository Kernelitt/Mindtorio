import pygame
import math

class GameRenderer:
    def __init__(self, screen, client):
        self.screen = screen
        self.client = client
        self.font_small = pygame.font.Font(None, 20)
        self.font = pygame.font.Font(None, 24)
        self.font_large = pygame.font.Font(None, 32)
        self.camera_x = 0
        self.camera_y = 0
        
        # Цвета для разных типов местности
        self.terrain_colors = {
            "water_deep": (20, 40, 80),
            "water_shallow": (30, 80, 120),
            "beach": (220, 210, 170),
            "grassland": (100, 180, 80),
            "forest": (60, 140, 60),
            "mountain": (120, 100, 80),
            "peak": (200, 190, 180),
            "desert": (210, 190, 140),
            "savanna": (180, 170, 100),
            "taiga": (80, 130, 100),
            "plains": (140, 180, 110),
            "snow_peak": (240, 245, 250),
            "ocean": (25, 60, 100),
        }
        
        # Цвета для зданий
        self.building_colors = {
            "recycler": (200, 150, 50),
            "assembler": (150, 150, 200),
            "smelter": (200, 100, 50),
            "chemical_plant": (100, 200, 100),
            "power_plant": (0, 150, 255),
            "turret_mg": (100, 100, 100),
            "turret_laser": (200, 50, 50),
            "turret_flamer": (255, 100, 0),
            "turret_mortar": (100, 50, 0),
            "wall": (150, 150, 150),
        }
    
    def render(self, dt: float):
        self.screen.fill((20, 20, 30))
        
        if not self.client.world_state:
            self._render_connecting()
            return
        
        world = self.client.world_state
        player_data = None
        
        # Центрируем камеру на игроке
        for eid, entity in world.get("entities", {}).items():
            if eid == self.client.player_id:
                player_data = entity
                self.camera_x = entity["x"] - self.screen.get_width() // 2
                self.camera_y = entity["y"] - self.screen.get_height() // 2
                break
        
        # Рендерим ресурсные узлы
        self._render_resources(world)
        
        # Рендерим сущности
        for eid, entity in world.get("entities", {}).items():
            x = int(entity["x"] - self.camera_x)
            y = int(entity["y"] - self.camera_y)
            
            if -50 <= x <= self.screen.get_width() + 50 and -50 <= y <= self.screen.get_height() + 50:
                if "building_type" in entity:
                    self._render_building(entity, x, y)
                elif "enemy_type" in entity:
                    self._render_enemy(entity, x, y)
                elif "role" in entity:
                    self._render_player(entity, x, y, eid == self.client.player_id)
        
        # Рендерим UI
        self._render_ui(world, player_data)
    
    def _render_resources(self, world):
        for node in world.get("resource_nodes", []):
            x = int(node["x"] - self.camera_x)
            y = int(node["y"] - self.camera_y)
            if -50 <= x <= self.screen.get_width() + 50 and -50 <= y <= self.screen.get_height() + 50:
                color = node.get("color")
                if not color:
                    color = {
                        "iron_scrap": (150, 100, 50),
                        "copper": (50, 200, 150),
                        "quartz_sand": (240, 240, 240),
                        "crude_oil": (50, 50, 50),
                        "titanium": (100, 50, 200),
                        "energon": (0, 200, 255),
                    }.get(node["type"], (100, 100, 100))
                
                size = 8
                if node["type"] == "titanium":
                    size = 6
                elif node["type"] == "energon":
                    size = 5
                elif node["type"] == "crude_oil":
                    size = 10
                
                pygame.draw.circle(self.screen, color, (x, y), size)
    
    def _render_connecting(self):
        text = self.font_large.render("Подключение к серверу...", True, (255, 255, 255))
        rect = text.get_rect(center=(self.screen.get_width()//2, self.screen.get_height()//2))
        self.screen.blit(text, rect)
    
    def _render_building(self, entity, x, y):
        color = self.building_colors.get(entity.get("building_type"), (100, 100, 100))
        size = 25
        if entity.get("building_type") in ["recycler", "assembler", "power_plant"]:
            size = 30
        elif entity.get("building_type") == "wall":
            size = 20
        
        pygame.draw.rect(self.screen, color, (x-size//2, y-size//2, size, size))
        pygame.draw.rect(self.screen, (255, 255, 255), (x-size//2, y-size//2, size, size), 1)
    
    def _render_enemy(self, entity, x, y):
        colors = {
            "shard": (255, 100, 100),
            "glass_swarm": (200, 200, 255),
            "crystal_crab": (150, 100, 200),
            "screamer": (255, 200, 100),
            "golem": (200, 50, 200),
            "mirror_drone": (100, 200, 255),
            "worm": (150, 75, 0),
            "leviathan": (255, 0, 0),
        }
        color = colors.get(entity.get("enemy_type"), (255, 0, 0))
        size = 25 if entity.get("enemy_type") == "leviathan" else 15
        pygame.draw.circle(self.screen, color, (x, y), size)
        
        if entity.get("max_hp", 0) > 0:
            hp_ratio = max(0, entity.get("hp", 0) / entity["max_hp"])
            bar_width = 30
            pygame.draw.rect(self.screen, (255, 0, 0), (x-bar_width//2, y-20, bar_width, 4))
            pygame.draw.rect(self.screen, (0, 255, 0), (x-bar_width//2, y-20, int(bar_width*hp_ratio), 4))
    
    def _render_player(self, entity, x, y, is_self):
        color = tuple(entity.get("role_color", [255, 255, 255]))
        
        if is_self:
            pygame.draw.circle(self.screen, (255, 255, 255), (x, y), 16, 2)
        
        pygame.draw.circle(self.screen, color, (x, y), 12)
        
        name_text = self.font_small.render(
            f"{entity.get('name', '')} [{entity.get('role', '')[:4]}]",
            True, (255, 255, 255)
        )
        self.screen.blit(name_text, (x - name_text.get_width()//2, y - 30))
    
    def _render_ui(self, world, player_data):
        # Режим игры
        mode_colors = {"solo": (100, 255, 100), "duo": (255, 255, 100), 
                      "trio": (255, 200, 100), "quad": (255, 100, 100)}
        mode_color = mode_colors.get(self.client.game_mode, (255, 255, 255))
        mode_text = self.font.render(f"Режим: {self.client.game_mode.upper()}", True, mode_color)
        self.screen.blit(mode_text, (10, 10))
        
        # Информация о волне
        wave_text = self.font.render(
            f"Волна: {world.get('wave_number', 0)} | Агрессия: {world.get('aggression', 0):.1f}",
            True, (255, 255, 255)
        )
        self.screen.blit(wave_text, (250, 10))
        
        # Подсказки
        controls = [
            "WASD - движение",
            "SPACE - добыча",
            "B - турель",
            "F5 - сохранение",
            "F9 - загрузка",
            "ESC - выход"
        ]
        
        y_pos = self.screen.get_height() - 30 * len(controls) - 10
        for control in controls:
            text = self.font_small.render(control, True, (200, 200, 200))
            self.screen.blit(text, (10, y_pos))
            y_pos += 25
        
        # Инвентарь
        if player_data and "inventory" in player_data:
            inv_text = self.font_small.render("Инвентарь:", True, (255, 255, 255))
            self.screen.blit(inv_text, (10, 50))
            
            y_pos = 75
            for item in player_data["inventory"][:7]:
                item_text = self.font_small.render(
                    f"  {item['type']}: {item['amount']}",
                    True, (200, 200, 200)
                )
                self.screen.blit(item_text, (10, y_pos))
                y_pos += 20