from pathlib import Path

import pygame

from config import CELL_SIZE
from models.enums import CellType
from models.map_state import MapState
from ui.colors import GRID_LINE, TEXT_COLOR


class MapTileRenderer:
    def __init__(
        self,
        font_small: pygame.font.Font,
        sprites: dict[str, pygame.Surface],
    ) -> None:
        self.font_small = font_small
        self.sprites = sprites
        self.tile_root = Path(__file__).resolve().parent.parent / "assets" / "maps" / "tiles"
        self.tile_surfaces: dict[str, pygame.Surface] = {}
        self.scaled_tile_cache: dict[tuple[str, int], pygame.Surface] = {}
        self.lamp_surface = self._load_lamp_surface()
        self._load_tile_assets()

    def has_tile_assets(self) -> bool:
        return bool(self.tile_surfaces)

    def _load_tile_assets(self) -> None:
        if not self.tile_root.exists():
            return
        for path in self.tile_root.glob("*.png"):
            self.tile_surfaces[path.stem] = pygame.image.load(str(path)).convert_alpha()

    def draw_tile(
        self,
        surface: pygame.Surface,
        rect: pygame.Rect,
        cell_type: CellType,
        position: tuple[int, int],
        map_state: MapState | None = None,
    ) -> None:
        if cell_type == CellType.LAMP:
            if not self._draw_tile_asset(surface, rect, "floor_empty"):
                self._draw_floor(surface, rect)
            self._draw_lamp(surface, rect)
            pygame.draw.rect(surface, GRID_LINE, rect, 1)
            return

        if self.tile_surfaces and map_state is not None:
            tile_name = self._tile_name_for(cell_type, position, map_state)
            if tile_name is not None and self._draw_tile_asset(surface, rect, tile_name):
                pygame.draw.rect(surface, GRID_LINE, rect, 1)
                return

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
        elif cell_type == CellType.TREE:
            self._draw_tree(surface, rect)
        elif cell_type == CellType.OBSTACLE:
            self._draw_obstacle(surface, rect, position)
        else:
            self._draw_floor(surface, rect)

        pygame.draw.rect(surface, GRID_LINE, rect, 1)

    def _load_lamp_surface(self) -> pygame.Surface | None:
        path = (
            Path(__file__).resolve().parent.parent
            / "assets"
            / "maps"
            / "street_lamp_tile.png"
        )
        if not path.exists():
            return None
        source = pygame.image.load(str(path)).convert_alpha()
        preview = pygame.transform.smoothscale(source, (256, 256))
        for row in range(preview.get_height()):
            for col in range(preview.get_width()):
                red, green, blue, alpha = preview.get_at((col, row))
                if (
                    alpha
                    and min(red, green, blue) > 205
                    and max(red, green, blue) - min(red, green, blue) < 12
                ):
                    preview.set_at((col, row), (red, green, blue, 0))
        bounds = preview.get_bounding_rect(min_alpha=16)
        if bounds.width == 0 or bounds.height == 0:
            return None
        return preview.subsurface(bounds).copy()

    def _draw_lamp(self, surface: pygame.Surface, rect: pygame.Rect) -> None:
        if self.lamp_surface is None:
            pygame.draw.circle(surface, (255, 204, 82), rect.center, 5)
            return
        scale = min(
            (rect.width - 4) / self.lamp_surface.get_width(),
            (rect.height - 4) / self.lamp_surface.get_height(),
        )
        size = (
            max(1, int(self.lamp_surface.get_width() * scale)),
            max(1, int(self.lamp_surface.get_height() * scale)),
        )
        lamp = pygame.transform.smoothscale(self.lamp_surface, size)
        surface.blit(lamp, lamp.get_rect(center=rect.center))

    def _draw_tile_asset(
        self,
        surface: pygame.Surface,
        rect: pygame.Rect,
        tile_name: str,
    ) -> bool:
        tile = self.tile_surfaces.get(tile_name)
        if tile is None:
            return False
        cache_key = (tile_name, rect.width)
        scaled = self.scaled_tile_cache.get(cache_key)
        if scaled is None:
            scaled = pygame.transform.smoothscale(tile, rect.size)
            self.scaled_tile_cache[cache_key] = scaled
        surface.blit(scaled, rect)
        return True

    def _tile_name_for(
        self,
        cell_type: CellType,
        position: tuple[int, int],
        map_state: MapState,
    ) -> str | None:
        if cell_type == CellType.ROAD:
            return self._road_tile_name(position, map_state)
        if cell_type == CellType.INTERSECTION:
            return self._road_tile_name(position, map_state, force_intersection=True)
        if cell_type == CellType.CAR_SLOT:
            return "car_parking_slot"
        if cell_type == CellType.MOTO_SLOT:
            return self._motorbike_tile_name(position, map_state)
        if cell_type == CellType.PARKING_SLOT:
            return "car_parking_slot"
        if cell_type == CellType.GATE:
            return self._gate_tile_name(position, map_state)
        if cell_type == CellType.TREE:
            return None
        if cell_type in {CellType.OBSTACLE, CellType.BLOCKED}:
            return "obstacle_wall"
        return "floor_empty"

    def _road_tile_name(
        self,
        position: tuple[int, int],
        map_state: MapState,
        force_intersection: bool = False,
    ) -> str:
        directions = self._drive_directions(position, map_state)
        if force_intersection and len(directions) >= 4:
            return "road_intersection"
        if len(directions) >= 4:
            return "road_cross"
        if directions == {"west", "east"}:
            return "road_horizontal"
        if directions == {"north", "south"}:
            return "road_vertical"
        if directions == {"north", "east"}:
            return "road_turn_ne"
        if directions == {"north", "west"}:
            return "road_turn_nw"
        if directions == {"south", "east"}:
            return "road_turn_se"
        if directions == {"south", "west"}:
            return "road_turn_sw"
        if directions == {"west", "east", "north"}:
            return "road_t_north"
        if directions == {"west", "east", "south"}:
            return "road_t_south"
        if directions == {"north", "south", "east"}:
            return "road_t_east"
        if directions == {"north", "south", "west"}:
            return "road_t_west"
        return "road_plain"

    def _drive_directions(
        self,
        position: tuple[int, int],
        map_state: MapState,
    ) -> set[str]:
        row, col = position
        offsets = {
            "north": (-1, 0),
            "south": (1, 0),
            "west": (0, -1),
            "east": (0, 1),
        }
        drive_types = {CellType.ROAD, CellType.INTERSECTION, CellType.GATE}
        directions: set[str] = set()
        for direction, (row_delta, col_delta) in offsets.items():
            neighbor_row = row + row_delta
            neighbor_col = col + col_delta
            if not (0 <= neighbor_row < map_state.rows and 0 <= neighbor_col < map_state.cols):
                continue
            if map_state.grid[neighbor_row][neighbor_col] in drive_types:
                directions.add(direction)
        return directions

    def _motorbike_tile_name(
        self,
        position: tuple[int, int],
        map_state: MapState,
    ) -> str:
        inner = map_state.motorbike_outer_to_inner.get(position)
        if inner is not None:
            return self._motorbike_pair_tile_name(position, inner, is_outer_tile=True)

        outer = map_state.motorbike_inner_to_outer.get(position)
        if outer is not None:
            return self._motorbike_pair_tile_name(outer, position, is_outer_tile=False)

        return "motorbike_parking_single"

    def _motorbike_pair_tile_name(
        self,
        outer_position: tuple[int, int],
        inner: tuple[int, int],
        is_outer_tile: bool,
    ) -> str:
        if outer_position[0] == inner[0]:
            return (
                "motorbike_parking_outer_horizontal"
                if is_outer_tile
                else "motorbike_parking_inner_horizontal"
            )
        if outer_position[1] == inner[1]:
            return (
                "motorbike_parking_outer_vertical"
                if is_outer_tile
                else "motorbike_parking_inner_vertical"
            )
        return "motorbike_parking_single"

    def _gate_tile_name(
        self,
        position: tuple[int, int],
        map_state: MapState,
    ) -> str:
        on_left = position[1] < map_state.cols // 2
        if position in map_state.entry_gates:
            return "gate_entry_left" if on_left else "gate_entry_right"
        if position in map_state.exit_gates:
            return "gate_exit_left" if on_left else "gate_exit_right"
        return "gate_entry_left" if on_left else "gate_exit_right"

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

    def _draw_tree(self, surface: pygame.Surface, rect: pygame.Rect) -> None:
        self._draw_floor(surface, rect)
        trunk = pygame.Rect(0, 0, max(4, rect.width // 8), max(8, rect.height // 4))
        trunk.center = (rect.centerx, rect.centery + rect.height // 6)
        pygame.draw.rect(surface, (104, 68, 38), trunk, border_radius=2)
        for offset_x, offset_y, radius, color in [
            (-8, -5, 11, (62, 142, 70)),
            (0, -11, 13, (82, 170, 78)),
            (9, -4, 10, (48, 124, 64)),
            (0, 2, 11, (72, 156, 74)),
        ]:
            pygame.draw.circle(
                surface,
                color,
                (rect.centerx + offset_x, rect.centery + offset_y),
                radius,
            )

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
