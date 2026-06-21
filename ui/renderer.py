from pathlib import Path

import pygame

from core.simulation_state import SimulationStatus, VehiclePlan
from core.pathfinding_metrics import METRICS
from models.enums import VehicleStatus, VehicleType
from models.guard import Guard
from models.map_state import MapState
from models.vehicle import Vehicle
from ui.colors import (
    BLACK,
    BLOCKED,
    GRID_LINE,
    PATH_COLOR,
    TEXT_COLOR,
    WHITE,
    VEHICLE_MANUAL,
    VEHICLE_MOVING,
    VEHICLE_PARKED,
    VEHICLE_REROUTING,
    VEHICLE_VIOLATION,
    VEHICLE_WAITING,
)
from ui.hud_overlay import draw_hud
from ui.map_tile_renderer import MapTileRenderer
from ui.sprite_loader import SpriteLoader
from ui.view_transform import get_game_viewport_rect, get_map_view_rect, map_pixel_size


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MAP_ASSET_ROOT = PROJECT_ROOT / "assets" / "maps"
VEHICLE_OVERLAY_PATHS = {
    "parked": MAP_ASSET_ROOT / "vehicle_parked_frame_green.png",
    "violation": MAP_ASSET_ROOT / "vehicle_violation_frame_red.png",
    "selected": MAP_ASSET_ROOT / "vehicle_selected_frame_blue.png",
}


