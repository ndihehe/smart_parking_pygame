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
ACTION_TOGGLE_NIGHT = "toggle_night"
ACTION_VIEW_SIMULATION = "view_simulation"
ACTION_VIEW_ADD_VEHICLE = "view_add_vehicle"
ACTION_VIEW_SCENARIOS = "view_scenarios"
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

_TITLE_FONTS: dict[int, pygame.font.Font] = {}


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
    night_mode: bool = False,
    sidebar_view: str = "simulation",
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
        night_mode,
        sidebar_view,
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
    night_mode: bool = False,
    sidebar_view: str = "simulation",
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
    groups, y = _contextual_sidebar_groups(
        x,
        y,
        width,
        current_algorithm,
        simulation_status,
        placement_vehicle_type,
        placement_plan,
        simulation_speed,
        step_mode_enabled,
        night_mode,
        sidebar_view,
        button_height,
        button_gap,
        section_gap,
        compact,
        active_scenario,
    )
    for label, label_y, buttons in groups:
        _draw_section(screen, font_small, label, x, label_y, compact)
        for button in buttons:
            button.draw(screen, font_small, mouse_pos)

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
    available_chart_height = panel_rect.bottom - y - 16
    if available_chart_height >= 150:
        y = _draw_algorithm_charts(
            screen,
            font_small,
            pathfinding_metrics or {},
            current_algorithm,
            metrics_x,
            y,
            metrics_width,
            min(190, available_chart_height),
        )

