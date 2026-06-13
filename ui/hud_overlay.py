from collections.abc import Iterable

import pygame

from core.simulation_state import SimulationStatus, VehiclePlan
from core.pathfinding_metrics import AlgorithmMetrics
from models.enums import AlgorithmType, VehicleType
from models.map_state import MapState
from models.vehicle import Vehicle
from ui.sidebar import (
    draw_sidebar,
    sidebar_action_at_position,
)


def algorithm_at_position(
    screen_size: tuple[int, int],
    position: tuple[int, int],
    map_state: MapState | None = None,
) -> AlgorithmType | None:
    if map_state is None:
        return None
    action = sidebar_action_at_position(
        screen_size,
        position,
        map_state,
        AlgorithmType.ASTAR,
        SimulationStatus.IDLE,
        VehicleType.CAR,
        VehiclePlan.ENTERING,
    )
    if action is None or not action.startswith("algorithm:"):
        return None
    return AlgorithmType(action.split(":", 1)[1])


def draw_hud(
    screen: pygame.Surface,
    font: pygame.font.Font,
    font_small: pygame.font.Font,
    current_algorithm: str | AlgorithmType | None,
    vehicles: Iterable[Vehicle],
    map_state: MapState | None = None,
    simulation_status: SimulationStatus = SimulationStatus.IDLE,
    placement_vehicle_type: VehicleType = VehicleType.CAR,
    placement_plan: VehiclePlan = VehiclePlan.ENTERING,
    active_scenario: str | None = None,
    simulation_speed: float = 1.0,
    step_mode_enabled: bool = False,
    pathfinding_metrics: dict[str, AlgorithmMetrics] | None = None,
) -> None:
    if map_state is None:
        return
    draw_sidebar(
        screen,
        font,
        font_small,
        current_algorithm or AlgorithmType.ASTAR,
        vehicles,
        map_state,
        simulation_status,
        placement_vehicle_type,
        placement_plan,
        active_scenario,
        simulation_speed,
        step_mode_enabled,
        pathfinding_metrics,
    )
