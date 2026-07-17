#!/usr/bin/env python3
"""Клиент Frontier: Salvage"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame
import time
from frontier_salvage.network.network_manager import GameClient
from frontier_salvage.ui.renderer import GameRenderer

def run_client(name: str, role: str, connect_to: str = None, port: int = 7777):
    pygame.init()
    screen = pygame.display.set_mode((1280, 720))
    
    if connect_to:
        client = GameClient(server_host=connect_to, server_port=port)
        mode_text = f"Клиент → {connect_to}"
    else:
        client = GameClient()
        mode_text = "Соло-режим"
    
    pygame.display.set_caption(f"Frontier: Salvage - {name} [{role}] - {mode_text}")
    clock = pygame.time.Clock()
    
    client.connect(name, role)
    
    wait_start = time.time()
    while not client.player_id:
        pygame.time.wait(50)
        if time.time() - wait_start > 5:
            print("Таймаут подключения!")
            return
    
    renderer = GameRenderer(screen, client)
    
    running = True
    while running:
        dt = clock.tick(60) / 1000.0
        
        keys = pygame.key.get_pressed()
        dx = dy = 0
        if keys[pygame.K_w] or keys[pygame.K_UP]: dy = -1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]: dy = 1
        if keys[pygame.K_a] or keys[pygame.K_LEFT]: dx = -1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]: dx = 1
        
        if dx != 0 or dy != 0:
            client.send_move(dx, dy)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    client.send_mine()
                elif event.key == pygame.K_b:
                    if client.world_state:
                        player_data = client.world_state["entities"].get(client.player_id)
                        if player_data:
                            client.send_build(
                                "turret_mg",
                                player_data["x"] + 50,
                                player_data["y"],
                                "machinegun_turret"
                            )
                elif event.key == pygame.K_TAB:
                    if client.can_switch_roles:
                        roles = ["engineer", "mechanic", "defender"]
                        if client.world_state:
                            player_data = client.world_state["entities"].get(client.player_id)
                            if player_data:
                                current_role = player_data.get("role", "engineer")
                                next_idx = (roles.index(current_role) + 1) % len(roles)
                                client.send_switch_role(roles[next_idx])
                elif event.key == pygame.K_ESCAPE:
                    running = False
        
        renderer.render(dt)
        pygame.display.flip()
    
    client.disconnect()
    pygame.quit()

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Frontier: Salvage Client")
    parser.add_argument("--name", default="Игрок", help="Имя игрока")
    parser.add_argument("--role", default="engineer", choices=["engineer", "mechanic", "defender"])
    parser.add_argument("--connect", default=None, help="IP сервера")
    parser.add_argument("--port", type=int, default=7777, help="Порт сервера")
    args = parser.parse_args()
    
    run_client(args.name, args.role, args.connect, args.port)

if __name__ == "__main__":
    main()