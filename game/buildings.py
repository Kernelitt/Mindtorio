from enum import Enum
from typing import List, Dict, Optional
import time
from .entity import Entity
from .resources import Resource

class BuildingType(Enum):
    RECYCLER = "recycler"
    ASSEMBLER = "assembler"
    SMELTER = "smelter"
    CHEMICAL_PLANT = "chemical_plant"
    POWER_PLANT = "power_plant"
    TURRET_MACHINEGUN = "turret_mg"
    TURRET_LASER = "turret_laser"
    TURRET_FLAMER = "turret_flamer"
    TURRET_MORTAR = "turret_mortar"
    WALL = "wall"

class Building(Entity):
    def __init__(self, building_type: BuildingType, **kwargs):
        super().__init__(**kwargs)
        self.building_type = building_type
        self.input_inventory: List[Resource] = []
        self.output_inventory: List[Resource] = []
        self.power_consumption: int = 0
        self.is_powered: bool = False
        self._last_craft_time: float = 0
        self.craft_time: float = 1.0
        self._setup_stats()
    
    def _setup_stats(self):
        stats = {
            BuildingType.RECYCLER: {"hp": 300, "power": 50, "craft_time": 2.0},
            BuildingType.ASSEMBLER: {"hp": 250, "power": 30, "craft_time": 1.5},
            BuildingType.SMELTER: {"hp": 200, "power": 40, "craft_time": 3.0},
            BuildingType.CHEMICAL_PLANT: {"hp": 200, "power": 35, "craft_time": 2.5},
            BuildingType.POWER_PLANT: {"hp": 400, "power": -100, "craft_time": 0},
            BuildingType.TURRET_MACHINEGUN: {"hp": 150, "power": 10, "craft_time": 0.5},
            BuildingType.TURRET_LASER: {"hp": 200, "power": 30, "craft_time": 0.8},
            BuildingType.TURRET_FLAMER: {"hp": 180, "power": 20, "craft_time": 0.6},
            BuildingType.TURRET_MORTAR: {"hp": 250, "power": 25, "craft_time": 1.0},
            BuildingType.WALL: {"hp": 500, "power": 0, "craft_time": 0},
        }
        s = stats.get(self.building_type, {"hp": 100, "power": 0, "craft_time": 0})
        self.max_hp = s["hp"]
        self.hp = s["hp"]
        self.power_consumption = s["power"]
        self.craft_time = s["craft_time"]
    
    def to_dict(self) -> dict:
        data = super().to_dict()
        data["building_type"] = self.building_type.value
        data["is_powered"] = self.is_powered
        data["type"] = "building"
        return data

class Turret(Building):
    def __init__(self, turret_type: BuildingType, **kwargs):
        super().__init__(turret_type, **kwargs)
        self.range: float = 200
        self.damage: int = 10
        self.fire_rate: float = 1.0
        self.target: Optional[Entity] = None
        self._last_shot_time: float = 0
        self._setup_turret_stats()
    
    def _setup_turret_stats(self):
        turret_stats = {
            BuildingType.TURRET_MACHINEGUN: {"range": 250, "damage": 5, "fire_rate": 4.0},
            BuildingType.TURRET_LASER: {"range": 350, "damage": 25, "fire_rate": 1.0},
            BuildingType.TURRET_FLAMER: {"range": 150, "damage": 15, "fire_rate": 10.0},
            BuildingType.TURRET_MORTAR: {"range": 500, "damage": 50, "fire_rate": 0.3},
        }
        stats = turret_stats.get(self.building_type, {})
        self.range = stats.get("range", 200)
        self.damage = stats.get("damage", 10)
        self.fire_rate = stats.get("fire_rate", 1.0)
    
    def find_target(self, enemies: List[Entity]) -> Optional[Entity]:
        closest = None
        min_dist = float('inf')
        for enemy in enemies:
            dx = enemy.x - self.x
            dy = enemy.y - self.y
            dist = (dx*dx + dy*dy)**0.5
            if dist <= self.range and dist < min_dist:
                min_dist = dist
                closest = enemy
        return closest
    
    def shoot(self, target: Entity) -> bool:
        current_time = time.time()
        if current_time - self._last_shot_time < 1.0 / self.fire_rate:
            return False
        self._last_shot_time = current_time
        return target.take_damage(self.damage)
    
    def to_dict(self) -> dict:
        data = super().to_dict()
        data["range"] = self.range
        data["damage"] = self.damage
        data["fire_rate"] = self.fire_rate
        return data