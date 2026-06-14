from collections.abc import Iterable

import pygame

from core.pathfinding_metrics import AlgorithmMetrics
from core.simulation_state import SimulationStatus, VehiclePlan
from models.enums import AlgorithmType, VehicleType
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
ACTION_PREVIOUS_STEP = "previous_step"
ACTION_MAIN_MENU = "main_menu"
ACTION_ALGORITHM_PREFIX = "algorithm:"

PANEL_PADDING = 22
BUTTON_HEIGHT = 28
BUTTON_GAP = 8
COMPACT_HEIGHT_THRESHOLD = 760
COMPACT_BUTTON_HEIGHT = 22
COMPACT_BUTTON_GAP = 4

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
    pathfinding_metrics: dict[str, AlgorithmMetrics] | None = None,
) -> None:
    panel_rect = get_control_panel_rect(screen.get_size(), map_state)
    mouse_pos = pygame.mouse.get_pos()
    _draw_panel_background(screen, panel_rect)
    compact = panel_rect.height < COMPACT_HEIGHT_THRESHOLD
    button_height = COMPACT_BUTTON_HEIGHT if compact else BUTTON_HEIGHT
    button_gap = COMPACT_BUTTON_GAP if compact else BUTTON_GAP
    section_gap = 14 if compact else 24

    x = panel_rect.left + PANEL_PADDING
    width = panel_rect.width - PANEL_PADDING * 2
    y = 12 if compact else 24
    title_height = _draw_title(screen, font, font_small, x, y, width, compact)
    y += title_height + (10 if compact else 16)

    y = _draw_section(screen, font_small, "Algorithm", x, y, compact)
    for button in _algorithm_buttons(
        x,
        y,
        width,
        current_algorithm,
        button_height,
        button_gap,
    ):
        button.draw(screen, font_small, mouse_pos)
    y += (button_height + button_gap) * 2 + section_gap

    y = _draw_section(screen, font_small, "Simulation Mode", x, y, compact)
    for button in _mode_buttons(x, y, width, simulation_status, active_scenario, button_height):
        button.draw(screen, font_small, mouse_pos)
    y += button_height + section_gap

    y = _draw_section(screen, font_small, "Controls", x, y, compact)
    for button in _control_buttons(
        x,
        y,
        width,
        simulation_status,
        placement_vehicle_type,
        placement_plan,
        simulation_speed,
        step_mode_enabled,
        button_height,
        button_gap,
    ):
        button.draw(screen, font_small, mouse_pos)
    y += (button_height + button_gap) * 8 + section_gap

    y = _draw_section(screen, font_small, "Algorithm Metrics", x, y, compact)
    metrics_x = max(panel_rect.left + 12, x - 10)
    metrics_width = min(panel_rect.right - metrics_x - 12, width + 20)
    y = _draw_metrics_table(
        screen,
        font_small,
        pathfinding_metrics or {},
        current_algorithm,
        metrics_x,
        y,
        metrics_width,
        compact,
    )

    if not compact and y + 120 < panel_rect.bottom - 18:
        y = _draw_section(screen, font_small, "Shortcuts", x, y + 12, compact)
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
    compact = panel_rect.height < COMPACT_HEIGHT_THRESHOLD
    button_height = COMPACT_BUTTON_HEIGHT if compact else BUTTON_HEIGHT
    button_gap = COMPACT_BUTTON_GAP if compact else BUTTON_GAP
    section_gap = 14 if compact else 24
    x = panel_rect.left + PANEL_PADDING
    width = panel_rect.width - PANEL_PADDING * 2
    y = 12 if compact else 24
    y += (36 if compact else 46) + (10 if compact else 16)
    y += 18 if compact else 24
    buttons = _algorithm_buttons(x, y, width, current_algorithm, button_height, button_gap)
    y += (button_height + button_gap) * 2 + section_gap
    y += 18 if compact else 24
    buttons.extend(_mode_buttons(x, y, width, simulation_status, None, button_height))
    y += button_height + section_gap
    y += 18 if compact else 24
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
            button_height,
            button_gap,
        )
    )
    return buttons


