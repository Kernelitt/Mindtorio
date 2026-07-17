import socket
import threading
import time
import pickle
from typing import Callable, Dict, Optional
from enum import Enum

class GameMode(Enum):
    SOLO = "solo"
    DUO = "duo"
    TRIO = "trio"
    QUAD = "quad"

class NetworkMessage:
    def __init__(self, msg_type: str, data: dict, sender_id: str = None):
        self.type = msg_type
        self.data = data
        self.sender_id = sender_id
        self.timestamp = time.time()
    
    def to_bytes(self) -> bytes:
        return pickle.dumps(self)
    
    @classmethod
    def from_bytes(cls, data: bytes):
        return pickle.loads(data)

class GameServer:
    """Выделенный сервер для мультиплеера"""
    def __init__(self, host: str = "0.0.0.0", port: int = 7777, max_players: int = 4):
        self.host = host
        self.port = port
        self.max_players = max_players
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.clients: Dict[str, tuple] = {}
        self.world = None
        self.game_mode = GameMode.SOLO
        self.running = False
        self.handlers: Dict[str, Callable] = {}
        self.load_save = None
        self.server_id = None  # Steam Lobby ID или уникальный ID
        
        self.handlers["player_join"] = self.on_player_join
        self.handlers["player_move"] = self.on_player_move
        self.handlers["build_request"] = self.on_build_request
        self.handlers["resource_mine"] = self.on_resource_mine
        self.handlers["player_leave"] = self.on_player_leave
        self.handlers["switch_role"] = self.on_switch_role
        self.handlers["save_request"] = self.on_save_request
        self.handlers["load_request"] = self.on_load_request
        self.handlers["get_server_info"] = self.on_get_server_info
    
    def start(self, load_save: str = None, server_id: str = None):
        self.load_save = load_save
        self.server_id = server_id or f"server_{int(time.time())}"
        self.socket.bind((self.host, self.port))
        self.running = True
        print(f"Сервер запущен на {self.host}:{self.port}")
        print(f"Server ID: {self.server_id}")
        
        from game.world import World
        self.world = World(seed=42, load_save=load_save)
        
        self._game_loop()
    
    def _game_loop(self):
        last_time = time.time()
        while self.running:
            current_time = time.time()
            dt = current_time - last_time
            last_time = current_time
            
            if self.world:
                self.world.update(dt)
            
            try:
                self.socket.settimeout(0.016)
                data, addr = self.socket.recvfrom(65536)
                message = NetworkMessage.from_bytes(data)
                
                if message.sender_id and message.sender_id not in self.clients:
                    self.clients[message.sender_id] = addr
                    print(f"[+] Новый игрок подключился с {addr}")
                
                if message.type in self.handlers:
                    self.handlers[message.type](message.data, message.sender_id)
            except socket.timeout:
                pass
            
            if self.world and len(self.clients) > 0:
                self._broadcast_world_state()
    
    def _broadcast_world_state(self):
        world_data = self.world.to_dict()
        world_data["server_id"] = self.server_id
        world_data["players_count"] = len(self.clients)
        world_data["max_players"] = self.max_players
        message = NetworkMessage("world_state", world_data)
        data = message.to_bytes()
        for client_addr in self.clients.values():
            if client_addr:
                try:
                    self.socket.sendto(data, client_addr)
                except:
                    pass
    
    def on_get_server_info(self, data: dict, sender_id: str):
        """Отправляет информацию о сервере"""
        info = {
            "server_id": self.server_id,
            "players": len(self.clients),
            "max_players": self.max_players,
            "game_mode": self.game_mode.value
        }
        message = NetworkMessage("server_info", info)
        if sender_id in self.clients:
            self.socket.sendto(message.to_bytes(), self.clients[sender_id])
    
    def on_player_join(self, data: dict, sender_id: str):
        from game.player import Player, PlayerRole
        
        if len(self.clients) >= self.max_players:
            return
        
        player = Player(
            player_id=sender_id,
            name=data.get("name", "Игрок"),
            role=PlayerRole(data.get("role", "engineer")),
            x=400 + len(self.clients) * 100,
            y=400
        )
        
        self.world.add_entity(player)
        print(f"Игрок {data.get('name')} подключился как {data.get('role')}")
        
        message = NetworkMessage("join_accepted", {
            "player_id": sender_id,
            "game_mode": "multiplayer",
            "can_switch_roles": False,
            "server_id": self.server_id
        })
        if sender_id in self.clients:
            self.socket.sendto(message.to_bytes(), self.clients[sender_id])
    
    def on_player_move(self, data: dict, sender_id: str):
        if sender_id in self.world.players:
            player = self.world.players[sender_id]
            player.move(data.get("dx", 0), data.get("dy", 0), 0.016)
    
    def on_build_request(self, data: dict, sender_id: str):
        from game.buildings import BuildingType, Turret, Building
        from game.crafting import CraftingSystem
        
        player = self.world.players.get(sender_id)
        if not player:
            return
        
        try:
            building_type = BuildingType(data["building_type"])
        except:
            return
        
        x, y = data.get("x", 0), data.get("y", 0)
        
        recipe_name = data.get("recipe_name")
        if recipe_name:
            recipe = CraftingSystem.get_recipe(recipe_name)
            if recipe:
                for input_res in recipe["inputs"]:
                    if not player.inventory.has(input_res.type, input_res.amount):
                        return
                for input_res in recipe["inputs"]:
                    player.inventory.remove(input_res.type, input_res.amount)
        
        if building_type in [BuildingType.TURRET_MACHINEGUN, BuildingType.TURRET_LASER,
                             BuildingType.TURRET_FLAMER, BuildingType.TURRET_MORTAR]:
            building = Turret(building_type, x=x, y=y, owner_id=sender_id)
        else:
            building = Building(building_type, x=x, y=y, owner_id=sender_id)
        
        self.world.add_entity(building)
    
    def on_resource_mine(self, data: dict, sender_id: str):
        from game.resources import Resource, ResourceType
        
        player = self.world.players.get(sender_id)
        if not player:
            return
        
        nearest_node = None
        min_dist = 100
        
        for node in self.world.resource_nodes:
            dx = node["x"] - player.x
            dy = node["y"] - player.y
            dist = (dx*dx + dy*dy)**0.5
            if dist < min_dist and node["amount"] > 0:
                min_dist = dist
                nearest_node = node
        
        if nearest_node:
            base_mined = {
                "iron_scrap": 15,
                "copper": 12,
                "quartz_sand": 10,
                "crude_oil": 8,
                "titanium": 3,
                "energon": 2,
            }.get(nearest_node["type"], 10)
            
            if player.role.value == "mechanic":
                base_mined = int(base_mined * 1.5)
            
            mined = min(base_mined, nearest_node["amount"])
            nearest_node["amount"] -= mined
            
            resource = Resource(ResourceType(nearest_node["type"]), mined)
            player.inventory.add(resource)
    
    def on_player_leave(self, data: dict, sender_id: str):
        if sender_id in self.world.players:
            self.world.quick_save()
            del self.world.players[sender_id]
        if sender_id in self.clients:
            del self.clients[sender_id]
    
    def on_switch_role(self, data: dict, sender_id: str):
        if sender_id in self.world.players:
            from game.player import PlayerRole
            player = self.world.players[sender_id]
            player.switch_role(PlayerRole(data["role"]))
    
    def on_save_request(self, data: dict, sender_id: str):
        if self.world:
            save_name = data.get("save_name")
            if save_name:
                success = self.world.save(save_name)
            else:
                success = self.world.quick_save()
            
            message = NetworkMessage("save_response", {
                "success": success,
                "save_name": self.world.save_system.save_manager.current_save
            })
            if sender_id in self.clients:
                self.socket.sendto(message.to_bytes(), self.clients[sender_id])
    
    def on_load_request(self, data: dict, sender_id: str):
        save_name = data.get("save_name")
        if self.world and save_name:
            success = self.world.load_from_save(save_name)
            message = NetworkMessage("load_response", {
                "success": success,
                "save_name": save_name
            })
            if sender_id in self.clients:
                self.socket.sendto(message.to_bytes(), self.clients[sender_id])
    
    def stop(self):
        if self.world:
            self.world.quick_save()
        self.running = False
        try:
            self.socket.close()
        except:
            pass