class Renderer:
    def __init__(self, screen: pygame.Surface) -> None:
        self.screen = screen
        self.font = pygame.font.SysFont("monospace", 12)
        self.font_small = pygame.font.SysFont("monospace", 9)
        self.font_bold = pygame.font.SysFont("monospace", 14, bold=True)
        self._map_surface: pygame.Surface | None = None
        self._map_cache_key: tuple[int, int, int] | None = None
        self._background_surface: pygame.Surface | None = None
        self._background_path: str | None = None
        self._sprites = SpriteLoader().load_entity_sprites()
        self._car_sprite_ids = self._directional_sprite_ids("car_topdown_")
        self._fallback_car_sprite_keys: list[str] = []
        self._motorbike_sprite_ids = self._directional_sprite_ids("motorbike_topdown_")
        self._fallback_motorbike_sprite_keys: list[str] = []
        self._map_tile_renderer = MapTileRenderer(self.font_small, self._sprites)
        self._world_surface: pygame.Surface | None = None
        self._scaled_sprite_cache: dict[tuple[int, int, int], pygame.Surface] = {}
        self._vehicle_overlay_sources = {
            name: self._load_vehicle_overlay(path)
            for name, path in VEHICLE_OVERLAY_PATHS.items()
        }
        self._vehicle_overlay_cache: dict[tuple[str, int], pygame.Surface] = {}
        self._night_light_cache: dict[int, tuple[pygame.Surface, pygame.Surface]] = {}
        self._headlight_cache: dict[
            tuple[int, str], tuple[pygame.Surface, pygame.Surface]
        ] = {}

    def draw_map(self, map_state: MapState) -> None:
        self._ensure_map_surface(map_state)
        if self._map_surface is not None:
            self.screen.blit(self._map_surface, (0, 0))

        for position in map_state.dynamic_blocks:
            x, y = self._cell_to_pixel(map_state, position)
            rect = pygame.Rect(x, y, map_state.tile_size, map_state.tile_size)
            pygame.draw.rect(self.screen, BLOCKED, rect)
            pygame.draw.rect(self.screen, GRID_LINE, rect, 1)
            text = self.font_small.render("B!", True, TEXT_COLOR)
            text_rect = text.get_rect(center=rect.center)
            self.screen.blit(text, text_rect)

    def _ensure_map_surface(self, map_state: MapState) -> None:
        cache_key = (id(map_state.grid), map_state.rows, map_state.cols)
        if self._map_surface is not None and self._map_cache_key == cache_key:
            return

        width = map_state.cols * map_state.tile_size
        height = map_state.rows * map_state.tile_size
        self._map_surface = pygame.Surface((width, height))
        self._map_cache_key = cache_key

        if (
            map_state.image_path
            and not self._map_tile_renderer.has_tile_assets()
            and self._background_exists(map_state.image_path)
        ):
            background = self._load_background(map_state)
            self._map_surface.blit(background, (0, 0))
            return

        for row_index, row in enumerate(map_state.grid):
            for col_index, cell_type in enumerate(row):
                position = (row_index, col_index)
                x, y = self._cell_to_pixel(map_state, position)
                rect = pygame.Rect(x, y, map_state.tile_size, map_state.tile_size)
                self._map_tile_renderer.draw_tile(
                    self._map_surface,
                    rect,
                    cell_type,
                    position,
                    map_state,
                )

    def _load_background(self, map_state: MapState) -> pygame.Surface:
        assert map_state.image_path is not None
        if (
            self._background_surface is not None
            and self._background_path == map_state.image_path
        ):
            return self._background_surface

        image_path = Path(map_state.image_path)
        if not image_path.is_absolute():
            image_path = Path.cwd() / image_path
        background = pygame.image.load(str(image_path)).convert()
        expected_size = (map_state.cols * map_state.tile_size, map_state.rows * map_state.tile_size)
        if background.get_size() != expected_size:
            background = pygame.transform.smoothscale(background, expected_size)
        self._background_surface = background
        self._background_path = map_state.image_path
        return background

    def _background_exists(self, image_path: str) -> bool:
        path = Path(image_path)
        if not path.is_absolute():
            path = Path.cwd() / path
        return path.exists()

    def _cell_to_pixel(
        self,
        map_state: MapState,
        position: tuple[int, int],
    ) -> tuple[int, int]:
        row, col = position
        return (
            map_state.grid_offset_x + col * map_state.tile_size,
            map_state.grid_offset_y + row * map_state.tile_size,
        )

    def _cell_center(
        self,
        map_state: MapState,
        position: tuple[int, int],
    ) -> tuple[int, int]:
        x, y = self._cell_to_pixel(map_state, position)
        return x + map_state.tile_size // 2, y + map_state.tile_size // 2

    def draw_vehicles(
        self,
        map_state: MapState,
        vehicles: list[Vehicle],
        selected_vehicle_id: int | None = None,
    ) -> None:
        status_colors = {
            VehicleStatus.MOVING: VEHICLE_MOVING,
            VehicleStatus.ARRIVED: VEHICLE_PARKED,
            VehicleStatus.PARKED: VEHICLE_PARKED,
            VehicleStatus.WAITING: VEHICLE_WAITING,
            VehicleStatus.MANUAL: VEHICLE_MANUAL,
            VehicleStatus.REROUTING: VEHICLE_REROUTING,
            VehicleStatus.VIOLATION: VEHICLE_VIOLATION,
        }

        for vehicle in vehicles:
            center = self._vehicle_render_center(map_state, vehicle)
            x = int(center[0] - map_state.tile_size / 2)
            y = int(center[1] - map_state.tile_size / 2)
            radius = max(6, map_state.tile_size // 2 - 9)
            color = status_colors[vehicle.status]
            sprite = self._get_vehicle_sprite(vehicle, map_state)
            self._draw_vehicle_overlay(
                center,
                map_state.tile_size,
                vehicle,
                selected_vehicle_id,
            )
            self._draw_vehicle_shadow(center, map_state.tile_size)
            if sprite is not None:
                scaled_sprite = self._scale_vehicle_sprite(
                    sprite,
                    vehicle.type,
                    map_state.tile_size,
                )
                sprite_rect = scaled_sprite.get_rect(center=center)
                self.screen.blit(scaled_sprite, sprite_rect)
                label_text = f"C{vehicle.id}" if vehicle.type.value == "CAR" else f"M{vehicle.id}"
            elif vehicle.type.value == "CAR":
                self._draw_car_icon(center, map_state.tile_size, color)
                label_text = f"C{vehicle.id}"
            else:
                pygame.draw.circle(self.screen, color, center, radius)
                pygame.draw.circle(self.screen, WHITE, center, radius, 2)
                pygame.draw.circle(self.screen, BLACK, center, max(2, radius // 3))
                label_text = f"M{vehicle.id}"

            self._draw_status_dot(
                (x + map_state.tile_size - 8, y + 8),
                color,
            )
            self._draw_vehicle_label(
                label_text,
                (center[0], y + map_state.tile_size - 8),
            )

    def _vehicle_render_center(
        self,
        map_state: MapState,
        vehicle: Vehicle,
    ) -> tuple[int, int]:
        end_x, end_y = self._cell_center(map_state, vehicle.position)
        if vehicle.render_from is None or vehicle.render_progress >= 1.0:
            return end_x, end_y
        start_x, start_y = self._cell_center(map_state, vehicle.render_from)
        progress = vehicle.render_progress
        return (
            int(start_x + (end_x - start_x) * progress),
            int(start_y + (end_y - start_y) * progress),
        )

    def _load_vehicle_overlay(self, path: Path) -> pygame.Surface | None:
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

    def _draw_vehicle_overlay(
        self,
        center: tuple[int, int],
        tile_size: int,
        vehicle: Vehicle,
        selected_vehicle_id: int | None,
    ) -> None:
        overlay_name: str | None = None
        if (
            vehicle.id == selected_vehicle_id
            and vehicle.status == VehicleStatus.MANUAL
        ):
            overlay_name = "selected"
        elif vehicle.status == VehicleStatus.VIOLATION:
            overlay_name = "violation"
        elif vehicle.status == VehicleStatus.PARKED:
            overlay_name = "parked"
        if overlay_name is None:
            return

        cache_key = (overlay_name, tile_size)
        overlay = self._vehicle_overlay_cache.get(cache_key)
        if overlay is None:
            source = self._vehicle_overlay_sources.get(overlay_name)
            if source is None:
                return
            overlay = self._build_glowing_overlay(source, tile_size)
            self._vehicle_overlay_cache[cache_key] = overlay
        self.screen.blit(overlay, overlay.get_rect(center=center))

    def _build_glowing_overlay(
        self,
        source: pygame.Surface,
        tile_size: int,
    ) -> pygame.Surface:
        crisp_size = tile_size + 8
        canvas_size = tile_size + 22
        canvas = pygame.Surface((canvas_size, canvas_size), pygame.SRCALPHA)
        for size, alpha in (
            (tile_size + 20, 38),
            (tile_size + 14, 72),
            (crisp_size, 255),
        ):
            layer = pygame.transform.smoothscale(source, (size, size))
            layer.set_alpha(alpha)
            canvas.blit(layer, layer.get_rect(center=canvas.get_rect().center))
        return canvas

    def _draw_vehicle_shadow(
        self,
        center: tuple[int, int],
        tile_size: int,
    ) -> None:
        shadow = pygame.Rect(0, 0, tile_size - 12, max(5, tile_size // 6))
        shadow.center = (center[0], center[1] + tile_size // 5)
        pygame.draw.ellipse(self.screen, (0, 0, 0, 95), shadow)

    def _draw_car_icon(
        self,
        center: tuple[int, int],
        tile_size: int,
        color: tuple[int, int, int],
    ) -> None:
        body = pygame.Rect(0, 0, tile_size - 8, tile_size - 14)
        body.center = center
        roof = pygame.Rect(0, 0, body.width - 12, max(8, body.height // 2))
        roof.center = (center[0], center[1] - 2)
        windshield = pygame.Rect(0, 0, roof.width - 8, max(4, roof.height // 2))
        windshield.center = (center[0], roof.top + roof.height // 2)

        pygame.draw.rect(self.screen, color, body, border_radius=5)
        pygame.draw.rect(self.screen, WHITE, body, 2, border_radius=5)
        pygame.draw.rect(self.screen, _darken(color, 36), roof, border_radius=4)
        pygame.draw.rect(self.screen, (166, 220, 238), windshield, border_radius=3)

        wheel_width = max(4, tile_size // 9)
        wheel_height = max(8, tile_size // 5)
        for wheel_x in (body.left - 1, body.right - wheel_width + 1):
            pygame.draw.rect(
                self.screen,
                (18, 20, 24),
                pygame.Rect(wheel_x, body.top + 5, wheel_width, wheel_height),
                border_radius=2,
            )
            pygame.draw.rect(
                self.screen,
                (18, 20, 24),
                pygame.Rect(wheel_x, body.bottom - wheel_height - 5, wheel_width, wheel_height),
                border_radius=2,
            )

        pygame.draw.circle(self.screen, (255, 238, 168), (body.right - 5, body.top + 5), 2)
        pygame.draw.circle(self.screen, (255, 238, 168), (body.right - 5, body.bottom - 5), 2)

    def _scale_vehicle_sprite(
        self,
        sprite: pygame.Surface,
        vehicle_type: VehicleType,
        tile_size: int,
    ) -> pygame.Surface:
        max_width = tile_size - (6 if vehicle_type == VehicleType.CAR else 12)
        max_height = tile_size - (8 if vehicle_type == VehicleType.CAR else 14)
        cache_key = (id(sprite), max_width, max_height)
        cached = self._scaled_sprite_cache.get(cache_key)
        if cached is not None:
            return cached

        width, height = sprite.get_size()
        scale = min(max_width / width, max_height / height)
        scaled_size = (
            max(1, int(width * scale)),
            max(1, int(height * scale)),
        )
        scaled = pygame.transform.smoothscale(sprite, scaled_size)
        self._scaled_sprite_cache[cache_key] = scaled
        return scaled

    def _draw_status_dot(
        self,
        center: tuple[int, int],
        color: tuple[int, int, int],
    ) -> None:
        pygame.draw.circle(self.screen, BLACK, center, 6)
        pygame.draw.circle(self.screen, color, center, 4)

    def _draw_vehicle_label(
        self,
        text: str,
        center: tuple[int, int],
    ) -> None:
        label = self.font_bold.render(text, True, WHITE)
        label_rect = label.get_rect(center=center)
        bg_rect = label_rect.inflate(8, 4)
        pygame.draw.rect(self.screen, (15, 18, 24), bg_rect, border_radius=4)
        pygame.draw.rect(self.screen, (235, 240, 225), bg_rect, 1, border_radius=4)
        self.screen.blit(label, label_rect)

    def _get_vehicle_sprite(
        self,
        vehicle: Vehicle,
        map_state: MapState,
    ) -> pygame.Surface | None:
        if vehicle.type.value == "CAR":
            return self._get_car_sprite(vehicle, map_state)
        return self._get_motorbike_sprite(vehicle, map_state)

    def _get_motorbike_sprite(
        self,
        vehicle: Vehicle,
        map_state: MapState,
    ) -> pygame.Surface | None:
        sprite_options = (
            [("directional", sprite_id) for sprite_id in self._motorbike_sprite_ids]
            + [("oriented", sprite_key) for sprite_key in self._fallback_motorbike_sprite_keys]
        )
        if not sprite_options:
            return None

        sprite_type, sprite_id = sprite_options[vehicle.id % len(sprite_options)]
        if sprite_type == "directional":
            for direction in self._direction_fallbacks(
                self._vehicle_direction_name(vehicle, map_state)
            ):
                sprite = self._sprites.get(f"{sprite_id}_{direction}")
                if sprite is not None:
                    return sprite

        sprite = self._sprites.get(sprite_id)
        if sprite is None:
            return None
        return self._orient_vehicle_sprite(sprite, vehicle, map_state)

    def _get_car_sprite(
        self,
        vehicle: Vehicle,
        map_state: MapState,
    ) -> pygame.Surface | None:
        if self._car_sprite_ids:
            sprite_id = self._car_sprite_ids[vehicle.id % len(self._car_sprite_ids)]
            for direction in self._direction_fallbacks(
                self._vehicle_direction_name(vehicle, map_state)
            ):
                sprite = self._sprites.get(f"{sprite_id}_{direction}")
                if sprite is not None:
                    return sprite

        if not self._fallback_car_sprite_keys:
            return None
        sprite_key = self._fallback_car_sprite_keys[
            vehicle.id % len(self._fallback_car_sprite_keys)
        ]
        sprite = self._sprites.get(sprite_key)
        if sprite is None:
            return None
        return self._orient_vehicle_sprite(sprite, vehicle, map_state)

    def _directional_sprite_ids(self, prefix: str) -> list[str]:
        suffix = "_east"
        return sorted(
            {
                key[: -len(suffix)]
                for key in self._sprites
                if key.startswith(prefix) and key.endswith(suffix)
            }
        )

    def _sprite_keys_with_fallback(
        self,
        prefixes: list[str],
        fallback_keys: list[str],
    ) -> list[str]:
        keys = sorted(
            key
            for key in self._sprites
            if prefixes and any(key.startswith(prefix) for prefix in prefixes)
        )
        if keys:
            return keys
        return [key for key in fallback_keys if key in self._sprites]

    def _existing_sprite_keys(self, keys: list[str]) -> list[str]:
        return [key for key in keys if key in self._sprites]

    def _vehicle_direction_name(self, vehicle: Vehicle, map_state: MapState) -> str:
        if vehicle.status == VehicleStatus.MANUAL:
            return vehicle.heading
        if not vehicle.path:
            parked_direction = self._parked_vehicle_direction_name(vehicle, map_state)
            return parked_direction if parked_direction is not None else "east"

        first_delta = self._movement_delta(vehicle.position, vehicle.path[0])
        if len(vehicle.path) > 1:
            second_delta = self._movement_delta(vehicle.path[0], vehicle.path[1])
            if first_delta != second_delta:
                turn_delta = (
                    first_delta[0] + second_delta[0],
                    first_delta[1] + second_delta[1],
                )
                direction = self._delta_direction_name(turn_delta)
                if direction is not None:
                    return direction

        direction = self._delta_direction_name(first_delta)
        return direction if direction is not None else "east"

    def _parked_vehicle_direction_name(
        self,
        vehicle: Vehicle,
        map_state: MapState,
    ) -> str | None:
        if vehicle.status not in {VehicleStatus.ARRIVED, VehicleStatus.PARKED}:
            return None
        if vehicle.position not in map_state.parking_slots:
            return None
        if vehicle.type == VehicleType.CAR:
            return "north"

        inner_to_outer = (
            map_state.car_inner_to_outer
            if vehicle.type == VehicleType.CAR
            else map_state.motorbike_inner_to_outer
        )
        outer_to_inner = (
            map_state.car_outer_to_inner
            if vehicle.type == VehicleType.CAR
            else map_state.motorbike_outer_to_inner
        )
        outer = inner_to_outer.get(vehicle.position)
        if outer is not None:
            return self._delta_direction_name(
                self._movement_delta(vehicle.position, outer)
            )
        inner = outer_to_inner.get(vehicle.position)
        if inner is not None:
            return self._delta_direction_name(
                self._movement_delta(inner, vehicle.position)
            )

        row, col = vehicle.position
        drive_types = {"G", "R", "I"}
        candidates = [
            ((row + 1, col), "north"),
            ((row - 1, col), "south"),
            ((row, col + 1), "west"),
            ((row, col - 1), "east"),
        ]
        for (neighbor_row, neighbor_col), direction in candidates:
            if not (0 <= neighbor_row < map_state.rows and 0 <= neighbor_col < map_state.cols):
                continue
            if map_state.grid[neighbor_row][neighbor_col].value in drive_types:
                return direction
        return None

    def _movement_delta(
        self,
        start: tuple[int, int],
        end: tuple[int, int],
    ) -> tuple[int, int]:
        return end[0] - start[0], end[1] - start[1]

    def _delta_direction_name(self, delta: tuple[int, int]) -> str | None:
        row_delta, col_delta = delta
        vertical = "north" if row_delta < 0 else "south" if row_delta > 0 else ""
        horizontal = "west" if col_delta < 0 else "east" if col_delta > 0 else ""
        if vertical and horizontal:
            return f"{vertical}{horizontal}"
        if vertical:
            return vertical
        if horizontal:
            return horizontal
        return None

    def _direction_fallbacks(self, direction: str) -> list[str]:
        fallback_map = {
            "northeast": ["northeast", "north", "east"],
            "northwest": ["northwest", "north", "west"],
            "southeast": ["southeast", "south", "east"],
            "southwest": ["southwest", "south", "west"],
        }
        return fallback_map.get(direction, [direction, "east"])

    def _orient_vehicle_sprite(
        self,
        sprite: pygame.Surface,
        vehicle: Vehicle,
        map_state: MapState,
    ) -> pygame.Surface:
        direction = self._vehicle_direction_name(vehicle, map_state)
        if direction == "west":
            return pygame.transform.flip(sprite, True, False)
        if direction in {"north", "northeast", "northwest"}:
            return pygame.transform.rotate(sprite, 90)
        if direction in {"south", "southeast", "southwest"}:
            return pygame.transform.rotate(sprite, -90)
        return sprite

    def draw_paths(self, map_state: MapState, vehicles: list[Vehicle]) -> None:
        for vehicle in vehicles:
            if vehicle.status in (VehicleStatus.MOVING, VehicleStatus.REROUTING) and vehicle.path:
                for position in vehicle.path:
                    center = self._cell_center(map_state, position)
                    pygame.draw.circle(self.screen, PATH_COLOR, center, 4)

    def draw_guards(self, map_state: MapState, guards: list[Guard] | None) -> None:
        if not guards:
            return
        for guard in guards:
            x, y = self._cell_to_pixel(map_state, guard.position)
            center = self._cell_center(map_state, guard.position)
            sprite = self._get_guard_sprite(guard)
            if sprite is not None:
                sprite_rect = sprite.get_rect(center=center)
                self.screen.blit(sprite, sprite_rect)
            else:
                rect = pygame.Rect(x + 4, y + 4, map_state.tile_size - 8, map_state.tile_size - 8)
                pygame.draw.rect(self.screen, WHITE, rect, border_radius=3)
                pygame.draw.rect(self.screen, GRID_LINE, rect, 2)
            label = self.font_small.render(f"S{guard.id}", True, GRID_LINE)
            self.screen.blit(label, label.get_rect(center=(center[0], y + map_state.tile_size - 5)))

    def _get_guard_sprite(self, guard: Guard) -> pygame.Surface | None:
        if guard.path or guard.is_walking:
            frames = [
                self._sprites.get("guard"),
                self._sprites.get("guard_walk"),
                self._sprites.get("guard_walk2"),
                self._sprites.get("guard_walk"),
            ]
            frames = [frame for frame in frames if frame is not None]
            if not frames:
                return None
            frame_index = (pygame.time.get_ticks() // 180 + guard.id) % len(frames)
            sprite = frames[frame_index]
        else:
            sprite = self._sprites.get("guard")

        if sprite is None:
            return None
        return self._orient_guard_sprite(sprite, guard)

    def _orient_guard_sprite(
        self,
        sprite: pygame.Surface,
        guard: Guard,
    ) -> pygame.Surface:
        if guard.path:
            next_cell = guard.path[0]
            row_delta = next_cell[0] - guard.position[0]
            col_delta = next_cell[1] - guard.position[1]
        else:
            row_delta, col_delta = guard.facing_delta
        if col_delta < 0:
            return pygame.transform.flip(sprite, True, False)
        if row_delta < 0:
            return pygame.transform.rotate(sprite, 90)
        if row_delta > 0:
            return pygame.transform.rotate(sprite, -90)
        return sprite

    def draw_selected_vehicle(
        self,
        map_state: MapState,
        vehicles: list[Vehicle],
        selected_vehicle_id: int | None,
        guards: list[Guard] | None = None,
    ) -> None:
        if selected_vehicle_id is None:
            return
        vehicle = next((item for item in vehicles if item.id == selected_vehicle_id), None)
        if vehicle is None:
            return

        wait_reason = vehicle.wait_reason.value if vehicle.wait_reason else "NONE"
        lines = [
            "SELECTED",
            f"id: {vehicle.id}",
            f"type: {vehicle.type.value}",
            f"status: {vehicle.status.value}",
            f"reason: {wait_reason}",
            f"pos: {vehicle.position}",
            f"slot: {vehicle.assigned_slot}",
            f"path: {len(vehicle.path)}",
        ]
        for index, line in enumerate(lines):
            text = self.font.render(line, True, TEXT_COLOR)
            self.screen.blit(text, (10, 10 + index * 16))

        if vehicle.assigned_slot is not None:
            x, y = self._cell_to_pixel(map_state, vehicle.assigned_slot)
            rect = pygame.Rect(x + 3, y + 3, map_state.tile_size - 6, map_state.tile_size - 6)
            pygame.draw.rect(self.screen, WHITE, rect, 3)

        if guards:
            guard_lines = [
                "GUARDS",
                f"count: {len(guards)}",
            ]
            for guard in guards[:4]:
                guard_lines.append(
                    f"#{guard.id} {guard.task} pos={guard.position} target={guard.target_vehicle_id}"
                )
            for index, line in enumerate(guard_lines):
                text = self.font.render(line, True, TEXT_COLOR)
                self.screen.blit(text, (10, 150 + index * 16))

    def _current_map_width(self) -> int:
        if self._map_surface is not None:
            return self._map_surface.get_width()
        return 0

    def render(
        self,
        map_state: MapState,
        vehicles: list[Vehicle],
        selected_vehicle_id: int | None = None,
        guards: list[Guard] | None = None,
        current_algorithm: str | None = None,
        simulation_status: SimulationStatus = SimulationStatus.IDLE,
        placement_vehicle_type: VehicleType = VehicleType.CAR,
        placement_plan: VehiclePlan = VehiclePlan.ENTERING,
        active_scenario: str | None = None,
        simulation_speed: float = 1.0,
        step_mode_enabled: bool = False,
        night_mode: bool = False,
        sidebar_view: str = "simulation",
    ) -> None:
        world_size = map_pixel_size(map_state)
        if self._world_surface is None or self._world_surface.get_size() != world_size:
            self._world_surface = pygame.Surface(world_size)

        target_screen = self.screen
        self.screen = self._world_surface
        self.screen.fill((0, 0, 0))
        self.draw_map(map_state)
        if night_mode:
            self._draw_night_lighting(map_state, vehicles)
        self.draw_paths(map_state, vehicles)
        self.draw_vehicles(map_state, vehicles, selected_vehicle_id)
        self.draw_guards(map_state, guards)
        self.screen = target_screen

        target_screen.fill((5, 7, 11))
        viewport_rect = get_game_viewport_rect(target_screen.get_size(), map_state)
        pygame.draw.rect(target_screen, (6, 8, 13), viewport_rect)
        view_rect = get_map_view_rect(map_state, target_screen.get_size())
        scaled_world = pygame.transform.smoothscale(self._world_surface, view_rect.size)
        target_screen.blit(scaled_world, view_rect)
        self._draw_map_overlay(
            target_screen,
            view_rect,
            vehicles,
            selected_vehicle_id,
            simulation_status,
            placement_vehicle_type,
            placement_plan,
        )
        draw_hud(
            target_screen,
            self.font_bold,
            self.font,
            current_algorithm,
            vehicles,
            map_state,
            simulation_status,
            placement_vehicle_type,
            placement_plan,
            active_scenario,
            simulation_speed,
            step_mode_enabled,
            night_mode,
            sidebar_view,
            METRICS.snapshot(),
        )

    def _draw_night_lighting(
        self,
        map_state: MapState,
        vehicles: list[Vehicle],
    ) -> None:
        world_size = map_pixel_size(map_state)
        darkness = pygame.Surface(world_size, pygame.SRCALPHA)
        darkness.fill((3, 7, 18, 205))
        glow = pygame.Surface(world_size, pygame.SRCALPHA)

        tile_size = map_state.tile_size
        relief_mask, warm_glow = self._night_light_surfaces(tile_size)
        for position in map_state.lamp_cells:
            center = self._cell_center(map_state, position)
            relief_rect = relief_mask.get_rect(center=center)
            darkness.blit(
                relief_mask,
                relief_rect,
                special_flags=pygame.BLEND_RGBA_SUB,
            )
            glow.blit(warm_glow, warm_glow.get_rect(center=center))

        self._draw_vehicle_headlights(darkness, glow, map_state, vehicles)

        self.screen.blit(darkness, (0, 0))
        self.screen.blit(glow, (0, 0))

    def _draw_vehicle_headlights(
        self,
        darkness: pygame.Surface,
        glow: pygame.Surface,
        map_state: MapState,
        vehicles: list[Vehicle],
    ) -> None:
        active_statuses = {
            VehicleStatus.MOVING,
            VehicleStatus.WAITING,
            VehicleStatus.REROUTING,
            VehicleStatus.MANUAL,
        }
        direction_vectors = {
            "north": (0.0, -1.0),
            "south": (0.0, 1.0),
            "west": (-1.0, 0.0),
            "east": (1.0, 0.0),
            "northeast": (0.7071, -0.7071),
            "northwest": (-0.7071, -0.7071),
            "southeast": (0.7071, 0.7071),
            "southwest": (-0.7071, 0.7071),
        }
        tile_size = map_state.tile_size
        relief = pygame.Surface(darkness.get_size(), pygame.SRCALPHA)
        for vehicle in vehicles:
            if vehicle.status not in active_statuses:
                continue
            light_heading = self._vehicle_direction_name(vehicle, map_state)
            forward = direction_vectors.get(light_heading, (1.0, 0.0))
            perpendicular = (-forward[1], forward[0])
            center = self._vehicle_render_center(map_state, vehicle)
            lamp_offsets = (
                (-0.16, 0.16)
                if vehicle.type == VehicleType.CAR
                else (0.0,)
            )
            for side in lamp_offsets:
                origin = (
                    center[0]
                    + int(forward[0] * tile_size * 0.36)
                    + int(perpendicular[0] * tile_size * side),
                    center[1]
                    + int(forward[1] * tile_size * 0.36)
                    + int(perpendicular[1] * tile_size * side),
                )
                beam_relief, beam_glow = self._headlight_surfaces(
                    tile_size,
                    light_heading,
                )
                relief.blit(beam_relief, beam_relief.get_rect(center=origin))
                glow.blit(beam_glow, beam_glow.get_rect(center=origin))
        darkness.blit(relief, (0, 0), special_flags=pygame.BLEND_RGBA_SUB)

    def _headlight_surfaces(
        self,
        tile_size: int,
        heading: str,
    ) -> tuple[pygame.Surface, pygame.Surface]:
        cache_key = (tile_size, heading)
        cached = self._headlight_cache.get(cache_key)
        if cached is not None:
            return cached

        vectors = {
            "north": (0.0, -1.0),
            "south": (0.0, 1.0),
            "west": (-1.0, 0.0),
            "east": (1.0, 0.0),
            "northeast": (0.7071, -0.7071),
            "northwest": (-0.7071, -0.7071),
            "southeast": (0.7071, 0.7071),
            "southwest": (-0.7071, 0.7071),
        }
        forward = vectors.get(heading, (1.0, 0.0))
        perpendicular = (-forward[1], forward[0])
        length = tile_size * 3.0
        size = int(length * 2) + 2
        center = (size - 1) / 2
        relief = pygame.Surface((size, size), pygame.SRCALPHA)
        warm = pygame.Surface((size, size), pygame.SRCALPHA)

        for y in range(size):
            for x in range(size):
                relative_x = x - center
                relative_y = y - center
                forward_distance = (
                    relative_x * forward[0] + relative_y * forward[1]
                )
                if not 0 <= forward_distance <= length:
                    continue
                lateral_distance = abs(
                    relative_x * perpendicular[0]
                    + relative_y * perpendicular[1]
                )
                progress = forward_distance / length
                half_width = tile_size * (0.10 + 0.68 * progress)
                if lateral_distance >= half_width:
                    continue
                lateral_fade = (1.0 - lateral_distance / half_width) ** 2
                distance_fade = (1.0 - progress) ** 1.45
                intensity = lateral_fade * distance_fade
                relief.set_at((x, y), (0, 0, 0, int(112 * intensity)))
                warm.set_at((x, y), (255, 216, 142, int(58 * intensity)))

        self._headlight_cache[cache_key] = (relief, warm)
        return relief, warm

    def _night_light_surfaces(
        self,
        tile_size: int,
    ) -> tuple[pygame.Surface, pygame.Surface]:
        cached = self._night_light_cache.get(tile_size)
        if cached is not None:
            return cached

        radius = tile_size * 4
        diameter = radius * 2
        relief = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
        warm = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
        center = radius - 0.5
        for y in range(diameter):
            for x in range(diameter):
                distance = ((x - center) ** 2 + (y - center) ** 2) ** 0.5
                if distance >= radius:
                    continue
                normalized = distance / radius
                intensity = (1.0 - normalized) ** 2
                relief.set_at((x, y), (0, 0, 0, int(190 * intensity)))
                warm.set_at(
                    (x, y),
                    (255, 174, 72, int(72 * intensity)),
                )

        self._night_light_cache[tile_size] = (relief, warm)
        return relief, warm

    def _draw_map_overlay(
        self,
        screen: pygame.Surface,
        view_rect: pygame.Rect,
        vehicles: list[Vehicle],
        selected_vehicle_id: int | None,
        simulation_status: SimulationStatus,
        placement_vehicle_type: VehicleType,
        placement_plan: VehiclePlan,
    ) -> None:
        if view_rect.width < 420 or view_rect.height < 260:
            return

        if simulation_status == SimulationStatus.PLACING_VEHICLE:
            mode_text = (
                "PLACEMENT: "
                f"{placement_vehicle_type.value} / {placement_plan.value} - click a valid cell"
            )
            self._draw_overlay_box(
                screen,
                [mode_text],
                pygame.Rect(view_rect.left + 14, view_rect.top + 14, 0, 0),
                accent=(90, 165, 220),
            )

    def _draw_overlay_box(
        self,
        screen: pygame.Surface,
        lines: list[str],
        anchor: pygame.Rect,
        accent: tuple[int, int, int],
    ) -> None:
        rendered = [self.font.render(line, True, WHITE) for line in lines]
        width = max(text.get_width() for text in rendered) + 20
        height = len(rendered) * 18 + 14
        rect = pygame.Rect(anchor.left, anchor.top, width, height)
        pygame.draw.rect(screen, (12, 15, 20), rect, border_radius=6)
        pygame.draw.rect(screen, accent, rect, 2, border_radius=6)
        for index, text in enumerate(rendered):
            screen.blit(text, (rect.left + 10, rect.top + 8 + index * 18))


def _darken(color: tuple[int, int, int], amount: int) -> tuple[int, int, int]:
    return tuple(max(0, component - amount) for component in color)
