import uuid
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class Entity:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    x: float = 0
    y: float = 0
    hp: int = 100
    max_hp: int = 100
    owner_id: Optional[str] = None
    
    def update(self, world, dt: float):
        pass
    
    def take_damage(self, damage: int) -> bool:
        self.hp -= damage
        return self.hp <= 0
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "x": self.x,
            "y": self.y,
            "hp": self.hp,
            "max_hp": self.max_hp,
            "owner_id": self.owner_id
        }