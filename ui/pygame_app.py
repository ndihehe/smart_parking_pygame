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
        initial_size = self._fit_window_size(
            (WINDOW_WIDTH, WINDOW_HEIGHT),
            (display_info.current_w, display_info.current_h),
        )
        self.windowed_size = initial_size
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
                if event.type == pygame.VIDEORESIZE and not self.fullscreen:
                    self.windowed_size = event.size
                    self.screen = pygame.display.set_mode(event.size, pygame.RESIZABLE)
                    self.renderer.screen = self.screen
                if event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
                    self.fullscreen = not self.fullscreen
                    if self.fullscreen:
                        self.windowed_size = self.screen.get_size()
                        self.screen = pygame.display.set_mode(self._display_size(), pygame.FULLSCREEN)
                    else:
                        self.screen = pygame.display.set_mode(self.windowed_size, pygame.RESIZABLE)
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

    def _display_size(self) -> tuple[int, int]:
        display_info = pygame.display.Info()
        return display_info.current_w, display_info.current_h

    def _fit_window_size(
        self,
        requested_size: tuple[int, int],
        display_size: tuple[int, int],
    ) -> tuple[int, int]:
        display_width, display_height = display_size
        max_width = max(640, display_width - 80)
        max_height = max(480, display_height - 120)
        min_width = min(MIN_WINDOW_WIDTH, max_width)
        min_height = min(MIN_WINDOW_HEIGHT, max_height)
        width = min(max(requested_size[0], min_width), max_width)
        height = min(max(requested_size[1], min_height), max_height)
        return width, height
