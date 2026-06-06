import pygame

from src.smart_parking.config import FPS, WINDOW_HEIGHT, WINDOW_WIDTH
from src.smart_parking.core.simulation import Simulation
from src.smart_parking.ui.input_handler import InputHandler
from src.smart_parking.ui.renderer import Renderer


class PygameApp:
    def __init__(self) -> None:
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.clock = pygame.time.Clock()
        self.running = True
        self.simulation = Simulation()
        self.input_handler = InputHandler()
        self.renderer = Renderer(self.screen)

    def run(self) -> None:
        while self.running:
            delta_time = self.clock.tick(FPS) / 1000
            self.handle_events()
            self.simulation.update(delta_time)
            self.renderer.render(self.simulation)
        pygame.quit()

    def handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            else:
                self.input_handler.handle_event(event, self.simulation)