def build_sidebar_buttons(
    screen_size: tuple[int, int],
    map_state: MapState,
    current_algorithm: str | AlgorithmType,
    simulation_status: SimulationStatus,
    placement_vehicle_type: VehicleType,
    placement_plan: VehiclePlan,
    simulation_speed: float = 1.0,
    step_mode_enabled: bool = False,
    night_mode: bool = False,
    sidebar_view: str = "simulation",
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
    groups, _end_y = _contextual_sidebar_groups(
        x,
        y,
        width,
        current_algorithm,
        simulation_status,
        placement_vehicle_type,
        placement_plan,
        simulation_speed,
        step_mode_enabled,
        night_mode,
        sidebar_view,
        button_height,
        button_gap,
        section_gap,
        compact,
        None,
    )
    return [button for _label, _label_y, buttons in groups for button in buttons]


def _contextual_sidebar_groups(
    x: int,
    y: int,
    width: int,
    current_algorithm: str | AlgorithmType,
    simulation_status: SimulationStatus,
    placement_vehicle_type: VehicleType,
    placement_plan: VehiclePlan,
    simulation_speed: float,
    step_mode_enabled: bool,
    night_mode: bool,
    sidebar_view: str,
    button_height: int,
    button_gap: int,
    section_gap: int,
    compact: bool,
    active_scenario: str | None,
) -> tuple[list[tuple[str, int, list[UIButton]]], int]:
    groups: list[tuple[str, int, list[UIButton]]] = []
    header_height = 18 if compact else 24

    def add_group(label: str, buttons: list[UIButton], rows: int) -> None:
        nonlocal y
        groups.append((label, y, buttons))
        y += header_height + rows * button_height + max(0, rows - 1) * button_gap
        y += section_gap

    add_group(
        "Mode",
        _view_buttons(x, y + header_height, width, sidebar_view, button_height, button_gap),
        1,
    )

    content_y = y + header_height
    if sidebar_view == "add_vehicle":
        buttons = _add_vehicle_context_buttons(
            x,
            content_y,
            width,
            simulation_status,
            placement_vehicle_type,
            placement_plan,
            button_height,
            button_gap,
        )
        add_group("Vehicle Setup", buttons, 3)
    elif sidebar_view == "scenarios":
        buttons = _scenario_context_buttons(
            x,
            content_y,
            width,
            active_scenario,
            button_height,
        )
        add_group("Scenarios", buttons, 1)
    else:
        buttons, rows = _simulation_context_buttons(
            x,
            content_y,
            width,
            current_algorithm,
            simulation_speed,
            step_mode_enabled,
            button_height,
            button_gap,
        )
        add_group("Simulation", buttons, rows)

    utility_y = y + header_height
    add_group(
        "General",
        _utility_buttons(
            x,
            utility_y,
            width,
            night_mode,
            button_height,
            button_gap,
        ),
        2,
    )
    return groups, y


def _view_buttons(
    x: int,
    y: int,
    width: int,
    sidebar_view: str,
    button_height: int,
    button_gap: int,
) -> list[UIButton]:
    labels = [
        (ACTION_VIEW_SIMULATION, "Simulation", "simulation"),
        (ACTION_VIEW_ADD_VEHICLE, "Add Vehicle", "add_vehicle"),
        (ACTION_VIEW_SCENARIOS, "Scenarios", "scenarios"),
    ]
    button_width = (width - button_gap * 2) // 3
    return [
        UIButton(
            action,
            label,
            pygame.Rect(x + index * (button_width + button_gap), y, button_width, button_height),
            selected=sidebar_view == view,
        )
        for index, (action, label, view) in enumerate(labels)
    ]


def _simulation_context_buttons(
    x: int,
    y: int,
    width: int,
    current_algorithm: str | AlgorithmType,
    simulation_speed: float,
    step_mode_enabled: bool,
    button_height: int,
    button_gap: int,
) -> tuple[list[UIButton], int]:
    algorithms = _algorithm_buttons(
        x, y, width, current_algorithm, button_height, button_gap
    )
    speed_y = y + (button_height + button_gap) * 2
    third_width = (width - button_gap * 2) // 3
    speed_buttons = [
        UIButton(
            ACTION_SPEED_SLOW,
            "Slow",
            pygame.Rect(x, speed_y, third_width, button_height),
            selected=not step_mode_enabled and simulation_speed < 0.99,
        ),
        UIButton(
            ACTION_SPEED_NORMAL,
            "Normal",
            pygame.Rect(x + third_width + button_gap, speed_y, third_width, button_height),
            selected=not step_mode_enabled and simulation_speed >= 0.99,
        ),
        UIButton(
            ACTION_STEP_MODE,
            "Step",
            pygame.Rect(x + (third_width + button_gap) * 2, speed_y, third_width, button_height),
            selected=step_mode_enabled,
        ),
    ]
    buttons = algorithms + speed_buttons
    rows = 3
    if step_mode_enabled:
        step_y = speed_y + button_height + button_gap
        half_width = (width - button_gap) // 2
        buttons.extend(
            [
                UIButton(ACTION_PREVIOUS_STEP, "< Prev", pygame.Rect(x, step_y, half_width, button_height)),
                UIButton(
                    ACTION_NEXT_STEP,
                    "Next >",
                    pygame.Rect(x + half_width + button_gap, step_y, half_width, button_height),
                ),
            ]
        )
        rows = 4
    return buttons, rows


def _add_vehicle_context_buttons(
    x: int,
    y: int,
    width: int,
    simulation_status: SimulationStatus,
    vehicle_type: VehicleType,
    plan: VehiclePlan,
    button_height: int,
    button_gap: int,
) -> list[UIButton]:
    half_width = (width - button_gap) // 2
    return [
        UIButton(ACTION_TYPE_CAR, "Car", pygame.Rect(x, y, half_width, button_height), selected=vehicle_type == VehicleType.CAR),
        UIButton(ACTION_TYPE_MOTORBIKE, "Motorbike", pygame.Rect(x + half_width + button_gap, y, half_width, button_height), selected=vehicle_type == VehicleType.MOTORBIKE),
        UIButton(ACTION_PLAN_ENTERING, "Entering", pygame.Rect(x, y + button_height + button_gap, half_width, button_height), selected=plan == VehiclePlan.ENTERING),
        UIButton(
            ACTION_PLAN_EXITING,
            "Exiting",
            pygame.Rect(
                x + half_width + button_gap,
                y + button_height + button_gap,
                half_width,
                button_height,
            ),
            selected=plan == VehiclePlan.EXITING,
            enabled=simulation_status == SimulationStatus.PLACING_VEHICLE,
        ),
        UIButton(
            ACTION_PLACE,
            "Finish Placement"
            if simulation_status == SimulationStatus.PLACING_VEHICLE
            else "Place on Map",
            pygame.Rect(x, y + (button_height + button_gap) * 2, width, button_height),
            selected=simulation_status == SimulationStatus.PLACING_VEHICLE,
        ),
    ]


def _scenario_context_buttons(
    x: int,
    y: int,
    width: int,
    active_scenario: str | None,
    button_height: int,
) -> list[UIButton]:
    return [
        UIButton(
            ACTION_TRAFFIC_JAM,
            "Traffic Jam",
            pygame.Rect(x, y, width, button_height),
            selected=active_scenario == "Traffic Jam Mode",
        )
    ]


def _utility_buttons(
    x: int,
    y: int,
    width: int,
    night_mode: bool,
    button_height: int,
    button_gap: int,
) -> list[UIButton]:
    half_width = (width - button_gap) // 2
    return [
        UIButton(ACTION_RESET, "Reset", pygame.Rect(x, y, half_width, button_height)),
        UIButton(
            ACTION_TOGGLE_NIGHT,
            "Day" if night_mode else "Night",
            pygame.Rect(x + half_width + button_gap, y, half_width, button_height),
            selected=night_mode,
        ),
        UIButton(
            ACTION_MAIN_MENU,
            "Main Menu",
            pygame.Rect(x, y + button_height + button_gap, width, button_height),
        ),
    ]


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
    night_mode: bool,
    button_height: int,
    button_gap: int,
) -> list[UIButton]:
    half_width = (width - button_gap) // 2
    placement_mode = simulation_status == SimulationStatus.PLACING_VEHICLE
    return [
        UIButton(
            ACTION_PLACE,
            "Place Vehicle",
            pygame.Rect(x, y, width, button_height),
            selected=placement_mode,
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
            enabled=placement_mode,
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
            enabled=placement_mode,
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
            ACTION_TOGGLE_NIGHT,
            "Day Mode" if night_mode else "Night Mode",
            pygame.Rect(x, y + (button_height + button_gap) * 7, width, button_height),
            selected=night_mode,
        ),
        UIButton(
            ACTION_MAIN_MENU,
            "Main Menu",
            pygame.Rect(x, y + (button_height + button_gap) * 8, width, button_height),
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
    font_size = 16 if compact else 20
    title_font = _TITLE_FONTS.get(font_size)
    if title_font is None:
        title_font = pygame.font.SysFont("monospace", font_size, bold=True)
        _TITLE_FONTS[font_size] = title_font
    title = title_font.render("Smart Parking Simulator", True, (252, 236, 178))
    screen.blit(title, title.get_rect(center=title_rect.center))
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


def _draw_algorithm_charts(
    screen: pygame.Surface,
    font: pygame.font.Font,
    metrics_by_algorithm: dict[str, AlgorithmMetrics],
    current_algorithm: str | AlgorithmType,
    x: int,
    y: int,
    width: int,
    height: int,
) -> int:
    chart_rect = pygame.Rect(x, y, width, height)
    pygame.draw.rect(screen, (22, 26, 30), chart_rect)
    pygame.draw.rect(screen, (94, 105, 80), chart_rect, 2)

    gap = 10
    panel_width = (width - gap - 12) // 2
    left = pygame.Rect(x + 6, y + 6, panel_width, height - 44)
    right = pygame.Rect(left.right + gap, y + 6, panel_width, height - 12)
    right.height = left.height
    runtime_values = []
    memory_values = []
    for _label, algorithm in ALGORITHM_BUTTONS:
        metrics = metrics_by_algorithm.get(algorithm.value.lower())
        runtime_values.append(None if metrics is None else metrics.avg_time_ms)
        memory_values.append(None if metrics is None else metrics.last_memory_kb)

    selected_label = algorithm_label(current_algorithm)
    _draw_vertical_bar_chart(
        screen,
        font,
        left,
        "AVG MS (LOWER)",
        runtime_values,
        selected_label,
        _format_ms,
    )
    _draw_vertical_bar_chart(
        screen,
        font,
        right,
        "LAST KB (LOWER)",
        memory_values,
        selected_label,
        _format_kb,
    )
    note_lines = [
        "AVG MS: average pathfinding time.",
        "LAST KB: latest memory use. Lower bars are better.",
    ]
    note_y = chart_rect.bottom - 32
    for index, line in enumerate(note_lines):
        note = font.render(line, True, (154, 162, 146))
        screen.blit(note, (chart_rect.left + 8, note_y + index * 13))
    return y + height + 8


def _draw_vertical_bar_chart(
    screen: pygame.Surface,
    font: pygame.font.Font,
    rect: pygame.Rect,
    title: str,
    values: list[float | None],
    selected_label: str,
    formatter,
) -> None:
    pygame.draw.rect(screen, (27, 31, 35), rect)
    title_surface = font.render(title, True, (160, 175, 145))
    screen.blit(title_surface, (rect.left + 6, rect.top + 5))

    plot = pygame.Rect(rect.left + 6, rect.top + 28, rect.width - 12, rect.height - 52)
    pygame.draw.line(screen, (76, 84, 72), plot.bottomleft, plot.bottomright, 1)
    numeric_values = [value for value in values if value is not None]
    maximum = max(numeric_values, default=1.0)
    bar_gap = 5
    bar_width = max(8, (plot.width - bar_gap * 5) // 4)
    colors = [
        (89, 171, 116),
        (218, 164, 82),
        (86, 154, 207),
        (202, 105, 112),
    ]

    for index, ((label, _algorithm), value) in enumerate(
        zip(ALGORITHM_BUTTONS, values, strict=True)
    ):
        bar_x = plot.left + bar_gap + index * (bar_width + bar_gap)
        if value is not None and maximum > 0:
            bar_height = max(2, int((plot.height - 18) * value / maximum))
            bar = pygame.Rect(bar_x, plot.bottom - bar_height, bar_width, bar_height)
            pygame.draw.rect(screen, colors[index], bar)
            value_text = font.render(formatter(value), True, (224, 226, 207))
            value_x = bar.centerx - value_text.get_width() // 2
            screen.blit(value_text, (value_x, max(plot.top, bar.top - 14)))
        else:
            empty = pygame.Rect(bar_x, plot.bottom - 3, bar_width, 3)
            pygame.draw.rect(screen, (62, 68, 63), empty)

        compact_label = _compact_algorithm_label(label)
        label_color = (
            (252, 236, 178)
            if label == selected_label
            else (174, 182, 163)
        )
        label_surface = font.render(compact_label, True, label_color)
        screen.blit(
            label_surface,
            (bar_x + (bar_width - label_surface.get_width()) // 2, plot.bottom + 4),
        )


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
