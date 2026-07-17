#!/usr/bin/env python3
"""Сервер Frontier: Salvage"""

import sys
import os
import socket
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from network.network_manager import GameServer, NetworkMessage

class SmartServer(GameServer):
    def __init__(self, host="0.0.0.0", port=7777, max_players=4):
        super().__init__(host, port, max_players)
        self.steam = None
        self.use_steam = False
    
    def start(self):
        # Пробуем занять порт
        tried_ports = []
        max_attempts = 10
        
        for attempt in range(max_attempts):
            try:
                self.socket.bind((self.host, self.port))
                break  # Успешно заняли порт
            except OSError as e:
                tried_ports.append(self.port)
                if attempt < max_attempts - 1:
                    print(f"[!] Порт {self.port} занят, пробую {self.port + 1}...")
                    self.port += 1
                    self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                else:
                    print(f"[X] Не удалось найти свободный порт после {max_attempts} попыток")
                    print(f"    Занятые порты: {tried_ports}")
                    print(f"    Закройте другие программы или перезагрузите компьютер")
                    return
        
        self.running = True
        
        # Показываем информацию
        local_ip = self._get_local_ip()
        print(f"\n{'='*50}")
        print(f"Сервер запущен!")
        print(f"Локальный IP: {local_ip}")
        print(f"Порт: {self.port}")
        print(f"\nКлиенты подключаются командой:")
        print(f"python main.py --connect {local_ip} --port {self.port}")
        print(f"{'='*50}\n")
        
        from game.world import World
        self.world = World(seed=42)
        
        self._game_loop()
    
    def _get_local_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"
    
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
    
    def stop(self):
        self.running = False
        try:
            self.socket.close()
        except:
            pass

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Frontier: Salvage Server")
    parser.add_argument("--host", default="0.0.0.0", help="IP адрес")
    parser.add_argument("--port", type=int, default=7777, help="Порт (если занят, будет выбран следующий)")
    parser.add_argument("--max-players", type=int, default=4, help="Максимум игроков")
    args = parser.parse_args()
    
    server = SmartServer(
        host=args.host,
        port=args.port,
        max_players=args.max_players
    )
    
    print(f"Запуск сервера Frontier: Salvage...")
    
    try:
        server.start()
    except KeyboardInterrupt:
        print("\n[Сервер] Остановлен.")
        server.stop()