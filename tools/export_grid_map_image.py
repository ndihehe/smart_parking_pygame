from __future__ import annotations

import json
from pathlib import Path

import pygame


PROJECT_ROOT = Path(__file__).resolve().parents[1]
LAYOUT_PATH = PROJECT_ROOT / "data" / "map_layout.json"
OUTPUT_PATH = PROJECT_ROOT / "assets" / "maps" / "parking_map_16x16_pixel.png"

ASPHALT = (54, 58, 60)
ASPHALT_DARK = (43, 46, 48)
ROAD_MARK = (226, 226, 214)
GRASS = (89, 139, 55)
GRASS_DARK = (58, 107, 49)
GRASS_LIGHT = (116, 162, 70)
WALL = (112, 116, 106)
CAR_SLOT = (60, 132, 208)
CAR_LINE = (230, 242, 255)
MOTO_SLOT = (220, 179, 38)
MOTO_LINE = (255, 245, 178)
GATE_YELLOW = (236, 190, 44)
GATE_RED = (222, 60, 48)
CURB = (164, 148, 112)


def draw_noise_tile(surface: pygame.Surface, rect: pygame.Rect, base: tuple[int, int, int]) -> None:
    pygame.draw.rect(surface, base, rect)
    for y in range(rect.top, rect.bottom, 8):
        for x in range(rect.left, rect.right, 8):
            delta = ((x * 17 + y * 11) % 17) - 8
            color = tuple(max(0, min(255, channel + delta)) for channel in base)
            pygame.draw.rect(surface, color, (x, y, min(8, rect.right - x), min(8, rect.bottom - y)))


def draw_grass(surface: pygame.Surface, rect: pygame.Rect, row: int, col: int) -> None:
    draw_noise_tile(surface, rect, GRASS)
    seed = row * 31 + col * 17
    if seed % 4 == 0:
        cx = rect.centerx + (seed % 9) - 4
        cy = rect.centery + ((seed // 3) % 9) - 4
        pygame.draw.circle(surface, GRASS_DARK, (cx, cy), rect.width // 5)
        pygame.draw.circle(surface, GRASS_LIGHT, (cx - 3, cy - 3), rect.width // 6)
    elif seed % 5 == 0:
        wall = rect.inflate(-8, -rect.height // 2)
        wall.centery = rect.centery
        pygame.draw.rect(surface, WALL, wall, border_radius=2)
        pygame.draw.rect(surface, GRASS_DARK, wall.inflate(-6, -4), border_radius=2)


def draw_road(surface: pygame.Surface, rect: pygame.Rect, directions: set[str], intersection: bool = False) -> None:
    draw_noise_tile(surface, rect, ASPHALT if not intersection else ASPHALT_DARK)
    center = rect.center
    half = rect.width // 2
    dash = max(5, rect.width // 5)
    if "west" in directions:
        pygame.draw.line(surface, ROAD_MARK, (rect.left + 5, center[1]), (center[0] - dash, center[1]), 3)
    if "east" in directions:
        pygame.draw.line(surface, ROAD_MARK, (center[0] + dash, center[1]), (rect.right - 5, center[1]), 3)
    if "north" in directions:
        pygame.draw.line(surface, ROAD_MARK, (center[0], rect.top + 5), (center[0], center[1] - dash), 3)
    if "south" in directions:
        pygame.draw.line(surface, ROAD_MARK, (center[0], center[1] + dash), (center[0], rect.bottom - 5), 3)
    if intersection:
        pygame.draw.rect(surface, (92, 96, 98), rect.inflate(-8, -8), 1)
    pygame.draw.rect(surface, (36, 38, 40), rect, 1)
    _ = half


def draw_car_slot(surface: pygame.Surface, rect: pygame.Rect) -> None:
    draw_noise_tile(surface, rect, CAR_SLOT)
    inner = rect.inflate(-8, -8)
    pygame.draw.rect(surface, CAR_LINE, inner, 3, border_radius=2)
    pygame.draw.line(surface, CAR_LINE, (inner.left + 8, inner.centery), (inner.left + 18, inner.centery), 3)
    pygame.draw.line(surface, CAR_LINE, (inner.right - 18, inner.centery), (inner.right - 8, inner.centery), 3)
    pygame.draw.rect(surface, (35, 82, 142), rect, 1)


def draw_motorbike_slot(surface: pygame.Surface, rect: pygame.Rect) -> None:
    draw_noise_tile(surface, rect, MOTO_SLOT)
    inner = rect.inflate(-12, -8)
    pygame.draw.rect(surface, MOTO_LINE, inner, 3, border_radius=2)
    pygame.draw.line(surface, MOTO_LINE, (rect.centerx, inner.top + 6), (rect.centerx, inner.bottom - 6), 3)
    pygame.draw.circle(surface, MOTO_LINE, (rect.centerx, inner.top + 9), 3)
    pygame.draw.circle(surface, MOTO_LINE, (rect.centerx, inner.bottom - 9), 3)
    pygame.draw.rect(surface, (146, 109, 24), rect, 1)


def draw_gate(surface: pygame.Surface, rect: pygame.Rect, left_side: bool) -> None:
    draw_noise_tile(surface, rect, ASPHALT_DARK)
    post_x = rect.left + 6 if left_side else rect.right - 12
    pygame.draw.rect(surface, GATE_YELLOW, (post_x, rect.top + 8, 6, rect.height - 16))
    if left_side:
        pygame.draw.line(surface, GATE_RED, (post_x + 5, rect.centery), (rect.right - 4, rect.centery - 12), 5)
    else:
        pygame.draw.line(surface, GATE_RED, (post_x, rect.centery), (rect.left + 4, rect.centery - 12), 5)
    pygame.draw.rect(surface, (30, 30, 28), rect, 1)


def drive_directions(grid: list[list[str]], row: int, col: int) -> set[str]:
    rows = len(grid)
    cols = len(grid[0]) if rows else 0
    drive = {"R", "I", "G"}
    directions: set[str] = set()
    for name, rr, cc in (
        ("north", row - 1, col),
        ("south", row + 1, col),
        ("west", row, col - 1),
        ("east", row, col + 1),
    ):
        if 0 <= rr < rows and 0 <= cc < cols and grid[rr][cc] in drive:
            directions.add(name)
    if not directions:
        directions = {"west", "east"}
    return directions


def main() -> None:
    payload = json.loads(LAYOUT_PATH.read_text(encoding="utf-8"))
    grid = payload["grid"]
    rows = int(payload["rows"])
    cols = int(payload["cols"])
    tile_size = int(payload["tile_size"])

    pygame.init()
    surface = pygame.Surface((cols * tile_size, rows * tile_size))

    for row_index, row in enumerate(grid):
        for col_index, cell in enumerate(row):
            rect = pygame.Rect(
                col_index * tile_size,
                row_index * tile_size,
                tile_size,
                tile_size,
            )
            if cell == "R":
                draw_road(surface, rect, drive_directions(grid, row_index, col_index))
            elif cell == "I":
                draw_road(surface, rect, drive_directions(grid, row_index, col_index), intersection=True)
            elif cell == "G":
                draw_gate(surface, rect, col_index == 0)
            elif cell == "C":
                draw_car_slot(surface, rect)
            elif cell == "M":
                draw_motorbike_slot(surface, rect)
            else:
                draw_grass(surface, rect, row_index, col_index)

            if cell in {"R", "I", "G"}:
                continue
            pygame.draw.rect(surface, CURB, rect, 1)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    pygame.image.save(surface, OUTPUT_PATH)
    pygame.quit()
    print(f"Wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
