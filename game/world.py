from typing import Dict, List, Optional
import random
from .entity import Entity
from .buildings import Building, Turret, BuildingType
from .enemies import Enemy, EnemyType, WaveManager
from .player import Player, PlayerRole
from .save_manager import SaveSystem

class World:
    def __init__(self, seed: int = None, width: int = 5000, height: int = 5000, 
                 load_save: str = None):
        self.seed = seed or random.randint(0, 2**32)
        self.width = width
        self.height = height
        self.entities: Dict[str, Entity] = {}
        self.players: Dict[str, Player] = {}
        self.buildings: Dict[str, Building] = {}
        self.enemies: Dict[str, Enemy] = {}
        self.wave_manager = WaveManager()
        self.time: float = 0
        
        # Система сохранений
        self.save_system = SaveSystem(self)
        
        # Генерируем ресурсы (упрощённо)
        self.resource_nodes = self._generate_resources()
        
        # Пытаемся загрузить сохранение
        if load_save:
            self.load_from_save(load_save)
    
    def _generate_resources(self) -> List[Dict]:
        """Генерирует ресурсы на карте"""
        resources = []
        for _ in range(50):
            node = {
                "x": random.randint(100, self.width - 100),
                "y": random.randint(100, self.height - 100),
                "type": random.choice(["iron_scrap", "copper", "quartz_sand", "crude_oil"]),
                "amount": random.randint(500, 5000),
                "color": (150, 100, 50)
            }
            resources.append(node)
        return resources
    
    def load_from_save(self, save_name: str) -> bool:
        """Загружает мир из сохранения"""
        return self.save_system.load(save_name)
    
    def get_height_at(self, x: float, y: float) -> float:
        return 0.0
    
    def get_biome_at(self, x: float, y: float) -> str:
        return "plains"
    
    def get_resources_in_area(self, x: float, y: float, radius: float) -> List[Dict]:
        result = []
        for node in self.resource_nodes:
            dx = node["x"] - x
            dy = node["y"] - y
            if dx*dx + dy*dy <= radius*radius:
                result.append(node)
        return result
    
    def add_entity(self, entity: Entity):
        self.entities[entity.id] = entity
        if isinstance(entity, Player):
            self.players[entity.id] = entity
        elif isinstance(entity, Turret):
            self.buildings[entity.id] = entity
        elif isinstance(entity, Building):
            self.buildings[entity.id] = entity
        elif isinstance(entity, Enemy):
            self.enemies[entity.id] = entity
    
    def remove_entity(self, entity_id: str):
        if entity_id in self.entities:
            del self.entities[entity_id]
        self.players.pop(entity_id, None)
        self.buildings.pop(entity_id, None)
        self.enemies.pop(entity_id, None)
    
    def update(self, dt: float):
        self.time += dt
        
        # Автосохранение
        if hasattr(self, 'save_system'):
            self.save_system.update(dt)
        
        for enemy in list(self.enemies.values()):
            enemy.update(self, dt)
        
        new_enemies = self.wave_manager.spawn_wave(self)
        for enemy in new_enemies:
            self.add_entity(enemy)
        
        for building in list(self.buildings.values()):
            if isinstance(building, Turret):
                target = building.find_target(list(self.enemies.values()))
                if target:
                    destroyed = building.shoot(target)
                    if destroyed:
                        from .resources import Resource
                        for loot_type, loot_amount in target.drop_loot():
                            building.output_inventory.append(Resource(loot_type, loot_amount))
                        self.remove_entity(target.id)
    
    def to_dict(self) -> dict:
        entities_dict = {}
        for eid, entity in self.entities.items():
            if hasattr(entity, "to_dict"):
                entities_dict[eid] = entity.to_dict()
            else:
                entities_dict[eid] = {"id": eid}
        
        players_dict = {}
        for pid, player in self.players.items():
            if hasattr(player, "to_dict"):
                players_dict[pid] = player.to_dict()
            else:
                players_dict[pid] = {"id": pid}
        
        return {
            "seed": self.seed,
            "width": self.width,
            "height": self.height,
            "time": self.time,
            "entities": entities_dict,
            "wave_number": self.wave_manager.wave_number,
            "aggression": self.wave_manager.aggression_level,
            "resource_nodes": self.resource_nodes,
            "players": players_dict
        }
    
    def save(self, save_name: str = None) -> bool:
        """Сохраняет мир"""
        if hasattr(self, 'save_system'):
            return self.save_system.save(save_name)
        return False
    
    def quick_save(self) -> bool:
        """Быстрое сохранение"""
        if hasattr(self, 'save_system'):
            return self.save_system.quick_save()
        return False