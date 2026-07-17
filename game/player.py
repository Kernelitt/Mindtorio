from enum import Enum
import time
from .entity import Entity
from .inventory import Inventory

class PlayerRole(Enum):
    ENGINEER = "engineer"
    MECHANIC = "mechanic"
    DEFENDER = "defender"

class Player(Entity):
    def __init__(self, player_id: str, name: str, role: PlayerRole, **kwargs):
        # Извлекаем can_switch_roles ДО передачи в Entity
        self.can_switch_roles = kwargs.pop("can_switch_roles", False)
        
        super().__init__(id=player_id, **kwargs)
        
        self.name = name
        self.role = role
        self.inventory = Inventory()
        self.speed: float = 200
        self.role_switch_cooldown: float = 0
        self.abilities = self._get_abilities()
        self.role_color = {
            PlayerRole.ENGINEER: (50, 200, 50),
            PlayerRole.MECHANIC: (200, 200, 50),
            PlayerRole.DEFENDER: (50, 50, 200),
        }
    
    def switch_role(self, new_role: PlayerRole) -> bool:
        if self.can_switch_roles and time.time() - self.role_switch_cooldown > 3.0:
            self.role = new_role
            self.abilities = self._get_abilities()
            self.role_switch_cooldown = time.time()
            return True
        return False
    
    def _get_abilities(self) -> dict:
        return {
            PlayerRole.ENGINEER: {"build_speed": 1.5, "description": "Строитель"},
            PlayerRole.MECHANIC: {"mining_bonus": 1.5, "description": "Шахтёр"},
            PlayerRole.DEFENDER: {"damage_bonus": 1.3, "description": "Защитник"},
        }[self.role]
    
    def move(self, dx: float, dy: float, dt: float):
        self.x += dx * self.speed * dt
        self.y += dy * self.speed * dt
    
    def to_dict(self) -> dict:
        data = super().to_dict()
        data["name"] = self.name
        data["role"] = self.role.value
        data["can_switch_roles"] = self.can_switch_roles
        data["role_color"] = list(self.role_color.get(self.role, (255, 255, 255)))
        data["inventory"] = self.inventory.to_dict()
        return data