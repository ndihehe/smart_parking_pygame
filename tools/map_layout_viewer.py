"""View the map image with saved layout annotations.

Run from the repository root:
    python tools/map_layout_viewer.py

Controls:
    Tab         Toggle grid
    L          Toggle labels
    Arrow keys Pan
    +/-        Zoom in/out
    0          Reset zoom and pan
    Esc        Quit
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pygame


ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_LAYOUT_PATH = Path("data/map_layout.json")
WINDOW_SIZE = (1280, 800)
MIN_ZOOM = 0.35
MAX_ZOOM = 3.0
PAN_STEP = 48

TILE_STYLES = {
    "G": ((58, 190, 255), (255, 255, 255), "Gate"),
    "R": ((80, 210, 120), (15, 30, 20), "Road"),
    "P": ((255, 214, 85), (40, 30, 0), "Parking"),
    "I": ((177, 132, 255), (255, 255, 255), "Intersection"),
    "X": ((235, 80, 80), (255, 255, 255), "Obstacle"),
    "C": ((255, 150, 60), (45, 20, 0), "Car slot"),
    "M": ((70, 230, 210), (0, 40, 40), "Motorbike slot"),
}


class MapLayoutViewer:
    def __init__(self, layout_path: Path) -> None:
        pygame.init()
        pygame.display.set_caption("Smart Parking Map Layout Viewer")
        self.screen = pygame.display.set_mode(WINDOW_SIZE, pygame.RESIZABLE)
        self.clock = pygame.time.Clock()
        self.layout_path = layout_path
        self.payload = self._load_layout()
        self.tile_size = int(self.payload["tile_size"])
        self.grid_offset_x = int(self.payload.get("grid_offset_x", 0))
        self.grid_offset_y = int(self.payload.get("grid_offset_y", 0))
        self.grid: list[list[str]] = self.payload["grid"]
        self.rows = int(self.payload.get("rows", len(self.grid)))
        self.cols = int(self.payload.get("cols", len(self.grid[0]) if self.grid else 0))
        self.background = self._load_background()
        self.image_width = self.background.get_width()
        self.image_height = self.background.get_height()
        self.zoom = 1.0
        self.offset_x = 0
        self.offset_y = 0
        self.show_grid = True
        self.show_labels = True
        self.running = True
        self.font = pygame.font.SysFont("consolas", 18, bold=True)
        self.small_font = pygame.font.SysFont("segoeui", 16)

    def _load_layout(self) -> dict[str, Any]:
        absolute_path = ROOT_DIR / self.layout_path
        if not absolute_path.exists():
            raise FileNotFoundError(f"Không tìm thấy layout: {absolute_path}")
        return json.loads(absolute_path.read_text(encoding="utf-8"))

    def _load_background(self) -> pygame.Surface:
        image_path = Path(self.payload["image_path"])
        if not image_path.is_absolute():
            image_path = ROOT_DIR / image_path
        if not image_path.exists():
            raise FileNotFoundError(f"Không tìm thấy ảnh nền: {image_path}")
        return pygame.image.load(str(image_path)).convert()

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
                self._handle_key(event.key)

        pressed = pygame.key.get_pressed()
        if pressed[pygame.K_LEFT]:
            self.offset_x += PAN_STEP
        if pressed[pygame.K_RIGHT]:
            self.offset_x -= PAN_STEP
        if pressed[pygame.K_UP]:
            self.offset_y += PAN_STEP
        if pressed[pygame.K_DOWN]:
            self.offset_y -= PAN_STEP

    def _handle_key(self, key: int) -> None:
        if key == pygame.K_ESCAPE:
            self.running = False
        elif key == pygame.K_TAB:
            self.show_grid = not self.show_grid
        elif key == pygame.K_l:
            self.show_labels = not self.show_labels
        elif key in {pygame.K_PLUS, pygame.K_EQUALS, pygame.K_KP_PLUS}:
            self.zoom = min(MAX_ZOOM, self.zoom + 0.1)
        elif key in {pygame.K_MINUS, pygame.K_KP_MINUS}:
            self.zoom = max(MIN_ZOOM, self.zoom - 0.1)
        elif key == pygame.K_0:
            self.zoom = 1.0
            self.offset_x = 0
            self.offset_y = 0

    def _draw(self) -> None:
        self.screen.fill((18, 20, 28))
        scaled_size = (
            int(self.image_width * self.zoom),
            int(self.image_height * self.zoom),
        )
        scaled_background = pygame.transform.smoothscale(self.background, scaled_size)
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
                style = TILE_STYLES.get(tile_code)
                if style is None:
                    continue
                rect = self._cell_to_screen_rect(row, col)
                if not rect.colliderect(self.screen.get_rect()):
                    continue
                color, text_color, _name = style
                overlay = pygame.Surface(rect.size, pygame.SRCALPHA)
                overlay.fill((*color, 105))
                self.screen.blit(overlay, rect)
                if self.show_labels:
                    label = self.font.render(tile_code, True, text_color)
                    self.screen.blit(label, label.get_rect(center=rect.center))

    def _draw_grid(self) -> None:
        width, height = self.screen.get_size()
        line_surface = pygame.Surface((width, height), pygame.SRCALPHA)
        line_color = (0, 0, 0, 90)
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
            pygame.draw.line(line_surface, line_color, (x, 0), (x, height), 1)
        for row in range(start_row, end_row + 1):
            y = int((self.grid_offset_y + row * self.tile_size) * self.zoom + self.offset_y)
            pygame.draw.line(line_surface, line_color, (0, y), (width, y), 1)
        self.screen.blit(line_surface, (0, 0))

    def _draw_hud(self) -> None:
        counts = {
            code: sum(1 for row in self.grid for cell in row if cell == code)
            for code in TILE_STYLES
        }
        hud_lines = [
            f"Layout: {self.layout_path.as_posix()} | Grid: {self.cols}x{self.rows} | Tile: {self.tile_size}px | Zoom: {self.zoom:.1f}x",
            " ".join(f"{code}:{counts[code]}" for code in TILE_STYLES),
            "Keys: Tab grid | L labels | Arrows pan | +/- zoom | 0 reset | Esc quit",
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

    def _cell_to_screen_rect(self, row: int, col: int) -> pygame.Rect:
        image_x = self.grid_offset_x + col * self.tile_size
        image_y = self.grid_offset_y + row * self.tile_size
        tile_width = min(self.tile_size, self.image_width - image_x)
        tile_height = min(self.tile_size, self.image_height - image_y)
        return pygame.Rect(
            int(image_x * self.zoom + self.offset_x),
            int(image_y * self.zoom + self.offset_y),
            max(1, int(tile_width * self.zoom)),
            max(1, int(tile_height * self.zoom)),
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="View map layout annotations.")
    parser.add_argument(
        "--layout",
        type=Path,
        default=DEFAULT_LAYOUT_PATH,
        help="Path to JSON layout file, relative to repo root.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    MapLayoutViewer(args.layout).run()


if __name__ == "__main__":
    main()