class LocalServer:
    """Встроенный сервер для соло-игры"""
    def __init__(self):
        self.running = False
        self.world = None
        self.game_mode = GameMode.SOLO
        self.local_player_id = None
        self.clients = {}
        self.max_players = 1
        self.load_save = None
        self.server_id = None
    
    def start(self, load_save: str = None, player_name: str = "Игрок", role: str = "engineer", server_id: str = None):
        from game.world import World
        self.load_save = load_save
        self.server_id = server_id or f"local_{int(time.time())}"
        self.world = World(seed=42, load_save=load_save)
        self.running = True
        print(f"Локальный сервер запущен (соло-режим)")
        print(f"Server ID: {self.server_id}")
        if load_save:
            print(f"Загружено сохранение: {load_save}")
        
        return self.connect_local_player(player_name, role)
    
    def connect_local_player(self, name: str, role: str) -> str:
        from game.player import Player, PlayerRole
        
        player_id = f"local_{name}"
        
        if self.world and self.world.players:
            for pid, player in self.world.players.items():
                if player.name == name:
                    self.local_player_id = pid
                    self.clients[pid] = None
                    print(f"Локальный игрок {name} загружен")
                    return pid
        
        player = Player(
            player_id=player_id,
            name=name,
            role=PlayerRole(role),
            x=400,
            y=400,
            can_switch_roles=True
        )
        self.world.add_entity(player)
        self.local_player_id = player_id
        self.clients[player_id] = None
        print(f"Локальный игрок {name} подключился как {role}")
        return player_id
    
    def process_message(self, msg_type: str, data: dict, sender_id: str):
        if msg_type == "player_move":
            if sender_id in self.world.players:
                player = self.world.players[sender_id]
                player.move(data.get("dx", 0), data.get("dy", 0), 0.016)
        
        elif msg_type == "build_request":
            from game.buildings import BuildingType, Turret, Building
            from game.crafting import CraftingSystem
            
            player = self.world.players.get(sender_id)
            if not player:
                return
            
            try:
                building_type = BuildingType(data["building_type"])
            except:
                return
            
            x, y = data.get("x", 0), data.get("y", 0)
            
            recipe_name = data.get("recipe_name")
            if recipe_name:
                recipe = CraftingSystem.get_recipe(recipe_name)
                if recipe:
                    for input_res in recipe["inputs"]:
                        if not player.inventory.has(input_res.type, input_res.amount):
                            print(f"Не хватает ресурсов для {recipe_name}")
                            return
                    for input_res in recipe["inputs"]:
                        player.inventory.remove(input_res.type, input_res.amount)
            
            if building_type in [BuildingType.TURRET_MACHINEGUN, BuildingType.TURRET_LASER,
                                 BuildingType.TURRET_FLAMER, BuildingType.TURRET_MORTAR]:
                building = Turret(building_type, x=x, y=y, owner_id=sender_id)
            else:
                building = Building(building_type, x=x, y=y, owner_id=sender_id)
            
            self.world.add_entity(building)
            print(f"Построено: {building_type.value}")
        
        elif msg_type == "resource_mine":
            from game.resources import Resource, ResourceType
            
            player = self.world.players.get(sender_id)
            if not player:
                return
            
            nearest_node = None
            min_dist = 100
            
            for node in self.world.resource_nodes:
                dx = node["x"] - player.x
                dy = node["y"] - player.y
                dist = (dx*dx + dy*dy)**0.5
                if dist < min_dist and node["amount"] > 0:
                    min_dist = dist
                    nearest_node = node
            
            if nearest_node:
                base_mined = {
                    "iron_scrap": 15,
                    "copper": 12,
                    "quartz_sand": 10,
                    "crude_oil": 8,
                    "titanium": 3,
                    "energon": 2,
                }.get(nearest_node["type"], 10)
                
                if player.role.value == "mechanic":
                    base_mined = int(base_mined * 1.5)
                
                mined = min(base_mined, nearest_node["amount"])
                nearest_node["amount"] -= mined
                
                try:
                    resource = Resource(ResourceType(nearest_node["type"]), mined)
                    player.inventory.add(resource)
                    print(f"Добыто: {nearest_node['type']} x{mined} (осталось: {nearest_node['amount']})")
                except Exception as e:
                    print(f"Ошибка добычи: {e}")
        
        elif msg_type == "switch_role":
            if sender_id in self.world.players:
                from game.player import PlayerRole
                player = self.world.players[sender_id]
                new_role = PlayerRole(data["role"])
                if player.switch_role(new_role):
                    print(f"Роль изменена на {new_role.value}")
        
        elif msg_type == "player_leave":
            if sender_id in self.world.players:
                self.world.quick_save()
        
        elif msg_type == "save_request":
            if self.world:
                save_name = data.get("save_name")
                if save_name:
                    success = self.world.save(save_name)
                else:
                    success = self.world.quick_save()
                print(f"Сохранение {'успешно' if success else 'не удалось'}")
        
        elif msg_type == "load_request":
            save_name = data.get("save_name")
            if self.world and save_name:
                success = self.world.load_from_save(save_name)
                if success:
                    print(f"Загружено сохранение: {save_name}")
        
        elif msg_type == "get_server_info":
            # Возвращаем информацию о сервере
            return {
                "server_id": self.server_id,
                "players": len(self.clients),
                "max_players": self.max_players,
                "game_mode": self.game_mode.value
            }
    
    def update(self, dt: float):
        if self.world:
            self.world.update(dt)
    
    def stop(self):
        if self.world:
            self.world.quick_save()
        self.running = False

