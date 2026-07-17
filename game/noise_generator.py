"""
Генератор шума Перлина для процедурной генерации мира
"""
import random
import math
from typing import List, Tuple, Optional, Dict

class PerlinNoise:
    """Генератор шума Перлина"""
    
    def __init__(self, seed: int = None):
        self.seed = seed or random.randint(0, 2**32)
        random.seed(self.seed)
        self.perm = self._generate_permutation()
    
    def _generate_permutation(self) -> List[int]:
        """Генерирует таблицу перестановок для шума"""
        p = list(range(256))
        random.shuffle(p)
        return p + p
    
    def _fade(self, t: float) -> float:
        """Функция сглаживания"""
        return t * t * t * (t * (t * 6 - 15) + 10)
    
    def _lerp(self, a: float, b: float, t: float) -> float:
        """Линейная интерполяция"""
        return a + t * (b - a)
    
    def _grad(self, hash_val: int, x: float, y: float) -> float:
        """Градиентная функция"""
        h = hash_val & 3
        u = x if h < 2 else y
        v = y if h < 2 else x
        return (u if (h & 1) == 0 else -u) + (v if (h & 2) == 0 else -v)
    
    def noise2d(self, x: float, y: float) -> float:
        """Двумерный шум Перлина"""
        X = int(math.floor(x)) & 255
        Y = int(math.floor(y)) & 255
        
        xf = x - math.floor(x)
        yf = y - math.floor(y)
        
        u = self._fade(xf)
        v = self._fade(yf)
        
        a = self.perm[X] + Y
        b = self.perm[X + 1] + Y
        
        return self._lerp(
            self._lerp(self._grad(self.perm[a], xf, yf), 
                      self._grad(self.perm[b], xf - 1, yf), u),
            self._lerp(self._grad(self.perm[a + 1], xf, yf - 1),
                      self._grad(self.perm[b + 1], xf - 1, yf - 1), u),
            v
        )
    
    def octave_noise(self, x: float, y: float, octaves: int = 4, 
                     persistence: float = 0.5, lacunarity: float = 2.0) -> float:
        """Шум с несколькими октавами (фрактальный шум)"""
        total = 0.0
        frequency = 1.0
        amplitude = 1.0
        max_val = 0.0
        
        for _ in range(octaves):
            total += self.noise2d(x * frequency, y * frequency) * amplitude
            max_val += amplitude
            amplitude *= persistence
            frequency *= lacunarity
        
        return total / max_val


