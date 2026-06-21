from __future__ import annotations

import math
import struct
import zlib
from pathlib import Path


TILE_SIZE = 64
PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / "assets" / "maps" / "tiles"

ASPHALT = (68, 72, 74, 255)
ASPHALT_DARK = (48, 52, 54, 255)
FLOOR = (112, 116, 114, 255)
WHITE = (232, 232, 224, 255)
YELLOW = (232, 190, 40, 255)
CYAN = (40, 224, 236, 255)
RED = (224, 40, 36, 255)
BLACK = (22, 24, 26, 255)
TRANSPARENT = (0, 0, 0, 0)

Color = tuple[int, int, int, int]


class Image:
    def __init__(self, width: int = TILE_SIZE, height: int = TILE_SIZE, color: Color = TRANSPARENT) -> None:
        self.width = width
        self.height = height
        self.pixels = bytearray(width * height * 4)
        self.fill(color)

    def fill(self, color: Color) -> None:
        self.pixels[:] = bytes(color) * (self.width * self.height)

    def set_pixel(self, x: int, y: int, color: Color) -> None:
        if not (0 <= x < self.width and 0 <= y < self.height):
            return
        index = (y * self.width + x) * 4
        self.pixels[index : index + 4] = bytes(color)

    def save(self, path: Path) -> None:
        raw = bytearray()
        stride = self.width * 4
        for y in range(self.height):
            raw.append(0)
            row_start = y * stride
            raw.extend(self.pixels[row_start : row_start + stride])

        def chunk(tag: bytes, data: bytes) -> bytes:
            return (
                struct.pack(">I", len(data))
                + tag
                + data
                + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
            )

        png = (
            b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", self.width, self.height, 8, 6, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
            + chunk(b"IEND", b"")
        )
        path.write_bytes(png)


def clamp_color(base: Color, delta: int) -> Color:
    return (
        max(0, min(255, base[0] + delta)),
        max(0, min(255, base[1] + delta)),
        max(0, min(255, base[2] + delta)),
        base[3],
    )


def rect(img: Image, x: int, y: int, width: int, height: int, color: Color) -> None:
    for yy in range(y, y + height):
        for xx in range(x, x + width):
            img.set_pixel(xx, yy, color)


def rect_outline(img: Image, x: int, y: int, width: int, height: int, color: Color, thickness: int) -> None:
    rect(img, x, y, width, thickness, color)
    rect(img, x, y + height - thickness, width, thickness, color)
    rect(img, x, y, thickness, height, color)
    rect(img, x + width - thickness, y, thickness, height, color)


