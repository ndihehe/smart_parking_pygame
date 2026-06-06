import pygame

from config import FPS, WINDOW_HEIGHT, WINDOW_WIDTH
from core.game_controller import GameController
from ui.input_handler import InputHandler
from ui.renderer import Renderer


class PygameApp:
    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption("Smart Parking Pygame")
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.clock = pygame.time.Clock()
        self.game_controller = GameController()
        self.renderer = Renderer(self.screen)
        self.input_handler = InputHandler()
        self.running = True

    def run(self) -> None:
        while self.running:
            delta_time = self.clock.tick(FPS) / 1000.0
            self.handle_events()
            self.game_controller.update(delta_time)
            self.renderer.draw(self.game_controller.state)
        pygame.quit()

    def handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            else:
                self.input_handler.handle(event, self.game_controller)

