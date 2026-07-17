from typing import List
from .resources import Resource, ResourceType

class Inventory:
    def __init__(self, max_slots: int = 30):
        self.max_slots = max_slots
        self.items: List[Resource] = []
    
    def add(self, resource: Resource) -> bool:
        for item in self.items:
            if item.type == resource.type:
                item.amount += resource.amount
                return True
        if len(self.items) < self.max_slots:
            self.items.append(resource)
            return True
        return False
    
    def remove(self, resource_type: ResourceType, amount: int) -> bool:
        for item in self.items:
            if item.type == resource_type:
                if item.amount >= amount:
                    item.amount -= amount
                    if item.amount == 0:
                        self.items.remove(item)
                    return True
                return False
        return False
    
    def has(self, resource_type: ResourceType, amount: int) -> bool:
        for item in self.items:
            if item.type == resource_type:
                return item.amount >= amount
        return False
    
    def to_dict(self) -> list:
        return [{"type": item.type.value, "amount": item.amount} for item in self.items]