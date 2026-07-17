from enum import Enum
from typing import Optional, Tuple, List
import random
import time
from .entity import Entity
from .resources import ResourceType

class EnemyType(Enum):
    SHARD = "shard"
    GLASS_SWARM = "glass_swarm"
    CRYSTAL_CRAB = "crystal_crab"
    SCREAMER = "screamer"
    GOLEM = "golem"
    MIRROR_DRONE = "mirror_drone"
    WORM = "worm"
    LEVIATHAN = "leviathan"

class Enemy(Entity):
    def __init__(self, enemy_type: EnemyType, **kwargs):
        super().__init__(**kwargs)
        self.enemy_type = enemy_type
        self.speed: float = 0
        self.damage: int = 0
        self.attack_range: float = 30
        self.target: Optional[Tuple[float, float]] = None
        self._setup_stats()
    
    def _setup_stats(self):
        stats = {
            EnemyType.SHARD: {"hp": 30, "speed": 120, "damage": 10},
            EnemyType.GLASS_SWARM: {"hp": 15, "speed": 150, "damage": 5},
            EnemyType.CRYSTAL_CRAB: {"hp": 80, "speed": 40, "damage": 20},
            EnemyType.SCREAMER: {"hp": 50, "speed": 80, "damage": 0},
            EnemyType.GOLEM: {"hp": 300, "speed": 30, "damage": 50},
            EnemyType.MIRROR_DRONE: {"hp": 40, "speed": 100, "damage": 15},
            EnemyType.WORM: {"hp": 150, "speed": 50, "damage": 25},
            EnemyType.LEVIATHAN: {"hp": 2000, "speed": 15, "damage": 100},
        }
        s = stats.get(self.enemy_type, {"hp": 50, "speed": 50, "damage": 10})
        self.max_hp = s["hp"]
        self.hp = s["hp"]
        self.speed = s["speed"]
        self.damage = s["damage"]
    
    def update(self, world, dt: float):
        # Враги отключены
        pass
    
    def drop_loot(self) -> list:
        return []
    
    def to_dict(self) -> dict:
        data = super().to_dict()
        data["enemy_type"] = self.enemy_type.value
        data["type"] = "enemy"
        return data

class WaveManager:
    def __init__(self):
        self.wave_number: int = 0
        self.aggression_level: float = 0
        self._last_wave_time: float = time.time()
        self.time_between_waves: float = 999999.0  # Враги отключены
        self.player_count: int = 1
    
    def update_difficulty(self, player_count: int):
        pass
    
    def spawn_wave(self, world) -> list:
        # Враги отключены
        return []