import pygame

from config import FPS, WINDOW_TITLE
from core.game_controller import GameController
from ui.input_handler import InputHandler
from ui.renderer import Renderer
from ui.ui_layout import WINDOW_HEIGHT, WINDOW_WIDTH


class PygameApp:
    def __init__(self, map_filepath: str) -> None:
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption(WINDOW_TITLE)
        self.clock = pygame.time.Clock()
        self.gc = GameController(map_filepath)
        self.renderer = Renderer(self.screen)
        self.input_handler = InputHandler(self.gc)
        self.running = True

    def run(self) -> None:
        while self.running:
            delta_time = self.clock.tick(FPS) / 1000.0
            events = pygame.event.get()
            self.running = self.input_handler.handle_events(events)
            self.gc.update(delta_time)
            self.screen.fill((0, 0, 0))
            self.renderer.render(
                self.gc.map_manager.get_state(),
                self.gc.vehicle_manager.get_all_vehicles(),
            )
            pygame.display.flip()
        pygame.quit()
