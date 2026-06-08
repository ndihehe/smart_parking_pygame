import pygame

from models.map_state import MapState


PANEL_MIN_WIDTH = 320
PANEL_MAX_WIDTH = 480
MIN_VIEWPORT_WIDTH = 320


def map_pixel_size(map_state: MapState) -> tuple[int, int]:
    return map_state.cols * map_state.tile_size, map_state.rows * map_state.tile_size


def get_control_panel_rect(
    screen_size: tuple[int, int],
    map_state: MapState | None = None,
) -> pygame.Rect:
    screen_width, screen_height = screen_size
    if screen_width <= MIN_VIEWPORT_WIDTH + PANEL_MIN_WIDTH:
        panel_width = max(0, screen_width - MIN_VIEWPORT_WIDTH)
    else:
        if map_state is None:
            map_aspect = 4 / 3
        else:
            map_width, map_height = map_pixel_size(map_state)
            map_aspect = map_width / map_height
        ideal_panel_width = screen_width - int(screen_height * map_aspect)
        panel_width = max(PANEL_MIN_WIDTH, min(PANEL_MAX_WIDTH, ideal_panel_width))
        panel_width = min(panel_width, screen_width - MIN_VIEWPORT_WIDTH)
    return pygame.Rect(screen_width - panel_width, 0, panel_width, screen_height)


def get_game_viewport_rect(
    screen_size: tuple[int, int],
    map_state: MapState | None = None,
) -> pygame.Rect:
    panel_rect = get_control_panel_rect(screen_size, map_state)
    return pygame.Rect(0, 0, panel_rect.left, screen_size[1])


def get_map_view_rect(map_state: MapState, screen_size: tuple[int, int]) -> pygame.Rect:
    map_width, map_height = map_pixel_size(map_state)
    viewport_rect = get_game_viewport_rect(screen_size, map_state)
    scale = min(viewport_rect.width / map_width, viewport_rect.height / map_height)
    scaled_width = max(1, int(map_width * scale))
    scaled_height = max(1, int(map_height * scale))
    return pygame.Rect(
        viewport_rect.left,
        viewport_rect.top + max(0, (viewport_rect.height - scaled_height) // 2),
        scaled_width,
        scaled_height,
    )


def screen_to_map_pixel(
    map_state: MapState,
    screen_size: tuple[int, int],
    position: tuple[int, int],
) -> tuple[int, int] | None:
    view_rect = get_map_view_rect(map_state, screen_size)
    if not view_rect.collidepoint(position):
        return None

    map_width, map_height = map_pixel_size(map_state)
    scale_x = map_width / view_rect.width
    scale_y = map_height / view_rect.height
    x = int((position[0] - view_rect.left) * scale_x)
    y = int((position[1] - view_rect.top) * scale_y)
    return x, y
