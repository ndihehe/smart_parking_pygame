import pygame

from ui.colors import BACKGROUND_COLOR


class Renderer:
    def __init__(self, screen: pygame.Surface) -> None:
        self.screen = screen

    def draw(self, state) -> None:
        self.screen.fill(BACKGROUND_COLOR)
        self.draw_map(state)
        self.draw_vehicles(state)
        self.draw_overlay(state)
        pygame.display.flip()

    def draw_map(self, state) -> None:
        pass

    def draw_vehicles(self, state) -> None:
        pass

    def draw_overlay(self, state) -> None:
        pass

