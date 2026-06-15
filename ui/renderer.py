from pathlib import Path

import pygame

from core.simulation_state import SimulationStatus, VehiclePlan
from core.pathfinding_metrics import METRICS
from models.enums import VehicleStatus, VehicleType
from models.guard import Guard
from models.map_state import MapState
from models.vehicle import Vehicle
from ui.colors import (
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

        if map_state.image_path:
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
            x, y = self._cell_to_pixel(map_state, vehicle.position)
            center = self._cell_center(map_state, vehicle.position)
            radius = map_state.tile_size // 2 - 5
            color = status_colors[vehicle.status]
            sprite = self._get_vehicle_sprite(vehicle)
            if sprite is not None:
                sprite_rect = sprite.get_rect(center=center)
                self.screen.blit(sprite, sprite_rect)
                label_text = f"C{vehicle.id}" if vehicle.type.value == "CAR" else f"M{vehicle.id}"
            elif vehicle.type.value == "CAR":
                rect = pygame.Rect(0, 0, map_state.tile_size - 8, map_state.tile_size - 12)
                rect.center = center
                pygame.draw.rect(self.screen, color, rect, border_radius=4)
                pygame.draw.rect(self.screen, WHITE, rect, 2)
                label_text = f"C{vehicle.id}"
            else:
                pygame.draw.circle(self.screen, color, center, radius)
                pygame.draw.circle(self.screen, WHITE, center, radius, 2)
                label_text = f"M{vehicle.id}"

            if vehicle.id == selected_vehicle_id:
                selected_rect = pygame.Rect(x + 2, y + 2, map_state.tile_size - 4, map_state.tile_size - 4)
                pygame.draw.rect(self.screen, WHITE, selected_rect, 3)

            pygame.draw.circle(self.screen, color, (x + map_state.tile_size - 7, y + 7), 4)
            label = self.font_bold.render(label_text, True, TEXT_COLOR)
            label_rect = label.get_rect(center=(center[0], y + map_state.tile_size - 7))
            self.screen.blit(label, label_rect)

    def _get_vehicle_sprite(self, vehicle: Vehicle) -> pygame.Surface | None:
        if vehicle.type.value == "CAR":
            return self._get_car_sprite(vehicle)
        return self._get_motorbike_sprite(vehicle)

    def _get_motorbike_sprite(self, vehicle: Vehicle) -> pygame.Surface | None:
        sprite_options = (
            [("directional", sprite_id) for sprite_id in self._motorbike_sprite_ids]
            + [("oriented", sprite_key) for sprite_key in self._fallback_motorbike_sprite_keys]
        )
        if not sprite_options:
            return None

        sprite_type, sprite_id = sprite_options[vehicle.id % len(sprite_options)]
        if sprite_type == "directional":
            for direction in self._direction_fallbacks(self._vehicle_direction_name(vehicle)):
                sprite = self._sprites.get(f"{sprite_id}_{direction}")
                if sprite is not None:
                    return sprite

        sprite = self._sprites.get(sprite_id)
        if sprite is None:
            return None
        return self._orient_vehicle_sprite(sprite, vehicle)

    def _get_car_sprite(self, vehicle: Vehicle) -> pygame.Surface | None:
        if self._car_sprite_ids:
            sprite_id = self._car_sprite_ids[vehicle.id % len(self._car_sprite_ids)]
            for direction in self._direction_fallbacks(self._vehicle_direction_name(vehicle)):
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
        return self._orient_vehicle_sprite(sprite, vehicle)

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

    def _vehicle_direction_name(self, vehicle: Vehicle) -> str:
        if not vehicle.path:
            return "east"

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
    ) -> pygame.Surface:
        if not vehicle.path:
            return sprite

        next_cell = vehicle.path[0]
        row_delta = next_cell[0] - vehicle.position[0]
        col_delta = next_cell[1] - vehicle.position[1]
        if col_delta < 0:
            return pygame.transform.flip(sprite, True, False)
        if row_delta < 0:
            return pygame.transform.rotate(sprite, 90)
        if row_delta > 0:
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
    ) -> None:
        world_size = map_pixel_size(map_state)
        if self._world_surface is None or self._world_surface.get_size() != world_size:
            self._world_surface = pygame.Surface(world_size)

        target_screen = self.screen
        self.screen = self._world_surface
        self.screen.fill((0, 0, 0))
        self.draw_map(map_state)
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
            METRICS.snapshot(),
        )
