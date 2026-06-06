import pygame


class Renderer:
    def __init__(self, screen: pygame.Surface) -> None:
        self.screen = screen

    def render(self, simulation) -> None:
        self.screen.fill((30, 30, 30))
        self.draw_map(simulation)
        self.draw_vehicles(simulation)
        self.draw_hud(simulation)
        pygame.display.flip()

    def draw_map(self, simulation) -> None:
        pass

    def draw_vehicles(self, simulation) -> None:
        pass

    def draw_hud(self, simulation) -> None:
        pass