class GameClient:
    """Клиент игры"""
    def __init__(self, server_host: str = None, server_port: int = None):
        self.is_local = (server_host is None)
        self.server_host = server_host or "local"
        self.server_port = server_port or 0
        self.socket = None
        self.player_id: str = None
        self.world_state: dict = None
        self.game_mode: str = "solo"
        self.can_switch_roles: bool = False
        self.local_server: Optional[LocalServer] = None
        self.running = False
        self.load_save = None
        self.server_id = None  # ID сервера для подключения
        self.use_steam = False
        self.steam_manager = None
        self.handlers: Dict[str, Callable] = {}
        
        self.handlers["world_state"] = self.on_world_state
        self.handlers["join_accepted"] = self.on_join_accepted
        self.handlers["save_response"] = self.on_save_response
        self.handlers["load_response"] = self.on_load_response
        self.handlers["server_info"] = self.on_server_info
    
    def connect(self, player_name: str, role: str):
        if self.is_local:
            self.local_server = LocalServer()
            self.local_server.start(self.load_save, player_name, role, self.server_id)
            self.player_id = self.local_server.local_player_id
            self.game_mode = "solo"
            self.can_switch_roles = True
            self.running = True
            self.server_id = self.local_server.server_id
            
            if self.local_server.world:
                self.world_state = self.local_server.world.to_dict()
                self.world_state["server_id"] = self.server_id
            
            server_thread = threading.Thread(target=self._local_server_loop, daemon=True)
            server_thread.start()
        else:
            # Подключение к удалённому серверу
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            message = NetworkMessage("player_join", {
                "name": player_name,
                "role": role,
                "server_id": self.server_id  # Передаём ID сервера для Steam
            }, f"client_{player_name}")
            self.player_id = f"client_{player_name}"
            self.socket.sendto(message.to_bytes(), (self.server_host, self.server_port))
            self.running = True
            
            receive_thread = threading.Thread(target=self._receive_loop, daemon=True)
            receive_thread.start()
    
    def connect_to_server_id(self, server_id: str, player_name: str, role: str):
        """Подключается к серверу по ID (для Steam)"""
        self.server_id = server_id
        self.use_steam = True
        self.is_local = False
        
        # В реальном Steam подключении здесь будет поиск по Lobby ID
        # Для демонстрации используем локальный хост
        self.server_host = "127.0.0.1"
        self.server_port = 7777
        
        self.connect(player_name, role)
    
    def _local_server_loop(self):
        last_time = time.time()
        while self.running:
            current_time = time.time()
            dt = current_time - last_time
            last_time = current_time
            
            if self.local_server:
                self.local_server.update(dt)
                if self.local_server.world:
                    self.world_state = self.local_server.world.to_dict()
                    self.world_state["server_id"] = self.local_server.server_id
                    self.game_mode = self.local_server.game_mode.value
            
            time.sleep(0.016)
    
    def _receive_loop(self):
        while self.running and self.socket:
            try:
                data, _ = self.socket.recvfrom(65536)
                message = NetworkMessage.from_bytes(data)
                if message.type in self.handlers:
                    self.handlers[message.type](message.data, message.sender_id)
            except:
                pass
    
    def send_message(self, msg_type: str, data: dict = None):
        if data is None:
            data = {}
        
        if self.is_local and self.local_server:
            self.local_server.process_message(msg_type, data, self.player_id)
        elif self.socket:
            message = NetworkMessage(msg_type, data, self.player_id)
            try:
                self.socket.sendto(message.to_bytes(), (self.server_host, self.server_port))
            except:
                pass
    
    def send_move(self, dx: float, dy: float):
        self.send_message("player_move", {"dx": dx, "dy": dy})
    
    def send_build(self, building_type: str, x: float, y: float, recipe_name: str = None):
        self.send_message("build_request", {
            "building_type": building_type,
            "x": x,
            "y": y,
            "recipe_name": recipe_name
        })
    
    def send_mine(self):
        self.send_message("resource_mine", {})
    
    def send_switch_role(self, role: str):
        self.send_message("switch_role", {"role": role})
    
    def send_save(self, save_name: str = None):
        self.send_message("save_request", {"save_name": save_name})
    
    def send_load(self, save_name: str):
        self.send_message("load_request", {"save_name": save_name})
    
    def get_server_info(self):
        """Запрашивает информацию о сервере"""
        self.send_message("get_server_info", {})
    
    def on_world_state(self, data: dict, sender_id: str):
        self.world_state = data
    
    def on_join_accepted(self, data: dict, sender_id: str):
        self.player_id = data["player_id"]
        self.game_mode = data.get("game_mode", "solo")
        self.can_switch_roles = data.get("can_switch_roles", False)
        self.server_id = data.get("server_id", self.server_id)
        print(f"Подключен! Режим: {self.game_mode}, ID: {self.player_id}")
        print(f"Server ID: {self.server_id}")
    
    def on_save_response(self, data: dict, sender_id: str):
        success = data.get("success", False)
        save_name = data.get("save_name", "unknown")
        if success:
            print(f"Игра сохранена: {save_name}")
        else:
            print("Ошибка сохранения!")
    
    def on_load_response(self, data: dict, sender_id: str):
        success = data.get("success", False)
        save_name = data.get("save_name", "unknown")
        if success:
            print(f"Игра загружена: {save_name}")
            if self.is_local and self.local_server and self.local_server.world:
                self.world_state = self.local_server.world.to_dict()
        else:
            print(f"Ошибка загрузки: {save_name}")
    
    def on_server_info(self, data: dict, sender_id: str):
        """Обработка информации о сервере"""
        server_id = data.get("server_id")
        players = data.get("players", 0)
        max_players = data.get("max_players", 4)
        game_mode = data.get("game_mode", "solo")
        print(f"Информация о сервере:")
        print(f"  ID: {server_id}")
        print(f"  Игроки: {players}/{max_players}")
        print(f"  Режим: {game_mode}")
    
    def disconnect(self):
        self.send_message("player_leave")
        self.running = False
        if self.local_server:
            self.local_server.stop()
        if self.socket:
            try:
                self.socket.close()
            except:
                pass