def line(img: Image, x1: int, y1: int, x2: int, y2: int, color: Color, thickness: int = 1) -> None:
    dx = abs(x2 - x1)
    dy = -abs(y2 - y1)
    sx = 1 if x1 < x2 else -1
    sy = 1 if y1 < y2 else -1
    err = dx + dy
    radius = max(0, thickness // 2)
    x, y = x1, y1
    while True:
        rect(img, x - radius, y - radius, thickness, thickness, color)
        if x == x2 and y == y2:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x += sx
        if e2 <= dx:
            err += dx
            y += sy


def circle(img: Image, cx: int, cy: int, radius: int, color: Color) -> None:
    radius_sq = radius * radius
    for y in range(cy - radius, cy + radius + 1):
        for x in range(cx - radius, cx + radius + 1):
            if (x - cx) * (x - cx) + (y - cy) * (y - cy) <= radius_sq:
                img.set_pixel(x, y, color)


def polygon(img: Image, points: list[tuple[int, int]], color: Color) -> None:
    min_y = min(y for _, y in points)
    max_y = max(y for _, y in points)
    for y in range(min_y, max_y + 1):
        nodes: list[int] = []
        previous = points[-1]
        for current in points:
            x1, y1 = previous
            x2, y2 = current
            if (y1 < y <= y2) or (y2 < y <= y1):
                nodes.append(int(x1 + (y - y1) * (x2 - x1) / (y2 - y1)))
            previous = current
        nodes.sort()
        for index in range(0, len(nodes), 2):
            if index + 1 >= len(nodes):
                break
            for x in range(nodes[index], nodes[index + 1] + 1):
                img.set_pixel(x, y, color)


def asphalt(base: Color = ASPHALT) -> Image:
    img = Image(color=base)
    for x in range(0, TILE_SIZE, 8):
        for y in range(0, TILE_SIZE, 8):
            delta = ((x * 17 + y * 11) % 19) - 9
            rect(img, x, y, 8, 8, clamp_color(base, delta))
    for index in range(42):
        x = (index * 23 + 7) % TILE_SIZE
        y = (index * 37 + 11) % TILE_SIZE
        shade = 84 + (index * 13) % 32
        rect(img, x, y, 2, 2, (shade, shade, shade, 255))
    return img


def save(img: Image, name: str) -> None:
    img.save(OUTPUT_DIR / name)


def draw_marker(img: Image, directions: set[str]) -> None:
    center = (32, 32)
    endpoints = {
        "north": (32, 0),
        "south": (32, 63),
        "west": (0, 32),
        "east": (63, 32),
    }
    for direction in directions:
        line(img, center[0], center[1], endpoints[direction][0], endpoints[direction][1], WHITE, 4)
    circle(img, 32, 32, 3, WHITE)


def dashed_line(img: Image, vertical: bool) -> None:
    for start in range(0, 64, 18):
        end = min(start + 10, 63)
        if vertical:
            line(img, 32, start, 32, end, WHITE, 4)
        else:
            line(img, start, 32, end, 32, WHITE, 4)


def create_base_tiles() -> None:
    road = asphalt(ASPHALT)
    save(road, "road_plain.png")
    save(road, "road_straight.png")
    save(asphalt(FLOOR), "floor_empty.png")

    obstacle = asphalt(ASPHALT_DARK)
    rect(obstacle, 8, 18, 48, 28, (172, 174, 166, 255))
    rect(obstacle, 12, 20, 40, 24, (92, 122, 62, 255))
    for x, y, radius, color in (
        (20, 27, 8, (70, 150, 70, 255)),
        (31, 25, 9, (82, 168, 76, 255)),
        (42, 30, 8, (52, 132, 66, 255)),
        (28, 37, 7, (62, 142, 58, 255)),
    ):
        circle(obstacle, x, y, radius, color)
    save(obstacle, "obstacle_wall.png")


def create_road_tiles() -> None:
    variants = {
        "road_horizontal.png": {"west", "east"},
        "road_vertical.png": {"north", "south"},
        "road_turn_ne.png": {"north", "east"},
        "road_turn_nw.png": {"north", "west"},
        "road_turn_se.png": {"south", "east"},
        "road_turn_sw.png": {"south", "west"},
        "road_t_north.png": {"west", "east", "north"},
        "road_t_south.png": {"west", "east", "south"},
        "road_t_east.png": {"north", "south", "east"},
        "road_t_west.png": {"north", "south", "west"},
        "road_cross.png": {"north", "south", "west", "east"},
        "road_intersection.png": {"north", "south", "west", "east"},
    }
    for name, directions in variants.items():
        img = asphalt(ASPHALT)
        draw_marker(img, directions)
        save(img, name)


def create_parking_tiles() -> None:
    car = asphalt(ASPHALT)
    rect_outline(car, 10, 8, 44, 48, WHITE, 4)
    rect(car, 10, 30, 8, 4, WHITE)
    rect(car, 46, 30, 8, 4, WHITE)
    save(car, "car_parking_slot.png")

    single = asphalt(ASPHALT)
    rect_outline(single, 22, 10, 20, 44, YELLOW, 4)
    save(single, "motorbike_parking_single.png")

    outer_h = asphalt(ASPHALT)
    line(outer_h, 8, 18, 63, 18, YELLOW, 4)
    line(outer_h, 8, 46, 63, 46, YELLOW, 4)
    line(outer_h, 8, 18, 8, 46, YELLOW, 4)
    save(outer_h, "motorbike_parking_outer_horizontal.png")
    save(outer_h, "motorbike_parking_outer.png")

    inner_h = asphalt(ASPHALT)
    line(inner_h, 0, 18, 56, 18, YELLOW, 4)
    line(inner_h, 0, 46, 56, 46, YELLOW, 4)
    line(inner_h, 56, 18, 56, 46, YELLOW, 4)
    save(inner_h, "motorbike_parking_inner_horizontal.png")
    save(inner_h, "motorbike_parking_inner.png")

    outer_v = asphalt(ASPHALT)
    line(outer_v, 18, 8, 18, 63, YELLOW, 4)
    line(outer_v, 46, 8, 46, 63, YELLOW, 4)
    line(outer_v, 18, 8, 46, 8, YELLOW, 4)
    save(outer_v, "motorbike_parking_outer_vertical.png")

    inner_v = asphalt(ASPHALT)
    line(inner_v, 18, 0, 18, 56, YELLOW, 4)
    line(inner_v, 46, 0, 46, 56, YELLOW, 4)
    line(inner_v, 18, 56, 46, 56, YELLOW, 4)
    save(inner_v, "motorbike_parking_inner_vertical.png")


def draw_gate(img: Image, arrow: str, barrier_color: Color) -> None:
    if arrow == "right":
        polygon(img, [(42, 32), (28, 20), (28, 28), (14, 28), (14, 36), (28, 36), (28, 44)], WHITE)
        rect(img, 8, 10, 6, 44, barrier_color)
        rect_outline(img, 8, 10, 6, 44, BLACK, 1)
        for y in range(12, 52, 12):
            line(img, 9, y, 13, y + 8, YELLOW, 2)
    else:
        polygon(img, [(22, 32), (36, 20), (36, 28), (50, 28), (50, 36), (36, 36), (36, 44)], WHITE)
        rect(img, 50, 10, 6, 44, barrier_color)
        rect_outline(img, 50, 10, 6, 44, BLACK, 1)
        for y in range(12, 52, 12):
            line(img, 51, y, 55, y + 8, YELLOW, 2)


def create_gate_tiles() -> None:
    for name, arrow, color in (
        ("gate_entry_left.png", "right", RED),
        ("gate_entry_right.png", "left", RED),
        ("gate_exit_left.png", "left", YELLOW),
        ("gate_exit_right.png", "right", YELLOW),
    ):
        img = asphalt(ASPHALT_DARK)
        draw_gate(img, arrow, color)
        save(img, name)
    generic_entry = asphalt(ASPHALT_DARK)
    draw_gate(generic_entry, "right", RED)
    save(generic_entry, "gate_entry.png")
    generic_exit = asphalt(ASPHALT_DARK)
    draw_gate(generic_exit, "right", YELLOW)
    save(generic_exit, "gate_exit.png")


def create_overlays() -> None:
    horizontal = Image(color=TRANSPARENT)
    dashed_line(horizontal, vertical=False)
    save(horizontal, "lane_marker_horizontal.png")

    vertical = Image(color=TRANSPARENT)
    dashed_line(vertical, vertical=True)
    save(vertical, "lane_marker_vertical.png")

    selected = Image(color=TRANSPARENT)
    rect_outline(selected, 4, 4, 56, 56, CYAN, 4)
    save(selected, "parking_slot_selected_overlay.png")

    blocked = Image(color=TRANSPARENT)
    line(blocked, 12, 12, 52, 52, RED, 6)
    line(blocked, 52, 12, 12, 52, RED, 6)
    save(blocked, "blocked_overlay.png")


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    create_base_tiles()
    create_road_tiles()
    create_parking_tiles()
    create_gate_tiles()
    create_overlays()
    print(f"Generated map tiles in {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