def _algorithm_buttons(
    x: int,
    y: int,
    width: int,
    current_algorithm: str | AlgorithmType,
    button_height: int,
    button_gap: int,
) -> list[UIButton]:
    selected_label = algorithm_label(current_algorithm)
    button_width = (width - button_gap) // 2
    buttons: list[UIButton] = []
    for index, (label, algorithm) in enumerate(ALGORITHM_BUTTONS):
        col = index % 2
        row = index // 2
        rect = pygame.Rect(
            x + col * (button_width + button_gap),
            y + row * (button_height + button_gap),
            button_width,
            button_height,
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
    button_height: int,
) -> list[UIButton]:
    return [
        UIButton(
            ACTION_TRAFFIC_JAM,
            "Traffic Jam Mode",
            pygame.Rect(x, y, width, button_height),
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
    button_height: int,
    button_gap: int,
) -> list[UIButton]:
    half_width = (width - button_gap) // 2
    return [
        UIButton(
            ACTION_PLACE,
            "Place Vehicle",
            pygame.Rect(x, y, width, button_height),
            selected=simulation_status == SimulationStatus.PLACING_VEHICLE,
        ),
        UIButton(
            ACTION_TYPE_CAR,
            "Car",
            pygame.Rect(x, y + button_height + button_gap, half_width, button_height),
            selected=placement_vehicle_type == VehicleType.CAR,
        ),
        UIButton(
            ACTION_TYPE_MOTORBIKE,
            "Motorbike",
            pygame.Rect(
                x + half_width + button_gap,
                y + button_height + button_gap,
                half_width,
                button_height,
            ),
            selected=placement_vehicle_type == VehicleType.MOTORBIKE,
        ),
        UIButton(
            ACTION_PLAN_ENTERING,
            "Entering",
            pygame.Rect(x, y + (button_height + button_gap) * 2, half_width, button_height),
            selected=placement_plan == VehiclePlan.ENTERING,
        ),
        UIButton(
            ACTION_PLAN_EXITING,
            "Exiting",
            pygame.Rect(
                x + half_width + button_gap,
                y + (button_height + button_gap) * 2,
                half_width,
                button_height,
            ),
            selected=placement_plan == VehiclePlan.EXITING,
        ),
        UIButton(
            ACTION_RESET,
            "Reset",
            pygame.Rect(x, y + (button_height + button_gap) * 3, width, button_height),
        ),
        UIButton(
            ACTION_SPEED_NORMAL,
            "Normal Speed",
            pygame.Rect(x, y + (button_height + button_gap) * 4, half_width, button_height),
            selected=not step_mode_enabled and simulation_speed >= 0.99,
        ),
        UIButton(
            ACTION_SPEED_SLOW,
            "Slow View",
            pygame.Rect(
                x + half_width + button_gap,
                y + (button_height + button_gap) * 4,
                half_width,
                button_height,
            ),
            selected=not step_mode_enabled and simulation_speed < 0.99,
        ),
        UIButton(
            ACTION_STEP_MODE,
            "Step Mode",
            pygame.Rect(x, y + (button_height + button_gap) * 5, width, button_height),
            selected=step_mode_enabled,
        ),
        UIButton(
            ACTION_PREVIOUS_STEP,
            "< Prev",
            pygame.Rect(x, y + (button_height + button_gap) * 6, half_width, button_height),
        ),
        UIButton(
            ACTION_NEXT_STEP,
            "Next >",
            pygame.Rect(
                x + half_width + button_gap,
                y + (button_height + button_gap) * 6,
                half_width,
                button_height,
            ),
        ),
        UIButton(
            ACTION_MAIN_MENU,
            "Main Menu",
            pygame.Rect(x, y + (button_height + button_gap) * 7, width, button_height),
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
    compact: bool = False,
) -> int:
    title_height = 36 if compact else 46
    title_rect = pygame.Rect(x, y, width, title_height)
    pygame.draw.rect(screen, (38, 44, 38), title_rect)
    pygame.draw.rect(screen, (164, 133, 82), title_rect, 2)
    title = font.render("Smart Parking", True, (252, 236, 178))
    subtitle = font_small.render("2D Simulation", True, (190, 176, 132))
    screen.blit(title, (title_rect.left + 12, title_rect.top + (6 if compact else 8)))
    if not compact:
        screen.blit(subtitle, (title_rect.left + 12, title_rect.top + 28))
    return title_height


def _draw_section(
    screen: pygame.Surface,
    font: pygame.font.Font,
    label: str,
    x: int,
    y: int,
    compact: bool = False,
) -> int:
    text = font.render(label.upper(), True, (132, 206, 119))
    screen.blit(text, (x, y))
    return y + (18 if compact else 24)


def _draw_metrics_table(
    screen: pygame.Surface,
    font_small: pygame.font.Font,
    metrics_by_algorithm: dict[str, AlgorithmMetrics],
    current_algorithm: str | AlgorithmType,
    x: int,
    y: int,
    width: int,
    compact: bool = False,
) -> int:
    row_height = 20 if compact else 24
    header_height = 18 if compact else 22
    table_height = header_height + row_height * len(ALGORITHM_BUTTONS)
    table_rect = pygame.Rect(x, y, width, table_height)
    pygame.draw.rect(screen, (28, 32, 36), table_rect)

    columns = [
        ("Alg", 0.02),
        ("Calls", 0.28),
        ("Last", 0.43),
        ("Avg", 0.56),
        ("Best", 0.68),
        ("Worst", 0.80),
        ("KB", 0.90),
        ("Len", 0.99),
    ]
    selected_label = algorithm_label(current_algorithm)
    _draw_metrics_row(
        screen,
        font_small,
        table_rect,
        y,
        columns,
        ["Alg", "Calls", "Last", "Avg", "Best", "Worst", "KB", "Len"],
        (160, 175, 145),
    )

    for index, (label, algorithm) in enumerate(ALGORITHM_BUTTONS):
        row_y = y + header_height + index * row_height
        algorithm_key = algorithm.value.lower()
        metrics = metrics_by_algorithm.get(algorithm_key)
        if label == selected_label:
            pygame.draw.rect(
                screen,
                (39, 59, 45),
                pygame.Rect(x + 2, row_y, width - 4, row_height),
            )
        values = [
            _compact_algorithm_label(label),
            "-" if metrics is None or metrics.runs == 0 else str(metrics.runs),
            _format_ms(None if metrics is None else metrics.last_time_ms),
            _format_ms(None if metrics is None else metrics.avg_time_ms),
            _format_ms(None if metrics is None else metrics.best_time_ms),
            _format_ms(None if metrics is None else metrics.worst_time_ms),
            _format_kb(None if metrics is None else metrics.last_memory_kb),
            "-" if metrics is None or metrics.last_path_length is None else str(metrics.last_path_length),
        ]
        color = (252, 236, 178) if label == selected_label else (214, 218, 190)
        _draw_metrics_row(
            screen,
            font_small,
            table_rect,
            row_y,
            columns,
            values,
            color,
        )

    pygame.draw.rect(screen, (94, 105, 80), table_rect, 2)
    return y + table_height + 8


def _draw_metrics_row(
    screen: pygame.Surface,
    font: pygame.font.Font,
    table_rect: pygame.Rect,
    y: int,
    columns: list[tuple[str, float]],
    values: list[str],
    color: tuple[int, int, int],
) -> None:
    for index, value in enumerate(values):
        _, offset = columns[index]
        text = font.render(value, True, color)
        if index == 0:
            text_x = table_rect.left + 8 + int(table_rect.width * offset)
        else:
            column_right = table_rect.left + int(table_rect.width * offset)
            text_x = column_right - text.get_width()
        screen.blit(text, (text_x, y + 5))


def _compact_algorithm_label(label: str) -> str:
    return "GRE" if label == "GREEDY" else label


def _format_ms(value: float | None) -> str:
    if value is None:
        return "-"
    if value < 1:
        return f"{value:.2f}"
    if value < 10:
        return f"{value:.1f}"
    return f"{value:.0f}"


def _format_kb(value: float | None) -> str:
    if value is None:
        return "-"
    if value < 10:
        return f"{value:.1f}"
    return f"{value:.0f}"


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
        "P: previous step",
        "F11: fullscreen",
    ]
    for index, hint in enumerate(hints):
        screen.blit(
            font.render(hint, True, (172, 176, 148)),
            (x, y + 28 + index * 20),
        )
