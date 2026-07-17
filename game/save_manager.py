"""
Система сохранения и загрузки игры в JSON
"""
import json
import os
import time
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime

class SaveManager:
    """Менеджер сохранений"""
    
    def __init__(self, save_dir: str = "saves"):
        self.save_dir = save_dir
        self.current_save = None
        self._ensure_save_dir()
    
    def _ensure_save_dir(self):
        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir)
    
    def _get_save_path(self, save_name: str) -> str:
        return os.path.join(self.save_dir, f"{save_name}.json")
    
    def _get_metadata_path(self) -> str:
        return os.path.join(self.save_dir, "saves_metadata.json")
    
    def _load_metadata(self) -> Dict:
        meta_path = self._get_metadata_path()
        if os.path.exists(meta_path):
            try:
                with open(meta_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {"saves": []}
        return {"saves": []}
    
    def _save_metadata(self, metadata: Dict):
        meta_path = self._get_metadata_path()
        with open(meta_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    def get_saves_list(self) -> List[Dict]:
        metadata = self._load_metadata()
        return metadata.get("saves", [])
    
    def save_game(self, world_state: Dict, save_name: str = None, 
                  player_name: str = "Игрок") -> bool:
        try:
            save_data = {
                "version": "1.0",
                "save_name": save_name or f"auto_{int(time.time())}",
                "timestamp": time.time(),
                "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "player_name": player_name,
                "world": {
                    "seed": world_state.get("seed"),
                    "width": world_state.get("width", 5000),
                    "height": world_state.get("height", 5000),
                    "time": world_state.get("time", 0),
                    "wave_number": world_state.get("wave_number", 0),
                    "aggression": world_state.get("aggression", 0)
                },
                "entities": world_state.get("entities", {}),
                "resource_nodes": world_state.get("resource_nodes", []),
                "players": world_state.get("players", {})
            }
            
            save_path = self._get_save_path(save_name or save_data["save_name"])
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, indent=2, ensure_ascii=False, default=self._json_serializer)
            
            metadata = self._load_metadata()
            save_info = {
                "name": save_data["save_name"],
                "timestamp": save_data["timestamp"],
                "datetime": save_data["datetime"],
                "player_name": player_name,
                "wave_number": save_data["world"]["wave_number"],
                "file_size": os.path.getsize(save_path)
            }
            
            existing = next((s for s in metadata["saves"] if s["name"] == save_data["save_name"]), None)
            if existing:
                existing.update(save_info)
            else:
                metadata["saves"].append(save_info)
            
            self._save_metadata(metadata)
            self.current_save = save_data["save_name"]
            
            print(f"[Сохранение] Игра сохранена как '{save_data['save_name']}'")
            return True
            
        except Exception as e:
            print(f"[Ошибка сохранения] {e}")
            return False
    
    def load_game(self, save_name: str) -> Optional[Dict]:
        try:
            save_path = self._get_save_path(save_name)
            if not os.path.exists(save_path):
                print(f"[Ошибка] Сохранение '{save_name}' не найдено")
                return None
            
            with open(save_path, 'r', encoding='utf-8') as f:
                save_data = json.load(f)
            
            world_state = {
                "seed": save_data["world"]["seed"],
                "width": save_data["world"]["width"],
                "height": save_data["world"]["height"],
                "time": save_data["world"]["time"],
                "wave_number": save_data["world"]["wave_number"],
                "aggression": save_data["world"]["aggression"],
                "entities": save_data.get("entities", {}),
                "resource_nodes": save_data.get("resource_nodes", []),
                "players": save_data.get("players", {})
            }
            
            self.current_save = save_name
            print(f"[Загрузка] Загружено сохранение '{save_name}'")
            return world_state
            
        except Exception as e:
            print(f"[Ошибка загрузки] {e}")
            return None
    
    def delete_save(self, save_name: str) -> bool:
        try:
            save_path = self._get_save_path(save_name)
            if os.path.exists(save_path):
                os.remove(save_path)
            
            metadata = self._load_metadata()
            metadata["saves"] = [s for s in metadata["saves"] if s["name"] != save_name]
            self._save_metadata(metadata)
            
            if self.current_save == save_name:
                self.current_save = None
            
            return True
        except Exception as e:
            print(f"[Ошибка удаления] {e}")
            return False
    
    def _json_serializer(self, obj):
        if hasattr(obj, "value"):
            return obj.value
        if hasattr(obj, "to_dict"):
            return obj.to_dict()
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


class SaveSystem:
    """Интеграция системы сохранений с игровым миром"""
    
    def __init__(self, world):
        self.world = world
        self.save_manager = SaveManager()
        self.auto_save_timer = 0
        self.auto_save_interval = 300  # 5 минут
    
    def save(self, save_name: str = None) -> bool:
        """Сохраняет текущий мир"""
        world_state = self.world.to_dict()
        return self.save_manager.save_game(
            world_state, 
            save_name,
            self._get_player_name()
        )
    
    def load(self, save_name: str) -> bool:
        """Загружает сохранение в мир"""
        world_state = self.save_manager.load_game(save_name)
        if world_state:
            # Обновляем мир
            self.world.seed = world_state["seed"]
            self.world.width = world_state["width"]
            self.world.height = world_state["height"]
            self.world.time = world_state["time"]
            self.world.wave_manager.wave_number = world_state["wave_number"]
            self.world.wave_manager.aggression_level = world_state["aggression"]
            
            # Восстанавливаем ресурсы
            self.world.resource_nodes = world_state["resource_nodes"]
            
            # Восстанавливаем сущности (упрощённо)
            self.world.entities = world_state["entities"]
            self.world.players = world_state["players"]
            
            return True
        return False
    
    def quick_save(self) -> bool:
        """Быстрое сохранение"""
        world_state = self.world.to_dict()
        return self.save_manager.quick_save(world_state, self._get_player_name())
    
    def auto_save(self) -> bool:
        """Автосохранение"""
        world_state = self.world.to_dict()
        return self.save_manager.auto_save(world_state, self._get_player_name())
    
    def update(self, dt: float):
        """Обновляет таймер автосохранения"""
        self.auto_save_timer += dt
        if self.auto_save_timer >= self.auto_save_interval:
            self.auto_save_timer = 0
            self.auto_save()
    
    def _get_player_name(self) -> str:
        """Возвращает имя первого игрока"""
        for player in self.world.players.values():
            if hasattr(player, "name"):
                return player.name
        return "Игрок"
    
    def get_saves(self) -> List[Dict]:
        """Возвращает список сохранений"""
        return self.save_manager.get_saves_list()
    
    def delete_save(self, save_name: str) -> bool:
        """Удаляет сохранение"""
        return self.save_manager.delete_save(save_name)