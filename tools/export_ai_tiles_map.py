from __future__ import annotations

import json
from pathlib import Path

import pygame


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MAPS_DIR = PROJECT_ROOT / "assets" / "maps"
LAYOUT_PATH = PROJECT_ROOT / "data" / "map_layout.json"
OUTPUT_PATH = MAPS_DIR / "parking_map_20x20.png"

ASSET_NAMES = {
    "asphalt": "asphalt_tile.png",
    "grass": "grass_tile.png",
    "bush": "bush_tile.png",
    "tree": "tree_tile.png",
    "gate": "gate_barrier_tile.png",
    "car_slot": "car_parking_slot_tile.png",
    "motorbike_vertical": "motorbike_parking_vertical_tile.png",
    "lamp": "street_lamp_tile.png",
}


def remove_near_white(surface: pygame.Surface) -> pygame.Surface:
    converted = surface.copy()
    converted.lock()
    for y in range(converted.get_height()):
        for x in range(converted.get_width()):
            r, g, b, a = converted.get_at((x, y))
            if a and r > 225 and g > 225 and b > 225:
                converted.set_at((x, y), (r, g, b, 0))
    converted.unlock()
    return converted


def load_tile(name: str, tile_size: int, clear_white: bool = False) -> pygame.Surface:
    image = pygame.image.load(str(MAPS_DIR / ASSET_NAMES[name])).convert_alpha()
    if clear_white:
        image = remove_near_white(image)
    return pygame.transform.smoothscale(image, (tile_size, tile_size))


def load_object_tile(name: str, tile_size: int) -> pygame.Surface:
    image = pygame.image.load(str(MAPS_DIR / ASSET_NAMES[name])).convert_alpha()
    image = remove_near_white(image)
    bounds = image.get_bounding_rect(min_alpha=16)
    image = image.subsurface(bounds).copy()
    scale = min((tile_size - 4) / image.get_width(), (tile_size - 4) / image.get_height())
    size = (
        max(1, int(image.get_width() * scale)),
        max(1, int(image.get_height() * scale)),
    )
    scaled = pygame.transform.smoothscale(image, size)
    tile = pygame.Surface((tile_size, tile_size), pygame.SRCALPHA)
    tile.blit(scaled, scaled.get_rect(center=tile.get_rect().center))
    return tile


def draw_road_marks(
    surface: pygame.Surface,
    rect: pygame.Rect,
    grid: list[list[str]],
    row: int,
    col: int,
) -> None:
    drive = {"R", "I", "G"}
    rows = len(grid)
    cols = len(grid[0])
    horizontal = (
        (col > 0 and grid[row][col - 1] in drive)
        or (col + 1 < cols and grid[row][col + 1] in drive)
    )
    vertical = (
        (row > 0 and grid[row - 1][col] in drive)
        or (row + 1 < rows and grid[row + 1][col] in drive)
    )
    if horizontal == vertical:
        return

    cx, cy = rect.center
    color = (230, 230, 218)
    half_dash = max(5, rect.width // 7)
    if horizontal and col % 2 == 0:
        pygame.draw.line(surface, color, (cx - half_dash, cy), (cx + half_dash, cy), 2)
    elif vertical and row % 2 == 0:
        pygame.draw.line(surface, color, (cx, cy - half_dash), (cx, cy + half_dash), 2)


def has_neighbor_type(
    grid: list[list[str]],
    row: int,
    col: int,
    cell_types: set[str],
) -> bool:
    rows = len(grid)
    cols = len(grid[0])
    for row_delta, col_delta in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        neighbor_row = row + row_delta
        neighbor_col = col + col_delta
        if not (0 <= neighbor_row < rows and 0 <= neighbor_col < cols):
            continue
        if grid[neighbor_row][neighbor_col] in cell_types:
            return True
    return False


def draw_empty_tile(
    surface: pygame.Surface,
    rect: pygame.Rect,
    tiles: dict[str, pygame.Surface],
    grid: list[list[str]],
    row: int,
    col: int,
) -> None:
    pygame.draw.rect(surface, (75, 132, 54), rect)
    surface.blit(tiles["grass"], rect)

    near_drive_or_slot = has_neighbor_type(grid, row, col, {"R", "I", "G", "C", "M"})
    if near_drive_or_slot:
        return

    if (row * 17 + col * 31) % 13 == 0:
        surface.blit(tiles["tree"], rect)
    elif (row * 13 + col * 19) % 11 == 0:
        surface.blit(tiles["bush"], rect)


def main() -> None:
    pygame.init()
    pygame.display.set_mode((1, 1), flags=pygame.HIDDEN)

    payload = json.loads(LAYOUT_PATH.read_text(encoding="utf-8"))
    grid = payload["grid"]
    rows = int(payload["rows"])
    cols = int(payload["cols"])
    tile_size = int(payload["tile_size"])

    tiles = {
        key: load_tile(key, tile_size, clear_white=key in {"grass", "bush", "tree"})
        for key in ASSET_NAMES
        if key != "lamp"
    }
    tiles["lamp"] = load_object_tile("lamp", tile_size)
    surface = pygame.Surface((cols * tile_size, rows * tile_size))
    surface.fill((75, 132, 54))

    for row_index, row in enumerate(grid):
        for col_index, cell in enumerate(row):
            rect = pygame.Rect(
                col_index * tile_size,
                row_index * tile_size,
                tile_size,
                tile_size,
            )
            if cell in {"R", "I"}:
                pygame.draw.rect(surface, (44, 47, 49), rect)
                surface.blit(tiles["asphalt"], rect)
                if cell == "R":
                    draw_road_marks(surface, rect, grid, row_index, col_index)
            elif cell == "G":
                pygame.draw.rect(surface, (44, 47, 49), rect)
                surface.blit(tiles["gate"], rect)
            elif cell == "C":
                pygame.draw.rect(surface, (44, 47, 49), rect)
                surface.blit(tiles["car_slot"], rect)
            elif cell == "M":
                pygame.draw.rect(surface, (44, 47, 49), rect)
                surface.blit(tiles["motorbike_vertical"], rect)
            elif cell == "T":
                pygame.draw.rect(surface, (75, 132, 54), rect)
                surface.blit(tiles["grass"], rect)
                surface.blit(tiles["tree"], rect)
            elif cell == "L":
                pygame.draw.rect(surface, (75, 132, 54), rect)
                surface.blit(tiles["grass"], rect)
                surface.blit(tiles["lamp"], rect)
            else:
                draw_empty_tile(surface, rect, tiles, grid, row_index, col_index)

    pygame.image.save(surface, OUTPUT_PATH)
    pygame.quit()
    print(f"Wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
