import pygame

from config import CELL_SIZE, LOG_MAX_LINES, SIDEBAR_WIDTH
from models.enums import CellType, VehicleStatus
from models.map_state import MapState
from models.vehicle import Vehicle
from ui.colors import (
    BLOCKED,
    CAR_SLOT,
    EMPTY,
    GATE,
    GRID_LINE,
    INTERSECTION,
    MOTO_SLOT,
    OBSTACLE,
    PATH_COLOR,
    ROAD,
    SIDEBAR_BG,
    TEXT_COLOR,
    VEHICLE_MANUAL,
    VEHICLE_MOVING,
    VEHICLE_PARKED,
    VEHICLE_REROUTING,
    VEHICLE_VIOLATION,
    VEHICLE_WAITING,
)
from ui.ui_layout import (
    LOG_AREA_HEIGHT,
    LOG_AREA_WIDTH,
    LOG_AREA_X,
    LOG_AREA_Y,
    SIDEBAR_X,
    WINDOW_HEIGHT,
)
from utils.grid_utils import cell_to_pixel
from utils.logger import Logger


class Renderer:
    def __init__(self, screen: pygame.Surface) -> None:
        self.screen = screen
        self.font = pygame.font.SysFont("monospace", 13)
        self.font_bold = pygame.font.SysFont("monospace", 14, bold=True)

    def draw_map(self, map_state: MapState) -> None:
        cell_colors = {
            CellType.ROAD: ROAD,
            CellType.GATE: GATE,
            CellType.INTERSECTION: INTERSECTION,
            CellType.CAR_SLOT: CAR_SLOT,
            CellType.MOTO_SLOT: MOTO_SLOT,
            CellType.OBSTACLE: OBSTACLE,
            CellType.BLOCKED: BLOCKED,
            CellType.EMPTY: EMPTY,
        }

        for row_index, row in enumerate(map_state.grid):
            for col_index, cell_type in enumerate(row):
                position = (row_index, col_index)
                color = cell_colors[cell_type]
                if position in map_state.dynamic_blocks:
                    color = BLOCKED

                x, y = cell_to_pixel(position)
                rect = pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)
                pygame.draw.rect(self.screen, color, rect)
                pygame.draw.rect(self.screen, GRID_LINE, rect, 1)

    def draw_vehicles(self, vehicles: list[Vehicle]) -> None:
        status_colors = {
            VehicleStatus.MOVING: VEHICLE_MOVING,
            VehicleStatus.PARKED: VEHICLE_PARKED,
            VehicleStatus.WAITING: VEHICLE_WAITING,
            VehicleStatus.MANUAL: VEHICLE_MANUAL,
            VehicleStatus.REROUTING: VEHICLE_REROUTING,
            VehicleStatus.VIOLATION: VEHICLE_VIOLATION,
        }

        for vehicle in vehicles:
            x, y = cell_to_pixel(vehicle.position)
            center = (x + CELL_SIZE // 2, y + CELL_SIZE // 2)
            radius = CELL_SIZE // 2 - 4
            pygame.draw.circle(self.screen, status_colors[vehicle.status], center, radius)

            label = self.font_bold.render(str(vehicle.id), True, TEXT_COLOR)
            label_rect = label.get_rect(center=center)
            self.screen.blit(label, label_rect)

    def draw_paths(self, vehicles: list[Vehicle]) -> None:
        for vehicle in vehicles:
            if vehicle.status in (VehicleStatus.MOVING, VehicleStatus.REROUTING) and vehicle.path:
                for position in vehicle.path:
                    x, y = cell_to_pixel(position)
                    center = (x + CELL_SIZE // 2, y + CELL_SIZE // 2)
                    pygame.draw.circle(self.screen, PATH_COLOR, center, 4)

    def draw_sidebar(self) -> None:
        rect = pygame.Rect(SIDEBAR_X, 0, SIDEBAR_WIDTH, WINDOW_HEIGHT)
        pygame.draw.rect(self.screen, SIDEBAR_BG, rect)
        title = self.font_bold.render("SMART PARKING", True, TEXT_COLOR)
        self.screen.blit(title, (SIDEBAR_X + 10, 20))

    def draw_logs(self) -> None:
        logs = Logger.get_logs()[-LOG_MAX_LINES:]
        max_lines = LOG_AREA_HEIGHT // 16
        logs = logs[-max_lines:]
        start_y = LOG_AREA_Y + LOG_AREA_HEIGHT - len(logs) * 16

        clip_rect = pygame.Rect(
            LOG_AREA_X,
            LOG_AREA_Y,
            LOG_AREA_WIDTH,
            LOG_AREA_HEIGHT,
        )
        previous_clip = self.screen.get_clip()
        self.screen.set_clip(clip_rect)
        for index, log_line in enumerate(logs):
            text = self.font.render(log_line, True, TEXT_COLOR)
            self.screen.blit(text, (LOG_AREA_X, start_y + index * 16))
        self.screen.set_clip(previous_clip)

    def draw_stats(self, vehicles: list[Vehicle]) -> None:
        moving = sum(1 for vehicle in vehicles if vehicle.status == VehicleStatus.MOVING)
        parked = sum(1 for vehicle in vehicles if vehicle.status == VehicleStatus.PARKED)
        waiting = sum(1 for vehicle in vehicles if vehicle.status == VehicleStatus.WAITING)
        violation = sum(1 for vehicle in vehicles if vehicle.status == VehicleStatus.VIOLATION)

        lines = [
            f"Moving: {moving}",
            f"Parked: {parked}",
            f"Waiting: {waiting}",
            f"Violation: {violation}",
        ]
        for index, line in enumerate(lines):
            text = self.font.render(line, True, TEXT_COLOR)
            self.screen.blit(text, (SIDEBAR_X + 10, 60 + index * 18))

    def render(self, map_state: MapState, vehicles: list[Vehicle]) -> None:
        self.draw_map(map_state)
        self.draw_paths(vehicles)
        self.draw_vehicles(vehicles)
        self.draw_sidebar()
        self.draw_stats(vehicles)
        self.draw_logs()
