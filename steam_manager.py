"""
Steamworks API интеграция для Frontier: Salvage
"""
import sys
import os
import time
import random
from typing import Optional, List, Dict, Callable

class SteamManager:
    """Менеджер Steam API"""
    
    def __init__(self):
        self.app_id = 480  # SpaceWar AppID для тестирования
        self.initialized = False
        self.steamworks = None
        self.steam_id = None
        self.lobby_id = None
        self.lobby_owner = None
        self.lobby_members = []
        self.is_host = False
        self._use_real_steam = False
        
    def initialize(self) -> bool:
        """Инициализация Steamworks API"""
        # Проверяем наличие реального Steam
        try:
            # Пробуем импортировать реальный Steamworks
            import steamworks
            self.steamworks = steamworks.Steamworks()
            self.steamworks.initialize()
            self.steam_id = self.steamworks.User.GetSteamID()
            self.initialized = True
            self._use_real_steam = True
            print(f"[Steam] Реальный Steam инициализирован! SteamID: {self.steam_id}")
            print(f"[Steam] Имя пользователя: {self.steamworks.Friends.GetPersonaName()}")
            return True
        except ImportError:
            print("[Steam] steamworks-py не установлен, использую эмуляцию")
        except Exception as e:
            print(f"[Steam] Ошибка инициализации реального Steam: {e}")
        
        # Если реальный Steam недоступен - используем эмуляцию
        try:
            # Генерируем фейковый Steam ID
            self.steam_id = f"STEAM_{random.randint(100000, 999999)}"
            self.initialized = True
            self._use_real_steam = False
            print(f"[Steam] Эмуляция Steam! SteamID: {self.steam_id}")
            print("[Steam] ВНИМАНИЕ: Используется эмуляция, мультиплеер работает по локальной сети")
            return True
        except Exception as e:
            print(f"[Steam] Ошибка инициализации эмуляции: {e}")
            return False
    
    def create_lobby(self, lobby_type: str = "public", max_players: int = 4) -> bool:
        """Создаёт лобби в Steam"""
        if not self.initialized:
            print("[Steam] API не инициализирован")
            return False
        
        try:
            if self._use_real_steam:
                # Реальное создание лобби через Steam
                lobby_types = {
                    "private": 0,
                    "friends_only": 1,
                    "public": 2,
                    "invisible": 3
                }
                lt = lobby_types.get(lobby_type, 2)
                self.lobby_id = self.steamworks.Matchmaking.CreateLobby(lt, max_players)
                
                if self.lobby_id:
                    self.is_host = True
                    self.lobby_owner = self.steam_id
                    print(f"[Steam] Реальное лобби создано! ID: {self.lobby_id}")
                    
                    # Устанавливаем данные лобби
                    self.steamworks.Matchmaking.SetLobbyData(self.lobby_id, "game", "Frontier: Salvage")
                    self.steamworks.Matchmaking.SetLobbyData(self.lobby_id, "version", "0.2.0")
                    self.steamworks.Matchmaking.SetLobbyData(self.lobby_id, "host_name", 
                                                            self.steamworks.Friends.GetPersonaName())
                    return True
                else:
                    print("[Steam] Не удалось создать лобби")
                    return False
            else:
                # Эмуляция создания лобби
                self.lobby_id = f"STEAM_LOBBY_{random.randint(1000, 9999)}_{int(time.time())}"
                self.is_host = True
                self.lobby_owner = self.steam_id
                print(f"[Steam] Лобби создано (эмуляция)! ID: {self.lobby_id}")
                return True
                
        except Exception as e:
            print(f"[Steam] Ошибка создания лобби: {e}")
            return False
    
    def join_lobby(self, lobby_id: str) -> bool:
        """Присоединяется к лобби по ID"""
        if not self.initialized:
            return False
        
        try:
            if self._use_real_steam:
                # Реальное подключение к лобби через Steam
                result = self.steamworks.Matchmaking.JoinLobby(lobby_id)
                if result:
                    self.lobby_id = lobby_id
                    self.is_host = False
                    print(f"[Steam] Присоединились к реальному лобби {lobby_id}")
                    return True
                return False
            else:
                # Эмуляция подключения
                self.lobby_id = lobby_id
                self.is_host = False
                print(f"[Steam] Присоединились к лобби (эмуляция) {lobby_id}")
                return True
        except Exception as e:
            print(f"[Steam] Ошибка подключения к лобби: {e}")
            return False
    
    def get_lobby_id(self) -> Optional[str]:
        """Возвращает ID текущего лобби"""
        return self.lobby_id
    
    def get_lobby_id_string(self) -> str:
        """Возвращает ID лобби в виде строки"""
        return str(self.lobby_id) if self.lobby_id else ""
    
    def get_lobby_members(self) -> List[Dict]:
        """Возвращает список игроков в лобби"""
        if not self.lobby_id:
            return []
        
        try:
            if self._use_real_steam:
                count = self.steamworks.Matchmaking.GetNumLobbyMembers(self.lobby_id)
                members = []
                for i in range(count):
                    member_id = self.steamworks.Matchmaking.GetLobbyMemberByIndex(
                        self.lobby_id, i
                    )
                    member_name = self.steamworks.Friends.GetFriendPersonaName(member_id)
                    members.append({
                        "id": str(member_id), 
                        "name": member_name,
                        "is_host": member_id == self.lobby_owner
                    })
                return members
            else:
                # Эмуляция списка участников
                return [
                    {"id": self.lobby_owner or "STEAM_1", "name": "Host Player", "is_host": True},
                    {"id": "STEAM_2", "name": "Player 2", "is_host": False},
                ]
        except Exception as e:
            print(f"[Steam] Ошибка получения членов лобби: {e}")
            return []
    
    def get_lobby_owner(self) -> Optional[str]:
        """Возвращает ID владельца лобби"""
        if not self.initialized or not self.lobby_id:
            return None
        
        try:
            if self._use_real_steam:
                owner = self.steamworks.Matchmaking.GetLobbyOwner(self.lobby_id)
                self.lobby_owner = owner
                return str(owner)
            else:
                return str(self.lobby_owner)
        except:
            return None
    
    def invite_friend(self, friend_steam_id: str):
        """Приглашает друга в лобби"""
        if not self.initialized or not self.lobby_id:
            return
        
        try:
            if self._use_real_steam:
                result = self.steamworks.Friends.InviteUserToLobby(
                    self.lobby_id, 
                    int(friend_steam_id)
                )
                if result:
                    print(f"[Steam] Приглашение отправлено другу {friend_steam_id}")
            else:
                print(f"[Steam] Приглашение (эмуляция) другу {friend_steam_id}")
        except Exception as e:
            print(f"[Steam] Ошибка приглашения: {e}")
    
    def set_lobby_data(self, key: str, value: str):
        """Устанавливает данные лобби"""
        if not self.initialized or not self.lobby_id:
            return
        
        try:
            if self._use_real_steam:
                self.steamworks.Matchmaking.SetLobbyData(self.lobby_id, key, value)
        except Exception as e:
            print(f"[Steam] Ошибка данных лобби: {e}")
    
    def get_lobby_data(self, key: str) -> str:
        """Получает данные лобби"""
        if not self.initialized or not self.lobby_id:
            return ""
        
        try:
            if self._use_real_steam:
                return self.steamworks.Matchmaking.GetLobbyData(self.lobby_id, key)
        except:
            pass
        return ""
    
    def get_friends_list(self) -> List[Dict]:
        """Возвращает список друзей в Steam"""
        if not self.initialized:
            return []
        
        try:
            if self._use_real_steam:
                friends = []
                count = self.steamworks.Friends.GetFriendCount()
                for i in range(count):
                    friend_id = self.steamworks.Friends.GetFriendByIndex(i)
                    if self.steamworks.Friends.GetFriendRelationship(friend_id) == 2:
                        friend_name = self.steamworks.Friends.GetFriendPersonaName(friend_id)
                        friends.append({
                            "id": str(friend_id),
                            "name": friend_name,
                            "in_game": self.steamworks.Friends.GetFriendGamePlayed(friend_id)
                        })
                return friends
            else:
                # Эмуляция друзей
                return [
                    {"id": "STEAM_1001", "name": "Friend 1 (Эмуляция)", "in_game": False},
                    {"id": "STEAM_1002", "name": "Friend 2 (Эмуляция)", "in_game": True},
                ]
        except Exception as e:
            print(f"[Steam] Ошибка получения друзей: {e}")
            return []
    
    def set_rich_presence(self, status: str, players: int = 1, max_players: int = 4):
        """Обновляет статус в Steam"""
        if not self.initialized:
            return
        
        try:
            if self._use_real_steam:
                self.steamworks.Friends.SetRichPresence("status", status)
                self.steamworks.Friends.SetRichPresence("players", str(players))
                self.steamworks.Friends.SetRichPresence("max_players", str(max_players))
                self.steamworks.Friends.SetRichPresence("steam_display", f"#Status_{status}")
        except Exception as e:
            print(f"[Steam] Ошибка Rich Presence: {e}")
    
    def run_callbacks(self):
        """Обязательно вызывать каждый кадр!"""
        if self.initialized and self._use_real_steam:
            try:
                self.steamworks.RunCallbacks()
            except:
                pass
    
    def leave_lobby(self):
        """Покидает лобби"""
        if self.initialized and self.lobby_id:
            try:
                if self._use_real_steam:
                    self.steamworks.Matchmaking.LeaveLobby(self.lobby_id)
                self.lobby_id = None
                self.is_host = False
                print("[Steam] Лобби покинуто")
            except Exception as e:
                print(f"[Steam] Ошибка выхода из лобби: {e}")
    
    def shutdown(self):
        """Завершает работу с API"""
        if self.initialized:
            print("[Steam] Отключение API...")
            self.leave_lobby()
            if self._use_real_steam:
                try:
                    self.steamworks.shutdown()
                except:
                    pass
            self.initialized = False


