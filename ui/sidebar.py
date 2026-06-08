from collections.abc import Iterable

import pygame

from core.simulation_state import SimulationStatus, VehiclePlan
from models.enums import AlgorithmType, VehicleStatus, VehicleType
from models.map_state import MapState
from models.vehicle import Vehicle
from ui.button import UIButton
from ui.view_transform import get_control_panel_rect


ACTION_TRAFFIC_JAM = "traffic_jam"
ACTION_RESET = "reset"
ACTION_PLACE = "place"
ACTION_TYPE_CAR = "type_car"
ACTION_TYPE_MOTORBIKE = "type_motorbike"
ACTION_PLAN_ENTERING = "plan_entering"
ACTION_PLAN_EXITING = "plan_exiting"
ACTION_SPEED_NORMAL = "speed_normal"
ACTION_SPEED_SLOW = "speed_slow"
ACTION_STEP_MODE = "step_mode"
ACTION_NEXT_STEP = "next_step"
ACTION_MAIN_MENU = "main_menu"
ACTION_ALGORITHM_PREFIX = "algorithm:"

PANEL_PADDING = 22
BUTTON_HEIGHT = 28
BUTTON_GAP = 8

ALGORITHM_BUTTONS = [
    ("BFS", AlgorithmType.BFS),
    ("DFS", AlgorithmType.DFS),
    ("GREEDY", AlgorithmType.GREEDY),
    ("A*", AlgorithmType.ASTAR),
]


def algorithm_label(algorithm: str | AlgorithmType | None) -> str:
    if algorithm is None:
        return "A*"
    value = algorithm.value if isinstance(algorithm, AlgorithmType) else str(algorithm)
    value = value.upper()
    return "A*" if value == "ASTAR" else value


def sidebar_action_at_position(
    screen_size: tuple[int, int],
    position: tuple[int, int],
    map_state: MapState,
    current_algorithm: str | AlgorithmType,
    simulation_status: SimulationStatus,
    placement_vehicle_type: VehicleType,
    placement_plan: VehiclePlan,
    simulation_speed: float = 1.0,
    step_mode_enabled: bool = False,
) -> str | None:
    for button in build_sidebar_buttons(
        screen_size,
        map_state,
        current_algorithm,
        simulation_status,
        placement_vehicle_type,
        placement_plan,
        simulation_speed,
        step_mode_enabled,
    ):
        if button.enabled and button.rect.collidepoint(position):
            return button.action
    return None


def draw_sidebar(
    screen: pygame.Surface,
    font: pygame.font.Font,
    font_small: pygame.font.Font,
    current_algorithm: str | AlgorithmType,
    vehicles: Iterable[Vehicle],
    map_state: MapState,
    simulation_status: SimulationStatus,
    placement_vehicle_type: VehicleType,
    placement_plan: VehiclePlan,
    active_scenario: str | None,
    simulation_speed: float = 1.0,
    step_mode_enabled: bool = False,
) -> None:
    panel_rect = get_control_panel_rect(screen.get_size(), map_state)
    mouse_pos = pygame.mouse.get_pos()
    _draw_panel_background(screen, panel_rect)

    x = panel_rect.left + PANEL_PADDING
    width = panel_rect.width - PANEL_PADDING * 2
    y = 24
    _draw_title(screen, font, font_small, x, y, width)
    y += 62

    y = _draw_section(screen, font_small, "Algorithm", x, y)
    for button in _algorithm_buttons(
        x,
        y,
        width,
        current_algorithm,
    ):
        button.draw(screen, font_small, mouse_pos)
    y += (BUTTON_HEIGHT + BUTTON_GAP) * 2 + 20

    y = _draw_section(screen, font_small, "Simulation Mode", x, y)
    for button in _mode_buttons(x, y, width, simulation_status, active_scenario):
        button.draw(screen, font_small, mouse_pos)
    y += BUTTON_HEIGHT + 24

    y = _draw_section(screen, font_small, "Controls", x, y)
    for button in _control_buttons(
        x,
        y,
        width,
        simulation_status,
        placement_vehicle_type,
        placement_plan,
        simulation_speed,
        step_mode_enabled,
    ):
        button.draw(screen, font_small, mouse_pos)
    y += (BUTTON_HEIGHT + BUTTON_GAP) * 7 + 22

    y = _draw_section(screen, font_small, "Status", x, y)
    y = _draw_status_cards(screen, font, font_small, vehicles, x, y, width)

    if y + 120 < panel_rect.bottom - 18:
        y = _draw_section(screen, font_small, "Shortcuts", x, y + 12)
        _draw_shortcuts(screen, font_small, x, y)


