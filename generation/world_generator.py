import random
from typing import Dict, List, Tuple
from enum import Enum

class Biome(Enum):
    SCRAP_FIELD = "scrap_field"
    MEGACITY_RUINS = "megacity_ruins"
    MILITARY_NECROPOLIS = "military_necropolis"
    ACID_SWAMP = "acid_swamp"
    IRON_FOREST = "iron_forest"
    GLASS_DESERT = "glass_desert"

class WorldGenerator:
    def __init__(self, seed: int = None):
        self.seed = seed or random.randint(0, 2**32)
        random.seed(self.seed)
    
    def generate_biome_map(self, width: int, height: int) -> Dict[Tuple[int, int], Biome]:
        """Генерирует карту биомов для процедурного мира"""
        biome_map = {}
        # Упрощённая генерация: случайные биомы в разных секторах
        for x in range(0, width, 500):
            for y in range(0, height, 500):
                sector_x = x // 500
                sector_y = y // 500
                dist_from_center = ((sector_x - width//1000)**2 + (sector_y - height//1000)**2)**0.5
                
                if dist_from_center < 2:
                    biome = Biome.SCRAP_FIELD
                elif dist_from_center < 4:
                    biome = random.choice([Biome.IRON_FOREST, Biome.GLASS_DESERT])
                elif dist_from_center < 6:
                    biome = random.choice([Biome.MEGACITY_RUINS, Biome.ACID_SWAMP])
                else:
                    biome = Biome.MILITARY_NECROPOLIS
                
                biome_map[(sector_x, sector_y)] = biome
        
        return biome_map
    
    def generate_resource_nodes(self, biome: Biome, count: int = 10) -> List[Dict]:
        """Генерирует ресурсные узлы в зависимости от биома"""
        nodes = []
        biome_resources = {
            Biome.SCRAP_FIELD: ["iron_scrap", "copper"],
            Biome.IRON_FOREST: ["iron_scrap", "titanium"],
            Biome.GLASS_DESERT: ["quartz_sand", "copper"],
            Biome.MEGACITY_RUINS: ["iron_scrap", "pcb", "servo"],
            Biome.ACID_SWAMP: ["crude_oil", "copper"],
            Biome.MILITARY_NECROPOLIS: ["titanium", "energon", "ai_core"]
        }
        
        available = biome_resources.get(biome, ["iron_scrap"])
        
        for _ in range(count):
            node = {
                "x": random.randint(0, 500),
                "y": random.randint(0, 500),
                "type": random.choice(available),
                "amount": random.randint(500, 5000)
            }
            nodes.append(node)
        
        return nodes
    
    def generate_wreckage(self, biome: Biome, difficulty: int) -> List[Dict]:
        """Генерирует обломки для разбора в Рециклере"""
        wreckages = []
        
        if difficulty < 3:
            count = random.randint(3, 7)
            types = ["drone_wreck", "vehicle_chassis", "household_tech"]
        elif difficulty < 6:
            count = random.randint(5, 10)
            types = ["tank_hull", "industrial_robot", "power_armor"]
        else:
            count = random.randint(2, 5)
            types = ["battleship_core", "orbital_cannon", "titan_mech"]
        
        for _ in range(count):
            wreckage = {
                "x": random.randint(0, 500),
                "y": random.randint(0, 500),
                "type": random.choice(types),
                "hp": random.randint(100, 1000),
                "loot_table": self._get_loot_table(random.choice(types))
            }
            wreckages.append(wreckage)
        
        return wreckages
    
    def _get_loot_table(self, wreck_type: str) -> List[Dict]:
        """Определяет таблицу лута для типа обломка"""
        loot_tables = {
            "drone_wreck": [
                {"type": "iron_scrap", "min": 10, "max": 30, "chance": 1.0},
                {"type": "pcb", "min": 1, "max": 3, "chance": 0.5},
                {"type": "lens", "min": 1, "max": 2, "chance": 0.3}
            ],
            "tank_hull": [
                {"type": "iron_scrap", "min": 50, "max": 100, "chance": 1.0},
                {"type": "servo", "min": 2, "max": 5, "chance": 0.7},
                {"type": "titanium", "min": 5, "max": 15, "chance": 0.4}
            ],
            "battleship_core": [
                {"type": "titanium", "min": 50, "max": 100, "chance": 1.0},
                {"type": "ai_core", "min": 1, "max": 3, "chance": 0.8},
                {"type": "grav_compensator", "min": 1, "max": 2, "chance": 0.5},
                {"type": "energon", "min": 20, "max": 50, "chance": 0.6}
            ]
        }
        return loot_tables.get(wreck_type, [{"type": "iron_scrap", "min": 5, "max": 15, "chance": 1.0}])