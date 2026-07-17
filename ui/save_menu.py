"""
Меню сохранения
"""
import pygame
import time
from datetime import datetime
from typing import Optional, List, Dict, Callable

class SaveMenu:
    """Меню сохранения без паузы"""
    
    def __init__(self, screen, save_manager, loc_mn=None, font=None):
        self.screen = screen
        self.save_manager = save_manager
        self.loc_mn = loc_mn
        self.font = font or pygame.font.Font(None, 32)
        self.font_small = pygame.font.Font(None, 24)
        self.font_title = pygame.font.Font(None, 48)
        
        self.active = False
        self.mode = "save"
        self.save_name = ""
        self.error_message = ""
        self.error_timer = 0
        self.selected_index = 0
        
        self.window_width = 600
        self.window_height = 500
        self.window_x = (screen.get_width() - self.window_width) // 2
        self.window_y = (screen.get_height() - self.window_height) // 2
        
        self.input_rect = pygame.Rect(
            self.window_x + 50,
            self.window_y + 150,
            self.window_width - 100,
            50
        )
        self.input_active = True
        self.cursor_visible = True
        self.cursor_timer = 0
        
        self.saves_list = []
        self.scroll_offset = 0
        self.visible_saves = 8
        
        self.world_state_callback = None
        
        self._create_buttons()
    
    def _get_text(self, key):
        if self.loc_mn:
            return self.loc_mn._g(key)
        return key
    
    def _create_buttons(self):
        btn_width = 120
        btn_height = 40
        
        self.save_button = {
            "rect": pygame.Rect(
                self.window_x + 50,
                self.window_y + self.window_height - 80,
                btn_width, btn_height
            ),
            "text": self._get_text("TID_SAVE"),
            "color": (60, 180, 60),
            "hover_color": (80, 220, 80),
            "callback": self._do_save
        }
        
        self.load_button = {
            "rect": pygame.Rect(
                self.window_x + 50 + btn_width + 20,
                self.window_y + self.window_height - 80,
                btn_width, btn_height
            ),
            "text": self._get_text("TID_LOAD"),
            "color": (60, 120, 220),
            "hover_color": (80, 160, 255),
            "callback": self._do_load
        }
        
        self.delete_button = {
            "rect": pygame.Rect(
                self.window_x + 50 + (btn_width + 20) * 2,
                self.window_y + self.window_height - 80,
                btn_width, btn_height
            ),
            "text": self._get_text("TID_DELETE"),
            "color": (220, 60, 60),
            "hover_color": (255, 80, 80),
            "callback": self._do_delete
        }
        
        self.cancel_button = {
            "rect": pygame.Rect(
                self.window_x + self.window_width - btn_width - 50,
                self.window_y + self.window_height - 80,
                btn_width, btn_height
            ),
            "text": self._get_text("TID_CANCEL"),
            "color": (120, 120, 120),
            "hover_color": (160, 160, 160),
            "callback": self._do_cancel
        }
        
        self.refresh_button = {
            "rect": pygame.Rect(
                self.window_x + self.window_width - 50 - 40,
                self.window_y + 110,
                40, 40
            ),
            "text": "🔄",
            "color": (80, 80, 80),
            "hover_color": (120, 120, 120),
            "callback": self._refresh_saves
        }
    
    def open(self, mode: str = "save"):
        self.active = True
        self.mode = mode
        self.save_name = ""
        self.error_message = ""
        self.error_timer = 0
        self.selected_index = 0
        self.scroll_offset = 0
        self.input_active = True
        self._refresh_saves()
    
    def close(self):
        self.active = False
    
    def _refresh_saves(self):
        self.saves_list = self.save_manager.get_saves_list()
        self.saves_list.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
    
    def _do_save(self):
        if not self.save_name.strip():
            self.error_message = self._get_text("TID_ENTER_NAME")
            self.error_timer = time.time() + 2
            return
        
        for save in self.saves_list:
            if save.get("name") == self.save_name.strip():
                self.error_message = self._get_text("TID_SAVE_EXISTS").replace("{name}", self.save_name)
                self.error_timer = time.time() + 2
                return
        
        success = self.save_manager.save_game(
            self._get_world_state(),
            self.save_name.strip()
        )
        
        if success:
            self.error_message = self._get_text("TID_SAVE_SUCCESS").replace("{name}", self.save_name)
            self.error_timer = time.time() + 2
            self.save_name = ""
            self._refresh_saves()
        else:
            self.error_message = self._get_text("TID_SAVE_ERROR")
            self.error_timer = time.time() + 2
    
    def _do_load(self):
        if not self.saves_list:
            self.error_message = self._get_text("TID_NO_SAVES")
            self.error_timer = time.time() + 2
            return
        
        if self.selected_index >= len(self.saves_list):
            self.selected_index = 0
            return
        
        save_name = self.saves_list[self.selected_index].get("name")
        if not save_name:
            return
        
        success = self.save_manager.load_game(save_name)
        if success:
            self.error_message = self._get_text("TID_LOAD_SUCCESS").replace("{name}", save_name)
            self.error_timer = time.time() + 2
            self.close()
        else:
            self.error_message = self._get_text("TID_LOAD_ERROR")
            self.error_timer = time.time() + 2
    
    def _do_delete(self):
        if not self.saves_list:
            self.error_message = self._get_text("TID_NO_SAVES")
            self.error_timer = time.time() + 2
            return
        
        if self.selected_index >= len(self.saves_list):
            self.selected_index = 0
            return
        
        save_name = self.saves_list[self.selected_index].get("name")
        if not save_name:
            return
        
        success = self.save_manager.delete_save(save_name)
        if success:
            self.error_message = self._get_text("TID_DELETE_SUCCESS").replace("{name}", save_name)
            self.error_timer = time.time() + 2
            self._refresh_saves()
            if self.selected_index >= len(self.saves_list):
                self.selected_index = max(0, len(self.saves_list) - 1)
        else:
            self.error_message = self._get_text("TID_DELETE_ERROR")
            self.error_timer = time.time() + 2
    
    def _do_cancel(self):
        self.close()
    
    def _get_world_state(self):
        if self.world_state_callback:
            return self.world_state_callback()
        return {}
    
    def set_world_state_callback(self, callback: Callable):
        self.world_state_callback = callback
    
    def update(self, events):
        if not self.active:
            return
        
        current_time = time.time()
        
        self.cursor_timer += 1
        if self.cursor_timer > 30:
            self.cursor_timer = 0
            self.cursor_visible = not self.cursor_visible
        
        if self.error_timer and current_time > self.error_timer:
            self.error_message = ""
            self.error_timer = 0
        
        mouse_pos = pygame.mouse.get_pos()
        
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.close()
                    return
                
                if self.input_active:
                    if event.key == pygame.K_BACKSPACE:
                        self.save_name = self.save_name[:-1]
                    elif event.key == pygame.K_RETURN:
                        if self.mode == "save":
                            self._do_save()
                        else:
                            self._do_load()
                    else:
                        if event.unicode and event.unicode.isprintable():
                            if len(self.save_name) < 50:
                                self.save_name += event.unicode
                
                if event.key == pygame.K_UP:
                    self.selected_index = max(0, self.selected_index - 1)
                elif event.key == pygame.K_DOWN:
                    self.selected_index = min(len(self.saves_list) - 1, self.selected_index + 1)
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    for btn in [self.save_button, self.load_button, 
                               self.delete_button, self.cancel_button, 
                               self.refresh_button]:
                        if btn["rect"].collidepoint(mouse_pos):
                            btn["callback"]()
                            return
                    
                    list_rect = pygame.Rect(
                        self.window_x + 50,
                        self.window_y + 210,
                        self.window_width - 100,
                        min(len(self.saves_list), self.visible_saves) * 40
                    )
                    if list_rect.collidepoint(mouse_pos):
                        index = (mouse_pos[1] - list_rect.y) // 40 + self.scroll_offset
                        if 0 <= index < len(self.saves_list):
                            self.selected_index = index
                            self.save_name = self.saves_list[index].get("name", "")
                    
                    if self.input_rect.collidepoint(mouse_pos):
                        self.input_active = True
                    else:
                        self.input_active = False
                
                elif event.button == 4:
                    self.scroll_offset = max(0, self.scroll_offset - 1)
                elif event.button == 5:
                    self.scroll_offset = min(
                        max(0, len(self.saves_list) - self.visible_saves),
                        self.scroll_offset + 1
                    )
    
    def draw(self, screen):
        if not self.active:
            return
        
        overlay = pygame.Surface(screen.get_size())
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        screen.blit(overlay, (0, 0))
        
        pygame.draw.rect(screen, (40, 40, 50), 
                        (self.window_x, self.window_y, self.window_width, self.window_height),
                        border_radius=10)
        pygame.draw.rect(screen, (100, 100, 120),
                        (self.window_x, self.window_y, self.window_width, self.window_height),
                        2, border_radius=10)
        
        title = self._get_text("TID_SAVE") if self.mode == "save" else self._get_text("TID_LOAD")
        title_text = self.font_title.render(title, True, (255, 255, 255))
        title_rect = title_text.get_rect(center=(self.window_x + self.window_width//2, 
                                                self.window_y + 40))
        screen.blit(title_text, title_rect)
        
        pygame.draw.line(screen, (80, 80, 100),
                        (self.window_x + 30, self.window_y + 70),
                        (self.window_x + self.window_width - 30, self.window_y + 70), 2)
        
        if self.mode == "save":
            label = self.font.render(self._get_text("TID_SAVE_NAME"), True, (200, 200, 200))
            screen.blit(label, (self.window_x + 50, self.window_y + 120))
            
            input_color = (80, 80, 100) if self.input_active else (60, 60, 80)
            pygame.draw.rect(screen, input_color, self.input_rect, border_radius=5)
            pygame.draw.rect(screen, (120, 120, 140), self.input_rect, 2, border_radius=5)
            
            display_text = self.save_name
            if self.input_active and self.cursor_visible:
                display_text += "|"
            if not display_text:
                display_text = self._get_text("TID_ENTER_SAVE_NAME")
                text_color = (150, 150, 150)
            else:
                text_color = (255, 255, 255)
            
            text_surf = self.font.render(display_text, True, text_color)
            screen.blit(text_surf, (self.input_rect.x + 10, 
                                   self.input_rect.y + (self.input_rect.height - text_surf.get_height()) // 2))
        
        list_label = self.font.render(self._get_text("TID_SAVES_LIST"), True, (200, 200, 200))
        screen.blit(list_label, (self.window_x + 50, self.window_y + 210))
        
        refresh_btn = self.refresh_button
        btn_color = refresh_btn["hover_color"] if refresh_btn["rect"].collidepoint(pygame.mouse.get_pos()) \
                    else refresh_btn["color"]
        pygame.draw.rect(screen, btn_color, refresh_btn["rect"], border_radius=5)
        refresh_text = self.font_small.render(refresh_btn["text"], True, (255, 255, 255))
        screen.blit(refresh_text, refresh_btn["rect"].center - 
                   pygame.Vector2(refresh_text.get_width()//2, refresh_text.get_height()//2))
        
        list_rect = pygame.Rect(
            self.window_x + 50,
            self.window_y + 245,
            self.window_width - 100,
            min(len(self.saves_list), self.visible_saves) * 40
        )
        
        pygame.draw.rect(screen, (30, 30, 40), list_rect, border_radius=5)
        pygame.draw.rect(screen, (60, 60, 80), list_rect, 1, border_radius=5)
        
        if not self.saves_list:
            empty_text = self.font.render(self._get_text("TID_NO_SAVES"), True, (150, 150, 150))
            screen.blit(empty_text, (list_rect.x + list_rect.width//2 - empty_text.get_width()//2,
                                     list_rect.y + list_rect.height//2 - empty_text.get_height()//2))
        else:
            start_idx = self.scroll_offset
            end_idx = min(start_idx + self.visible_saves, len(self.saves_list))
            
            for i in range(start_idx, end_idx):
                save = self.saves_list[i]
                item_rect = pygame.Rect(
                    list_rect.x + 5,
                    list_rect.y + (i - start_idx) * 40,
                    list_rect.width - 10,
                    38
                )
                
                if i == self.selected_index:
                    pygame.draw.rect(screen, (60, 100, 180), item_rect, border_radius=3)
                
                name_text = self.font_small.render(
                    save.get("name", "Без имени"),
                    True, (255, 255, 255) if i == self.selected_index else (200, 200, 200)
                )
                screen.blit(name_text, (item_rect.x + 10, item_rect.y + 8))
                
                date_str = save.get("datetime", "")
                if date_str:
                    date_text = self.font_small.render(date_str, True, (150, 150, 150))
                    screen.blit(date_text, (item_rect.right - date_text.get_width() - 10, item_rect.y + 8))
        
        for btn in [self.save_button, self.load_button, self.delete_button, self.cancel_button]:
            if btn["rect"].collidepoint(pygame.mouse.get_pos()):
                color = btn["hover_color"]
            else:
                color = btn["color"]
            
            pygame.draw.rect(screen, color, btn["rect"], border_radius=5)
            btn_text = self.font.render(btn["text"], True, (255, 255, 255))
            screen.blit(btn_text, btn["rect"].center - 
                       pygame.Vector2(btn_text.get_width()//2, btn_text.get_height()//2))
        
        if self.error_message:
            color = (255, 100, 100) if "error" in self.error_message.lower() or "ошибк" in self.error_message.lower() \
                    else (100, 255, 100)
            error_text = self.font.render(self.error_message, True, color)
            screen.blit(error_text, (self.window_x + 50, self.window_y + self.window_height - 120))