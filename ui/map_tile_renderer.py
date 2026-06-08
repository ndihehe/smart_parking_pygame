import pygame

from config import CELL_SIZE
from models.enums import CellType
from ui.colors import GRID_LINE, TEXT_COLOR


class MapTileRenderer:
    def __init__(
        self,
        font_small: pygame.font.Font,
        sprites: dict[str, pygame.Surface],
    ) -> None:
        self.font_small = font_small
        self.sprites = sprites

    def draw_tile(
        self,
        surface: pygame.Surface,
        rect: pygame.Rect,
        cell_type: CellType,
        position: tuple[int, int],
    ) -> None:
        if cell_type == CellType.ROAD:
            self._draw_road(surface, rect)
        elif cell_type == CellType.INTERSECTION:
            self._draw_intersection(surface, rect)
        elif cell_type == CellType.CAR_SLOT:
            self._draw_parking_slot(surface, rect, "P-C", (66, 128, 178))
        elif cell_type == CellType.MOTO_SLOT:
            self._draw_parking_slot(surface, rect, "P-M", (136, 92, 178))
        elif cell_type == CellType.PARKING_SLOT:
            self._draw_parking_slot(surface, rect, "P", (92, 156, 108))
        elif cell_type == CellType.GATE:
            self._draw_gate(surface, rect)
        elif cell_type == CellType.OBSTACLE:
            self._draw_obstacle(surface, rect, position)
        else:
            self._draw_floor(surface, rect)

        pygame.draw.rect(surface, GRID_LINE, rect, 1)

    def _draw_floor(self, surface: pygame.Surface, rect: pygame.Rect) -> None:
        pygame.draw.rect(surface, (220, 224, 218), rect)
        pygame.draw.rect(surface, (236, 239, 232), rect.inflate(-4, -4))

    def _draw_road(self, surface: pygame.Surface, rect: pygame.Rect) -> None:
        pygame.draw.rect(surface, (106, 111, 116), rect)
        pygame.draw.rect(surface, (126, 131, 136), rect.inflate(-3, -3))
        pygame.draw.line(
            surface,
            (160, 164, 168),
            (rect.left + 3, rect.top + 5),
            (rect.right - 4, rect.top + 5),
            1,
        )
        pygame.draw.line(
            surface,
            (74, 78, 82),
            (rect.left + 2, rect.bottom - 3),
            (rect.right - 3, rect.bottom - 3),
            2,
        )

    def _draw_intersection(self, surface: pygame.Surface, rect: pygame.Rect) -> None:
        self._draw_road(surface, rect)
        pygame.draw.rect(surface, (172, 142, 48), rect.inflate(-8, -8), 2)
        pygame.draw.line(
            surface,
            (236, 205, 88),
            rect.midleft,
            rect.midright,
            2,
        )
        pygame.draw.line(
            surface,
            (236, 205, 88),
            rect.midtop,
            rect.midbottom,
            2,
        )

    def _draw_parking_slot(
        self,
        surface: pygame.Surface,
        rect: pygame.Rect,
        label: str,
        accent: tuple[int, int, int],
    ) -> None:
        pygame.draw.rect(surface, (92, 96, 100), rect)
        inner = rect.inflate(-5, -5)
        pygame.draw.rect(surface, (188, 196, 204), inner)
        pygame.draw.rect(surface, accent, inner, 2)
        pygame.draw.line(surface, (245, 245, 245), inner.topleft, inner.topright, 2)
        pygame.draw.line(surface, (245, 245, 245), inner.bottomleft, inner.bottomright, 2)
        text = self.font_small.render(label, True, (30, 35, 40))
        surface.blit(text, text.get_rect(center=rect.center))

    def _draw_gate(self, surface: pygame.Surface, rect: pygame.Rect) -> None:
        self._draw_road(surface, rect)
        gate_sprite = self.sprites.get("gate")
        if gate_sprite is not None:
            surface.blit(gate_sprite, gate_sprite.get_rect(center=rect.center))
            return
        text = self.font_small.render("G", True, TEXT_COLOR)
        surface.blit(text, text.get_rect(center=rect.center))

    def _draw_obstacle(
        self,
        surface: pygame.Surface,
        rect: pygame.Rect,
        position: tuple[int, int],
    ) -> None:
        pygame.draw.rect(surface, (90, 104, 82), rect)
        pygame.draw.rect(surface, (116, 132, 94), rect.inflate(-4, -4))
        variant = (position[0] * 7 + position[1] * 13) % 5
        if variant == 0:
            self._draw_asset(surface, rect, "barrier")
        elif variant == 1:
            self._draw_asset(surface, rect, "sign_red")
        elif variant == 2:
            self._draw_asset(surface, rect, "light")
        elif variant == 3:
            self._draw_planter(surface, rect)
        else:
            self._draw_trash_bin(surface, rect)

    def _draw_asset(
        self,
        surface: pygame.Surface,
        rect: pygame.Rect,
        key: str,
    ) -> None:
        sprite = self.sprites.get(key)
        if sprite is None:
            self._draw_trash_bin(surface, rect)
            return
        shadow = pygame.Rect(0, 0, min(CELL_SIZE - 8, sprite.get_width()), 5)
        shadow.center = (rect.centerx, rect.bottom - 7)
        pygame.draw.ellipse(surface, (54, 62, 50), shadow)
        surface.blit(sprite, sprite.get_rect(center=rect.center))

    def _draw_planter(self, surface: pygame.Surface, rect: pygame.Rect) -> None:
        pot = pygame.Rect(rect.left + 9, rect.bottom - 12, CELL_SIZE - 18, 8)
        pygame.draw.ellipse(surface, (54, 62, 50), pot.move(0, 4))
        pygame.draw.rect(surface, (134, 82, 46), pot, border_radius=3)
        pygame.draw.rect(surface, (172, 104, 56), pot.inflate(-3, -3), border_radius=2)
        for offset, color in ((-6, (58, 138, 76)), (0, (72, 166, 86)), (6, (46, 116, 66))):
            pygame.draw.circle(
                surface,
                color,
                (rect.centerx + offset, rect.centery - 4),
                7,
            )

    def _draw_trash_bin(self, surface: pygame.Surface, rect: pygame.Rect) -> None:
        body = pygame.Rect(rect.left + 10, rect.top + 8, CELL_SIZE - 20, CELL_SIZE - 13)
        pygame.draw.ellipse(surface, (54, 62, 50), body.move(0, 9))
        pygame.draw.rect(surface, (54, 104, 112), body, border_radius=3)
        pygame.draw.rect(surface, (78, 138, 146), body.inflate(-4, -4), border_radius=2)
        pygame.draw.rect(surface, (36, 74, 82), (body.left - 1, body.top - 3, body.width + 2, 4))