class WorldGeneratorV2:
    """Генератор мира с использованием трех слоев шума"""
    
    def __init__(self, seed: int = None, width: int = 5000, height: int = 5000):
        self.seed = seed or random.randint(0, 2**32)
        self.width = width
        self.height = height
        
        # Три независимых генератора шума для разных слоёв
        self.height_noise = PerlinNoise(self.seed + 1000)
        self.biome_noise = PerlinNoise(self.seed + 2000)
        self.resource_noise = PerlinNoise(self.seed + 3000)
        
        # Кэш для оптимизации
        self._height_cache = {}
        self._biome_cache = {}
        self._resource_cache = {}
        
        self.resource_nodes = []
        self.height_map = {}
        self.biome_map = {}
        self.resource_map = {}
    
    def generate_height(self, x: float, y: float) -> float:
        """Генерация высоты (ландшафт)"""
        cache_key = (int(x // 10), int(y // 10))
        if cache_key in self._height_cache:
            return self._height_cache[cache_key]
        
        # Масштаб для ландшафта
        scale = 0.005
        
        # Основной шум для высоты
        height = self.height_noise.octave_noise(
            x * scale, y * scale,
            octaves=6, persistence=0.5, lacunarity=2.1
        )
        
        # Добавляем детализацию
        detail_scale = 0.02
        detail = self.height_noise.octave_noise(
            x * detail_scale, y * detail_scale,
            octaves=3, persistence=0.3, lacunarity=3.0
        ) * 0.2
        
        result = height + detail
        
        # Кэшируем результат
        self._height_cache[cache_key] = result
        return result
    
    def get_terrain_type(self, height: float) -> str:
        """Определяет тип местности по высоте"""
        if height < -0.3:
            return "water_deep"      # Глубокая вода
        elif height < -0.1:
            return "water_shallow"   # Мелкая вода
        elif height < 0.1:
            return "beach"           # Пляж/песок
        elif height < 0.3:
            return "grassland"       # Трава/равнина
        elif height < 0.6:
            return "forest"          # Лес/холмы
        elif height < 0.8:
            return "mountain"        # Горы
        else:
            return "peak"            # Вершины гор
    
    def generate_biome(self, x: float, y: float, height: float) -> str:
        """Генерация биома на основе шума"""
        cache_key = (int(x // 20), int(y // 20))
        if cache_key in self._biome_cache:
            return self._biome_cache[cache_key]
        
        # Масштаб для биомов (крупнее чем высота)
        scale = 0.002
        
        # Биомный шум
        biome_value = self.biome_noise.octave_noise(
            x * scale, y * scale,
            octaves=3, persistence=0.5, lacunarity=2.0
        )
        
        # Определяем биом с учётом высоты
        terrain = self.get_terrain_type(height)
        
        # Вода - всегда водный биом
        if terrain in ["water_deep", "water_shallow"]:
            return "ocean"
        
        # На основе шума и высоты выбираем биом
        if terrain == "beach":
            return "beach"
        
        if terrain == "peak":
            return "snow_peak"
        
        if terrain == "mountain":
            return "mountain"
        
        # Для остальных территорий используем шум
        if biome_value < -0.4:
            return "desert"
        elif biome_value < -0.1:
            return "savanna"
        elif biome_value < 0.2:
            return "forest"
        elif biome_value < 0.5:
            return "taiga"
        else:
            return "plains"
    
    def generate_resources(self, x: float, y: float, biome: str, height: float) -> Optional[dict]:
        """Генерация ресурсов на основе шума"""
        cache_key = (int(x // 50), int(y // 50))
        if cache_key in self._resource_cache:
            return self._resource_cache[cache_key]
        
        # Масштаб для ресурсов (мелкий)
        scale = 0.01
        
        # Шум для определения наличия ресурсов
        resource_value = self.resource_noise.octave_noise(
            x * scale, y * scale,
            octaves=2, persistence=0.7, lacunarity=3.0
        )
        
        # Ресурсы только на суше
        if height < -0.05:
            self._resource_cache[cache_key] = None
            return None
        
        # Порог для появления ресурсов
        threshold = 0.3
        
        # Разные пороги для разных биомов
        biome_thresholds = {
            "desert": 0.4,
            "mountain": 0.2,
            "snow_peak": 0.5,
            "taiga": 0.3,
            "plains": 0.35,
            "forest": 0.3,
            "savanna": 0.35,
            "beach": 0.4,
            "ocean": 0.6,
        }
        threshold = biome_thresholds.get(biome, 0.35)
        
        if resource_value < threshold:
            self._resource_cache[cache_key] = None
            return None
        
        # Определяем тип ресурса
        resource_types = {
            "desert": ["quartz_sand", "copper"],
            "mountain": ["iron_scrap", "titanium"],
            "snow_peak": ["titanium", "energon"],
            "taiga": ["iron_scrap", "crude_oil"],
            "plains": ["iron_scrap", "copper"],
            "forest": ["copper", "quartz_sand"],
            "savanna": ["crude_oil", "iron_scrap"],
            "beach": ["quartz_sand", "iron_scrap"],
        }
        
        available = resource_types.get(biome, ["iron_scrap", "copper"])
        
        # Используем шум для выбора типа
        type_idx = int(abs(self.resource_noise.noise2d(x * 0.1, y * 0.1 + 100)) * len(available))
        type_idx = min(type_idx, len(available) - 1)
        resource_type = available[type_idx]
        
        # Количество ресурсов зависит от высоты и шума
        base_amount = int(abs(resource_value - threshold) * 2000 + 500)
        
        # Бонус за высоту для некоторых ресурсов
        if resource_type in ["titanium", "energon"] and height > 0.5:
            base_amount = int(base_amount * 1.5)
        elif resource_type in ["crude_oil"] and height < 0.2:
            base_amount = int(base_amount * 1.3)
        
        # Минимальное количество
        base_amount = max(100, base_amount)
        
        resource = {
            "x": x,
            "y": y,
            "type": resource_type,
            "amount": base_amount,
            "biome": biome,
            "height": height
        }
        
        self._resource_cache[cache_key] = resource
        return resource
    
    def generate_world(self) -> List[dict]:
        """Генерирует полный мир с ресурсами"""
        resources = []
        
        # Шаг сетки для размещения ресурсов
        step = 25
        
        # Количество ресурсных узлов
        nodes_count = 0
        
        for x in range(100, self.width - 100, step):
            for y in range(100, self.height - 100, step):
                # Генерируем высоту
                height = self.generate_height(x, y)
                
                # Генерируем биом
                biome = self.generate_biome(x, y, height)
                
                # Генерируем ресурсы
                resource = self.generate_resources(x, y, biome, height)
                
                if resource:
                    # Добавляем цвета для рендеринга
                    colors = {
                        "iron_scrap": (150, 100, 50),
                        "copper": (50, 200, 150),
                        "quartz_sand": (240, 240, 240),
                        "crude_oil": (50, 50, 50),
                        "titanium": (100, 50, 200),
                        "energon": (0, 200, 255),
                    }
                    resource["color"] = colors.get(resource["type"], (100, 100, 100))
                    resources.append(resource)
                    nodes_count += 1
        
        self.resource_nodes = resources
        
        print(f"Сгенерировано {nodes_count} ресурсных узлов")
        return resources
    
    def get_resources_in_area(self, x: float, y: float, radius: float) -> List[dict]:
        """Возвращает ресурсы в радиусе от точки"""
        result = []
        for node in self.resource_nodes:
            dx = node["x"] - x
            dy = node["y"] - y
            if dx*dx + dy*dy <= radius*radius:
                result.append(node)
        return result
    
    def get_nearest_resource(self, x: float, y: float, resource_type: str = None) -> Optional[dict]:
        """Находит ближайший ресурс"""
        nearest = None
        min_dist = float('inf')
        
        for node in self.resource_nodes:
            if resource_type and node["type"] != resource_type:
                continue
            dx = node["x"] - x
            dy = node["y"] - y
            dist = dx*dx + dy*dy
            if dist < min_dist:
                min_dist = dist
                nearest = node
        
        return nearest
    
    def get_biome_at(self, x: float, y: float) -> str:
        """Возвращает биом в указанной точке"""
        height = self.generate_height(x, y)
        return self.generate_biome(x, y, height)
    
    def get_height_at(self, x: float, y: float) -> float:
        """Возвращает высоту в указанной точке"""
        return self.generate_height(x, y)