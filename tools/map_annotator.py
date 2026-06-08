"""Pygame tool for annotating parking-map logic on top of a background image.

Run from the repository root:
    python tools/map_annotator.py
    python tools/map_annotator.py --tile-size 64

Controls:
    G/R/P/I/X/C/M  Select tile type
    Left click     Paint selected tile type
    Right click    Reset tile to X
    Tab            Toggle grid
    S              Save data/map_layout.json
    L              Load data/map_layout.json
    Arrow keys     Pan viewport
    Ctrl+arrows    Move grid offset by 1 px
    Ctrl+Shift+arrows Move grid offset by 8 px
    +/-            Zoom in/out
    0              Reset zoom and pan
    Esc            Quit
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import pygame


ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_IMAGE_PATH = Path("assets/maps/parking_map.png")
DEFAULT_LAYOUT_PATH = Path("data/map_layout.json")

WINDOW_SIZE = (1280, 800)
MIN_ZOOM = 0.35
MAX_ZOOM = 3.0
PAN_STEP = 48

TILE_TYPES = {
    "G": {
        "name": "gate",
        "color": (58, 190, 255),
        "text": (255, 255, 255),
        "walkable": True,
    },
    "R": {
        "name": "road",
        "color": (80, 210, 120),
        "text": (15, 30, 20),
        "walkable": True,
    },
    "P": {
        "name": "parking_slot",
        "color": (255, 214, 85),
        "text": (40, 30, 0),
        "walkable": True,
    },
    "I": {
        "name": "intersection",
        "color": (177, 132, 255),
        "text": (255, 255, 255),
        "walkable": True,
    },
    "X": {
        "name": "obstacle",
        "color": (235, 80, 80),
        "text": (255, 255, 255),
        "walkable": False,
    },
    "C": {
        "name": "car_parking_zone",
        "color": (255, 150, 60),
        "text": (45, 20, 0),
        "walkable": True,
    },
    "M": {
        "name": "motorbike_parking_zone",
        "color": (70, 230, 210),
        "text": (0, 40, 40),
        "walkable": True,
    },
}


class MapAnnotator:
    def __init__(self, image_path: Path, layout_path: Path, tile_size: int) -> None:
        pygame.init()
        pygame.display.set_caption("Smart Parking Map Annotator")

        self.screen = pygame.display.set_mode(WINDOW_SIZE, pygame.RESIZABLE)
        self.clock = pygame.time.Clock()

        self.image_path = image_path
        self.layout_path = layout_path
        self.tile_size = tile_size
        self.show_grid = True
        self.selected_type = "R"
        self.zoom = 1.0
        self.offset_x = 0
        self.offset_y = 0
        self.grid_offset_x = 0
        self.grid_offset_y = 0
        self.running = True

        self.background = self._load_background()
        self.image_width = self.background.get_width()
        self.image_height = self.background.get_height()
        self.cols = 0
        self.rows = 0
        self.grid: list[list[str]] = []
        self._rebuild_grid_dimensions()

        self.font = pygame.font.SysFont("consolas", 18, bold=True)
        self.small_font = pygame.font.SysFont("segoeui", 16)

    def _load_background(self) -> pygame.Surface:
        absolute_path = ROOT_DIR / self.image_path
        if not absolute_path.exists():
            raise FileNotFoundError(
                f"Không tìm thấy ảnh nền: {absolute_path}\n"
                "Hãy đặt ảnh tại assets/maps/parking_map.png hoặc truyền --image."
            )
        return pygame.image.load(str(absolute_path)).convert()

    def run(self) -> None:
        while self.running:
            self._handle_events()
            self._draw()
            self.clock.tick(60)
        pygame.quit()

    def _handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.VIDEORESIZE:
                self.screen = pygame.display.set_mode(event.size, pygame.RESIZABLE)
            elif event.type == pygame.KEYDOWN:
                self._handle_key(event.key, event.unicode.upper())
            elif event.type == pygame.MOUSEBUTTONDOWN:
                self._handle_mouse(event)

        pressed = pygame.key.get_pressed()
        if pygame.key.get_mods() & pygame.KMOD_CTRL:
            return
        if pressed[pygame.K_LEFT]:
            self.offset_x += PAN_STEP
        if pressed[pygame.K_RIGHT]:
            self.offset_x -= PAN_STEP
        if pressed[pygame.K_UP]:
            self.offset_y += PAN_STEP
        if pressed[pygame.K_DOWN]:
            self.offset_y -= PAN_STEP

    def _handle_key(self, key: int, text: str) -> None:
        if key == pygame.K_ESCAPE:
            self.running = False
        elif key in {pygame.K_LEFT, pygame.K_RIGHT, pygame.K_UP, pygame.K_DOWN} and pygame.key.get_mods() & pygame.KMOD_CTRL:
            self._move_grid_offset(key)
        elif key == pygame.K_TAB:
            self.show_grid = not self.show_grid
        elif key == pygame.K_s and not (pygame.key.get_mods() & pygame.KMOD_SHIFT):
            self.save_layout()
        elif key == pygame.K_l:
            self.load_layout()
        elif key in {pygame.K_PLUS, pygame.K_EQUALS, pygame.K_KP_PLUS}:
            self.zoom = min(MAX_ZOOM, self.zoom + 0.1)
        elif key in {pygame.K_MINUS, pygame.K_KP_MINUS}:
            self.zoom = max(MIN_ZOOM, self.zoom - 0.1)
        elif key == pygame.K_0:
            self.zoom = 1.0
            self.offset_x = 0
            self.offset_y = 0
            self.grid_offset_x = 0
            self.grid_offset_y = 0
            self._rebuild_grid_dimensions()
        elif text in TILE_TYPES:
            self.selected_type = text

    def _move_grid_offset(self, key: int) -> None:
        step = 8 if pygame.key.get_mods() & pygame.KMOD_SHIFT else 1
        if key == pygame.K_LEFT:
            self.grid_offset_x -= step
        elif key == pygame.K_RIGHT:
            self.grid_offset_x += step
        elif key == pygame.K_UP:
            self.grid_offset_y -= step
        elif key == pygame.K_DOWN:
            self.grid_offset_y += step

        limit = self.tile_size - 1
        self.grid_offset_x = max(-limit, min(limit, self.grid_offset_x))
        self.grid_offset_y = max(-limit, min(limit, self.grid_offset_y))
        self._rebuild_grid_dimensions()

    def _rebuild_grid_dimensions(self) -> None:
        old_grid = self.grid
        old_rows = len(old_grid)
        old_cols = len(old_grid[0]) if old_rows else 0

        self.cols = math.ceil((self.image_width - self.grid_offset_x) / self.tile_size)
        self.rows = math.ceil((self.image_height - self.grid_offset_y) / self.tile_size)
        self.cols = max(1, self.cols)
        self.rows = max(1, self.rows)

        new_grid = [["X" for _col in range(self.cols)] for _row in range(self.rows)]
        for row in range(min(old_rows, self.rows)):
            for col in range(min(old_cols, self.cols)):
                new_grid[row][col] = old_grid[row][col]
        self.grid = new_grid

    def _handle_mouse(self, event: pygame.event.Event) -> None:
        if event.button not in {1, 3}:
            return
        cell = self._screen_to_cell(event.pos)
        if cell is None:
            return
        row, col = cell
        self.grid[row][col] = self.selected_type if event.button == 1 else "X"

    def _screen_to_cell(self, position: tuple[int, int]) -> tuple[int, int] | None:
        screen_x, screen_y = position
        image_x = (screen_x - self.offset_x) / self.zoom
        image_y = (screen_y - self.offset_y) / self.zoom
        if image_x < 0 or image_y < 0 or image_x >= self.image_width or image_y >= self.image_height:
            return None
        grid_x = image_x - self.grid_offset_x
        grid_y = image_y - self.grid_offset_y
        if grid_x < 0 or grid_y < 0:
            return None
        col = int(grid_x // self.tile_size)
        row = int(grid_y // self.tile_size)
        if 0 <= row < self.rows and 0 <= col < self.cols:
            return row, col
        return None

    def _cell_to_screen_rect(self, row: int, col: int) -> pygame.Rect:
        image_x = self.grid_offset_x + col * self.tile_size
        image_y = self.grid_offset_y + row * self.tile_size
        x = int(image_x * self.zoom + self.offset_x)
        y = int(image_y * self.zoom + self.offset_y)
        tile_width = min(self.tile_size, self.image_width - image_x)
        tile_height = min(self.tile_size, self.image_height - image_y)
        width = max(1, int(tile_width * self.zoom))
        height = max(1, int(tile_height * self.zoom))
        return pygame.Rect(x, y, width, height)

    def _draw(self) -> None:
        self.screen.fill((18, 20, 28))
        scaled_width = int(self.image_width * self.zoom)
        scaled_height = int(self.image_height * self.zoom)
        scaled_background = pygame.transform.smoothscale(self.background, (scaled_width, scaled_height))
        self.screen.blit(scaled_background, (self.offset_x, self.offset_y))

        self._draw_annotations()
        if self.show_grid:
            self._draw_grid()
        self._draw_hud()
        pygame.display.flip()

    def _draw_annotations(self) -> None:
        for row in range(self.rows):
            for col in range(self.cols):
                tile_code = self.grid[row][col]
                if tile_code == "X":
                    continue
                rect = self._cell_to_screen_rect(row, col)
                if not self._is_visible(rect):
                    continue
                color = TILE_TYPES[tile_code]["color"]
                overlay = pygame.Surface(rect.size, pygame.SRCALPHA)
                overlay.fill((*color, 110))
                self.screen.blit(overlay, rect)

                label = self.font.render(tile_code, True, TILE_TYPES[tile_code]["text"])
                label_rect = label.get_rect(center=rect.center)
                self.screen.blit(label, label_rect)

    def _draw_grid(self) -> None:
        width, height = self.screen.get_size()
        grid_color = (0, 0, 0, 90)
        line_surface = pygame.Surface((width, height), pygame.SRCALPHA)
        step = self.tile_size * self.zoom
        if step < 4:
            return

        view_left = -self.offset_x / self.zoom
        view_right = (width - self.offset_x) / self.zoom
        view_top = -self.offset_y / self.zoom
        view_bottom = (height - self.offset_y) / self.zoom
        start_col = max(0, int((view_left - self.grid_offset_x) // self.tile_size) - 1)
        end_col = min(self.cols, int((view_right - self.grid_offset_x) // self.tile_size) + 2)
        start_row = max(0, int((view_top - self.grid_offset_y) // self.tile_size) - 1)
        end_row = min(self.rows, int((view_bottom - self.grid_offset_y) // self.tile_size) + 2)

        for col in range(start_col, end_col + 1):
            x = int((self.grid_offset_x + col * self.tile_size) * self.zoom + self.offset_x)
            pygame.draw.line(line_surface, grid_color, (x, 0), (x, height), 1)
        for row in range(start_row, end_row + 1):
            y = int((self.grid_offset_y + row * self.tile_size) * self.zoom + self.offset_y)
            pygame.draw.line(line_surface, grid_color, (0, y), (width, y), 1)
        self.screen.blit(line_surface, (0, 0))

    def _draw_hud(self) -> None:
        mouse_cell = self._screen_to_cell(pygame.mouse.get_pos())
        gate_count = sum(1 for row in self.grid for cell in row if cell == "G")
        slot_count = sum(1 for row in self.grid for cell in row if cell in {"P", "C", "M"})
        hud_lines = [
            f"Selected: {self.selected_type} ({TILE_TYPES[self.selected_type]['name']})",
            f"Tile: {self.tile_size}px | Grid: {self.cols}x{self.rows} | Zoom: {self.zoom:.1f}x",
            f"Grid offset: x={self.grid_offset_x}px y={self.grid_offset_y}px",
            f"Mouse cell: {mouse_cell if mouse_cell else '-'} | Gates: {gate_count} | Parking slots/zones: {slot_count}",
            "Keys: G R P I X C M | Left paint | Right reset | Tab | S save | L load | Ctrl+arrows align grid",
        ]
        padding = 10
        line_height = 22
        box_width = max(self.small_font.size(line)[0] for line in hud_lines) + padding * 2
        box_height = len(hud_lines) * line_height + padding * 2
        box = pygame.Surface((box_width, box_height), pygame.SRCALPHA)
        box.fill((12, 16, 24, 220))
        self.screen.blit(box, (10, 10))
        for index, line in enumerate(hud_lines):
            text = self.small_font.render(line, True, (235, 238, 245))
            self.screen.blit(text, (10 + padding, 10 + padding + index * line_height))

    def _is_visible(self, rect: pygame.Rect) -> bool:
        return rect.colliderect(self.screen.get_rect())

    def save_layout(self) -> None:
        absolute_path = ROOT_DIR / self.layout_path
        absolute_path.parent.mkdir(parents=True, exist_ok=True)
        payload = self._build_payload()
        absolute_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Đã lưu layout: {absolute_path}")

    def load_layout(self) -> None:
        absolute_path = ROOT_DIR / self.layout_path
        if not absolute_path.exists():
            print(f"Chưa có file layout để load: {absolute_path}")
            return

        payload = json.loads(absolute_path.read_text(encoding="utf-8"))
        loaded_tile_size = int(payload.get("tile_size", self.tile_size))
        loaded_grid_offset_x = int(payload.get("grid_offset_x", 0))
        loaded_grid_offset_y = int(payload.get("grid_offset_y", 0))
        loaded_grid = payload.get("grid")
        if loaded_tile_size != self.tile_size:
            print(
                f"Layout dùng tile_size={loaded_tile_size}, tool hiện dùng tile_size={self.tile_size}. "
                "Hãy chạy lại với --tile-size phù hợp."
            )
            return
        self.grid_offset_x = loaded_grid_offset_x
        self.grid_offset_y = loaded_grid_offset_y
        self._rebuild_grid_dimensions()
        if not self._is_valid_grid(loaded_grid):
            print("File layout không hợp lệ: grid sai kích thước hoặc chứa ký hiệu không hỗ trợ.")
            return

        self.grid = loaded_grid
        print(f"Đã load layout: {absolute_path}")

    def _build_payload(self) -> dict[str, Any]:
        gates = []
        parking_slots = []
        for row in range(self.rows):
            for col in range(self.cols):
                tile_type = self.grid[row][col]
                if tile_type == "G":
                    gates.append({"row": row, "col": col})
                elif tile_type in {"P", "C", "M"}:
                    parking_slots.append(
                        {
                            "row": row,
                            "col": col,
                            "type": TILE_TYPES[tile_type]["name"],
                        }
                    )

        return {
            "image_path": self.image_path.as_posix(),
            "tile_size": self.tile_size,
            "grid_offset_x": self.grid_offset_x,
            "grid_offset_y": self.grid_offset_y,
            "rows": self.rows,
            "cols": self.cols,
            "grid": self.grid,
            "gates": gates,
            "parking_slots": parking_slots,
        }

    def _is_valid_grid(self, grid: object) -> bool:
        if not isinstance(grid, list) or len(grid) != self.rows:
            return False
        for row in grid:
            if not isinstance(row, list) or len(row) != self.cols:
                return False
            if any(cell not in TILE_TYPES for cell in row):
                return False
        return True


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Annotate parking map logic over a map image.")
    parser.add_argument("--image", type=Path, default=DEFAULT_IMAGE_PATH, help="Path to map image, relative to repo root.")
    parser.add_argument(
        "--layout",
        type=Path,
        default=DEFAULT_LAYOUT_PATH,
        help="Path to JSON layout file, relative to repo root.",
    )
    parser.add_argument("--tile-size", type=int, choices=(32, 64), default=32, help="Grid tile size in pixels.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    annotator = MapAnnotator(args.image, args.layout, args.tile_size)
    annotator.run()


if __name__ == "__main__":
    main()