class SteamLobbyManager:
    """Менеджер для управления Steam лобби в игре"""
    
    def __init__(self):
        self.steam = SteamManager()
        self.lobby_id = None
        self.is_host = False
        self.members = []
        self.on_member_join = None
        self.on_member_leave = None
        self.on_lobby_created = None
        self.on_lobby_joined = None
        
    def initialize(self) -> bool:
        """Инициализирует Steam"""
        return self.steam.initialize()
    
    def create_lobby(self) -> Optional[str]:
        """Создаёт лобби и возвращает его ID"""
        if self.steam.create_lobby("public", 4):
            self.lobby_id = self.steam.get_lobby_id()
            self.is_host = True
            if self.on_lobby_created:
                self.on_lobby_created(self.lobby_id)
            return self.lobby_id
        return None
    
    def join_lobby(self, lobby_id: str) -> bool:
        """Присоединяется к лобби по ID"""
        if self.steam.join_lobby(lobby_id):
            self.lobby_id = lobby_id
            self.is_host = False
            if self.on_lobby_joined:
                self.on_lobby_joined(lobby_id)
            return True
        return False
    
    def get_lobby_id(self) -> str:
        """Возвращает ID лобби в виде строки"""
        return self.steam.get_lobby_id_string()
    
    def get_members(self) -> List[Dict]:
        """Возвращает список участников"""
        return self.steam.get_lobby_members()
    
    def invite_friend(self, friend_id: str):
        """Приглашает друга"""
        self.steam.invite_friend(friend_id)
    
    def get_friends(self) -> List[Dict]:
        """Возвращает список друзей"""
        return self.steam.get_friends_list()
    
    def update(self):
        """Обновляет состояние лобби"""
        self.steam.run_callbacks()
        
        if self.lobby_id:
            new_members = self.get_members()
            old_ids = {m["id"] for m in self.members}
            new_ids = {m["id"] for m in new_members}
            
            for member in new_members:
                if member["id"] not in old_ids:
                    if self.on_member_join:
                        self.on_member_join(member)
            
            for member in self.members:
                if member["id"] not in new_ids:
                    if self.on_member_leave:
                        self.on_member_leave(member)
            
            self.members = new_members
    
    def set_rich_presence(self, status: str, players: int = 1, max_players: int = 4):
        """Устанавливает Rich Presence"""
        self.steam.set_rich_presence(status, players, max_players)
    
    def shutdown(self):
        """Завершает работу"""
        self.steam.shutdown()