def build_sidebar_buttons(
    screen_size: tuple[int, int],
    map_state: MapState,
    current_algorithm: str | AlgorithmType,
    simulation_status: SimulationStatus,
    placement_vehicle_type: VehicleType,
    placement_plan: VehiclePlan,
    simulation_speed: float = 1.0,
    step_mode_enabled: bool = False,
) -> list[UIButton]:
    panel_rect = get_control_panel_rect(screen_size, map_state)
    x = panel_rect.left + PANEL_PADDING
    width = panel_rect.width - PANEL_PADDING * 2
    y = 24 + 62
    y += 24
    buttons = _algorithm_buttons(x, y, width, current_algorithm)
    y += (BUTTON_HEIGHT + BUTTON_GAP) * 2 + 20
    y += 24
    buttons.extend(_mode_buttons(x, y, width, simulation_status, None))
    y += BUTTON_HEIGHT + 24
    y += 24
    buttons.extend(
        _control_buttons(
            x,
            y,
            width,
            simulation_status,
            placement_vehicle_type,
            placement_plan,
            simulation_speed,
            step_mode_enabled,
        )
    )
    return buttons


def _algorithm_buttons(
    x: int,
    y: int,
    width: int,
    current_algorithm: str | AlgorithmType,
) -> list[UIButton]:
    selected_label = algorithm_label(current_algorithm)
    button_width = (width - BUTTON_GAP) // 2
    buttons: list[UIButton] = []
    for index, (label, algorithm) in enumerate(ALGORITHM_BUTTONS):
        col = index % 2
        row = index // 2
        rect = pygame.Rect(
            x + col * (button_width + BUTTON_GAP),
            y + row * (BUTTON_HEIGHT + BUTTON_GAP),
            button_width,
            BUTTON_HEIGHT,
        )
        buttons.append(
            UIButton(
                f"{ACTION_ALGORITHM_PREFIX}{algorithm.value}",
                label,
                rect,
                selected=label == selected_label,
            )
        )
    return buttons


def _mode_buttons(
    x: int,
    y: int,
    width: int,
    simulation_status: SimulationStatus,
    active_scenario: str | None,
) -> list[UIButton]:
    return [
        UIButton(
            ACTION_TRAFFIC_JAM,
            "Traffic Jam Mode",
            pygame.Rect(x, y, width, BUTTON_HEIGHT),
            selected=active_scenario == "Traffic Jam Mode",
        )
    ]


def _control_buttons(
    x: int,
    y: int,
    width: int,
    simulation_status: SimulationStatus,
    placement_vehicle_type: VehicleType,
    placement_plan: VehiclePlan,
    simulation_speed: float,
    step_mode_enabled: bool,
) -> list[UIButton]:
    half_width = (width - BUTTON_GAP) // 2
    return [
        UIButton(
            ACTION_PLACE,
            "Place Vehicle",
            pygame.Rect(x, y, width, BUTTON_HEIGHT),
            selected=simulation_status == SimulationStatus.PLACING_VEHICLE,
        ),
        UIButton(
            ACTION_TYPE_CAR,
            "Car",
            pygame.Rect(x, y + BUTTON_HEIGHT + BUTTON_GAP, half_width, BUTTON_HEIGHT),
            selected=placement_vehicle_type == VehicleType.CAR,
        ),
        UIButton(
            ACTION_TYPE_MOTORBIKE,
            "Motorbike",
            pygame.Rect(
                x + half_width + BUTTON_GAP,
                y + BUTTON_HEIGHT + BUTTON_GAP,
                half_width,
                BUTTON_HEIGHT,
            ),
            selected=placement_vehicle_type == VehicleType.MOTORBIKE,
        ),
        UIButton(
            ACTION_PLAN_ENTERING,
            "Entering",
            pygame.Rect(x, y + (BUTTON_HEIGHT + BUTTON_GAP) * 2, half_width, BUTTON_HEIGHT),
            selected=placement_plan == VehiclePlan.ENTERING,
        ),
        UIButton(
            ACTION_PLAN_EXITING,
            "Exiting",
            pygame.Rect(
                x + half_width + BUTTON_GAP,
                y + (BUTTON_HEIGHT + BUTTON_GAP) * 2,
                half_width,
                BUTTON_HEIGHT,
            ),
            selected=placement_plan == VehiclePlan.EXITING,
        ),
        UIButton(
            ACTION_RESET,
            "Reset",
            pygame.Rect(x, y + (BUTTON_HEIGHT + BUTTON_GAP) * 3, width, BUTTON_HEIGHT),
        ),
        UIButton(
            ACTION_SPEED_NORMAL,
            "Normal Speed",
            pygame.Rect(x, y + (BUTTON_HEIGHT + BUTTON_GAP) * 4, half_width, BUTTON_HEIGHT),
            selected=not step_mode_enabled and simulation_speed >= 0.99,
        ),
        UIButton(
            ACTION_SPEED_SLOW,
            "Slow View",
            pygame.Rect(
                x + half_width + BUTTON_GAP,
                y + (BUTTON_HEIGHT + BUTTON_GAP) * 4,
                half_width,
                BUTTON_HEIGHT,
            ),
            selected=not step_mode_enabled and simulation_speed < 0.99,
        ),
        UIButton(
            ACTION_STEP_MODE,
            "Step Mode",
            pygame.Rect(x, y + (BUTTON_HEIGHT + BUTTON_GAP) * 5, half_width, BUTTON_HEIGHT),
            selected=step_mode_enabled,
        ),
        UIButton(
            ACTION_NEXT_STEP,
            "Next Step",
            pygame.Rect(
                x + half_width + BUTTON_GAP,
                y + (BUTTON_HEIGHT + BUTTON_GAP) * 5,
                half_width,
                BUTTON_HEIGHT,
            ),
        ),
        UIButton(
            ACTION_MAIN_MENU,
            "Main Menu",
            pygame.Rect(x, y + (BUTTON_HEIGHT + BUTTON_GAP) * 6, width, BUTTON_HEIGHT),
        ),
    ]


