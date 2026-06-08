import pygame

from config import FPS, WINDOW_TITLE
from core.game_controller import GameController
from ui.input_handler import InputHandler
from ui.main_menu import ACTION_EXIT, ACTION_PLAY, MainMenu
from ui.renderer import Renderer
from ui.ui_layout import (
    MIN_WINDOW_HEIGHT,
    MIN_WINDOW_WIDTH,
    WINDOW_HEIGHT,
    WINDOW_WIDTH,
)


class PygameApp:
    def __init__(self, map_filepath: str) -> None:
        pygame.init()
        display_info = pygame.display.Info()
        initial_size = (
            max(display_info.current_w, WINDOW_WIDTH),
            max(display_info.current_h, WINDOW_HEIGHT),
        )
        self.screen = pygame.display.set_mode(initial_size, pygame.RESIZABLE)
        pygame.display.set_caption(WINDOW_TITLE)
        if hasattr(pygame.display, "set_allow_screensaver"):
            pygame.display.set_allow_screensaver(True)
        self.clock = pygame.time.Clock()
        self.gc = GameController(map_filepath)
        self.renderer = Renderer(self.screen)
        self.input_handler = InputHandler(self.gc)
        self.main_menu = MainMenu()
        self.scene = "MENU"
        self.running = True
        self.fullscreen = False

    def run(self) -> None:
        while self.running:
            delta_time = self.clock.tick(FPS) / 1000.0
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.VIDEORESIZE:
                    width = max(event.w, MIN_WINDOW_WIDTH)
                    height = max(event.h, MIN_WINDOW_HEIGHT)
                    self.screen = pygame.display.set_mode((width, height), pygame.RESIZABLE)
                    self.renderer.screen = self.screen
                if event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
                    self.fullscreen = not self.fullscreen
                    if self.fullscreen:
                        self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
                    else:
                        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.RESIZABLE)
                    self.renderer.screen = self.screen

            if self.scene == "MENU":
                action = self.main_menu.handle_events(events, self.screen.get_size())
                if action == ACTION_PLAY:
                    self.scene = "GAME"
                elif action == ACTION_EXIT:
                    self.running = False
                self.main_menu.update(delta_time, self.screen.get_size())
                self.main_menu.render(self.screen)
            else:
                self.running = self.input_handler.handle_events(events)
                if self.input_handler.request_main_menu:
                    self.input_handler.request_main_menu = False
                    self.scene = "MENU"
                    continue
                self.gc.update(delta_time)
                self.screen.fill((0, 0, 0))
                self.renderer.render(
                    self.gc.map_manager.get_state(),
                    self.gc.vehicle_manager.get_all_vehicles(),
                    self.input_handler.get_selected_id(),
                    self.gc.guards,
                    self.gc.current_algorithm,
                    self.gc.simulation_status,
                    self.gc.placement_vehicle_type,
                    self.gc.placement_plan,
                    self.gc.active_scenario,
                    self.gc.simulation_speed,
                    self.gc.step_mode_enabled,
                )
            pygame.display.flip()
        pygame.quit()
