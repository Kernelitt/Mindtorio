from enum import Enum
from dataclasses import dataclass

class ResourceType(Enum):
    # Сырьё (добывается из земли)
    IRON_SCRAP = "iron_scrap"        # Железный лом
    COPPER = "copper"                # Медь
    QUARTZ_SAND = "quartz_sand"      # Кварцевый песок
    CRUDE_OIL = "crude_oil"          # Сырая нефть
    TITANIUM = "titanium"            # Титан
    ENERGON = "energon"              # Энергон
    
    # Компоненты (получаются из обломков/переработки)
    STEEL_PLATE = "steel_plate"      # Стальная пластина
    COPPER_WIRE = "copper_wire"      # Медный провод
    GLASS = "glass"                  # Стекло
    PLASTIC = "plastic"              # Пластик
    FUEL = "fuel"                    # Топливо
    TITANIUM_ALLOY = "titanium_alloy" # Титановый сплав
    ENERGY_CELL = "energy_cell"      # Энергоячейка
    
    # Продвинутые компоненты
    PCB = "pcb"                      # Печатные платы
    SERVO = "servo"                  # Сервоприводы
    LENS = "lens"                    # Оптические линзы
    GRAV_COMPENSATOR = "grav_compensator"  # Гравикомпенсатор
    AI_CORE = "ai_core"              # Ядро ИИ
    NANOPLATE = "nanoplate"          # Нанопластина

@dataclass
class Resource:
    type: ResourceType
    amount: int
    
    def __add__(self, other):
        if self.type == other.type:
            return Resource(self.type, self.amount + other.amount)
        raise ValueError("Cannot add different resource types")