def _draw_panel_background(screen: pygame.Surface, rect: pygame.Rect) -> None:
    pygame.draw.rect(screen, (17, 18, 20), rect)
    pygame.draw.rect(screen, (53, 42, 31), rect, 4)
    inner = rect.inflate(-14, -14)
    pygame.draw.rect(screen, (24, 27, 31), inner)
    pygame.draw.rect(screen, (91, 74, 50), inner, 2)


def _draw_title(
    screen: pygame.Surface,
    font: pygame.font.Font,
    font_small: pygame.font.Font,
    x: int,
    y: int,
    width: int,
) -> None:
    title_rect = pygame.Rect(x, y, width, 46)
    pygame.draw.rect(screen, (38, 44, 38), title_rect)
    pygame.draw.rect(screen, (164, 133, 82), title_rect, 2)
    title = font.render("Smart Parking", True, (252, 236, 178))
    subtitle = font_small.render("2D Simulation", True, (190, 176, 132))
    screen.blit(title, (title_rect.left + 12, title_rect.top + 8))
    screen.blit(subtitle, (title_rect.left + 12, title_rect.top + 28))


def _draw_section(
    screen: pygame.Surface,
    font: pygame.font.Font,
    label: str,
    x: int,
    y: int,
) -> int:
    text = font.render(label.upper(), True, (132, 206, 119))
    screen.blit(text, (x, y))
    return y + 24


def _draw_status_cards(
    screen: pygame.Surface,
    font: pygame.font.Font,
    font_small: pygame.font.Font,
    vehicles: Iterable[Vehicle],
    x: int,
    y: int,
    width: int,
) -> int:
    vehicle_list = list(vehicles)
    stats = [
        ("Moving", sum(1 for vehicle in vehicle_list if vehicle.status == VehicleStatus.MOVING)),
        ("Parked", sum(1 for vehicle in vehicle_list if vehicle.status == VehicleStatus.PARKED)),
        ("Waiting", sum(1 for vehicle in vehicle_list if vehicle.status == VehicleStatus.WAITING)),
    ]
    card_height = 34
    for index, (name, value) in enumerate(stats):
        rect = pygame.Rect(x, y + index * (card_height + 8), width, card_height)
        pygame.draw.rect(screen, (35, 39, 43), rect)
        pygame.draw.rect(screen, (94, 105, 80), rect, 2)
        screen.blit(font_small.render(name, True, (208, 210, 180)), (rect.left + 10, rect.top + 9))
        value_text = font.render(str(value), True, (252, 236, 178))
        screen.blit(value_text, (rect.right - value_text.get_width() - 12, rect.top + 6))
    return y + len(stats) * (card_height + 8)


def _draw_shortcuts(
    screen: pygame.Surface,
    font: pygame.font.Font,
    x: int,
    y: int,
) -> None:
    hints = [
        "Enter: start ready simulation",
        "C/M: select vehicle type",
        "R: reset",
        "J: traffic jam mode",
        "N: next step",
        "F11: fullscreen",
    ]
    for index, hint in enumerate(hints):
        screen.blit(
            font.render(hint, True, (172, 176, 148)),
            (x, y + 28 + index * 20),
        )
