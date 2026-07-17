from typing import Dict
from .resources import Resource, ResourceType

# Все рецепты крафта
RECIPES = {
    # === ПЕРЕРАБОТКА СЫРЬЯ ===
    "steel_plate": {
        "name": "Стальная пластина",
        "inputs": [Resource(ResourceType.IRON_SCRAP, 10)],
        "outputs": [Resource(ResourceType.STEEL_PLATE, 5)],
        "building_type": None,
        "craft_station": "smelter"
    },
    "copper_wire": {
        "name": "Медный провод",
        "inputs": [Resource(ResourceType.COPPER, 5)],
        "outputs": [Resource(ResourceType.COPPER_WIRE, 10)],
        "building_type": None,
        "craft_station": "assembler"
    },
    "glass": {
        "name": "Стекло",
        "inputs": [Resource(ResourceType.QUARTZ_SAND, 10)],
        "outputs": [Resource(ResourceType.GLASS, 8)],
        "building_type": None,
        "craft_station": "smelter"
    },
    "plastic": {
        "name": "Пластик",
        "inputs": [Resource(ResourceType.CRUDE_OIL, 15)],
        "outputs": [Resource(ResourceType.PLASTIC, 10)],
        "building_type": None,
        "craft_station": "chemical_plant"
    },
    "fuel": {
        "name": "Топливо",
        "inputs": [Resource(ResourceType.CRUDE_OIL, 20)],
        "outputs": [Resource(ResourceType.FUEL, 15)],
        "building_type": None,
        "craft_station": "chemical_plant"
    },
    "titanium_alloy": {
        "name": "Титановый сплав",
        "inputs": [
            Resource(ResourceType.TITANIUM, 5),
            Resource(ResourceType.STEEL_PLATE, 3)
        ],
        "outputs": [Resource(ResourceType.TITANIUM_ALLOY, 5)],
        "building_type": None,
        "craft_station": "smelter"
    },
    "energy_cell": {
        "name": "Энергоячейка",
        "inputs": [
            Resource(ResourceType.ENERGON, 5),
            Resource(ResourceType.GLASS, 3)
        ],
        "outputs": [Resource(ResourceType.ENERGY_CELL, 3)],
        "building_type": None,
        "craft_station": "chemical_plant"
    },
    
    # === ПРОДВИНУТЫЕ КОМПОНЕНТЫ ===
    "pcb": {
        "name": "Печатная плата",
        "inputs": [
            Resource(ResourceType.COPPER_WIRE, 5),
            Resource(ResourceType.PLASTIC, 3)
        ],
        "outputs": [Resource(ResourceType.PCB, 1)],
        "building_type": None,
        "craft_station": "assembler"
    },
    "servo": {
        "name": "Сервопривод",
        "inputs": [
            Resource(ResourceType.STEEL_PLATE, 5),
            Resource(ResourceType.COPPER_WIRE, 3)
        ],
        "outputs": [Resource(ResourceType.SERVO, 1)],
        "building_type": None,
        "craft_station": "assembler"
    },
    "lens": {
        "name": "Оптическая линза",
        "inputs": [
            Resource(ResourceType.GLASS, 5),
            Resource(ResourceType.ENERGY_CELL, 1)
        ],
        "outputs": [Resource(ResourceType.LENS, 1)],
        "building_type": None,
        "craft_station": "assembler"
    },
    
    # === ПОСТРОЙКИ ===
    "machinegun_turret": {
        "name": "Пулеметная турель",
        "inputs": [
            Resource(ResourceType.STEEL_PLATE, 10),
            Resource(ResourceType.COPPER_WIRE, 5)
        ],
        "outputs": [],
        "building_type": "turret_mg",
        "craft_station": "assembler"
    },
    "laser_turret": {
        "name": "Лазерная турель",
        "inputs": [
            Resource(ResourceType.STEEL_PLATE, 15),
            Resource(ResourceType.LENS, 2),
            Resource(ResourceType.ENERGY_CELL, 3)
        ],
        "outputs": [],
        "building_type": "turret_laser",
        "craft_station": "assembler"
    },
    "flamer_turret": {
        "name": "Огнеметная турель",
        "inputs": [
            Resource(ResourceType.STEEL_PLATE, 12),
            Resource(ResourceType.FUEL, 20),
            Resource(ResourceType.SERVO, 1)
        ],
        "outputs": [],
        "building_type": "turret_flamer",
        "craft_station": "assembler"
    },
    "mortar_turret": {
        "name": "Минометная турель",
        "inputs": [
            Resource(ResourceType.TITANIUM_ALLOY, 8),
            Resource(ResourceType.SERVO, 3),
            Resource(ResourceType.PCB, 2)
        ],
        "outputs": [],
        "building_type": "turret_mortar",
        "craft_station": "assembler"
    },
    "recycler": {
        "name": "Рециклер",
        "inputs": [
            Resource(ResourceType.STEEL_PLATE, 20),
            Resource(ResourceType.SERVO, 2),
            Resource(ResourceType.PCB, 1)
        ],
        "outputs": [],
        "building_type": "recycler",
        "craft_station": "assembler"
    },
    "assembler": {
        "name": "Сборочный цех",
        "inputs": [
            Resource(ResourceType.STEEL_PLATE, 15),
            Resource(ResourceType.COPPER_WIRE, 10),
            Resource(ResourceType.PCB, 3)
        ],
        "outputs": [],
        "building_type": "assembler",
        "craft_station": "assembler"
    },
    "smelter": {
        "name": "Плавильня",
        "inputs": [
            Resource(ResourceType.STEEL_PLATE, 10),
            Resource(ResourceType.IRON_SCRAP, 20)
        ],
        "outputs": [],
        "building_type": "smelter",
        "craft_station": "assembler"
    },
    "chemical_plant": {
        "name": "Химическая станция",
        "inputs": [
            Resource(ResourceType.STEEL_PLATE, 12),
            Resource(ResourceType.GLASS, 10),
            Resource(ResourceType.COPPER_WIRE, 5)
        ],
        "outputs": [],
        "building_type": "chemical_plant",
        "craft_station": "assembler"
    },
    "power_plant": {
        "name": "Энергостанция",
        "inputs": [
            Resource(ResourceType.TITANIUM_ALLOY, 10),
            Resource(ResourceType.ENERGY_CELL, 5),
            Resource(ResourceType.PCB, 5)
        ],
        "outputs": [],
        "building_type": "power_plant",
        "craft_station": "assembler"
    },
    "wall": {
        "name": "Стена",
        "inputs": [Resource(ResourceType.STEEL_PLATE, 15)],
        "outputs": [],
        "building_type": "wall",
        "craft_station": "assembler"
    },
}

class CraftingSystem:
    @staticmethod
    def get_recipe(name: str) -> Dict:
        return RECIPES.get(name)
    
    @staticmethod
    def get_all_recipes() -> Dict:
        return RECIPES
    
    @staticmethod
    def get_recipes_by_station(station_type: str) -> Dict:
        return {
            name: recipe for name, recipe in RECIPES.items()
            if recipe["craft_station"] == station_type
        }