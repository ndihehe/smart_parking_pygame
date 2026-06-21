from __future__ import annotations

import json
from pathlib import Path


TILE_SIZE = 48
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_PATH = PROJECT_ROOT / "data" / "maps" / "default_map.txt"
OUTPUT_PATH = PROJECT_ROOT / "data" / "map_layout.json"
VALID_SYMBOLS = {".", "T", "L", "R", "I", "G", "C", "M", "P", "X", "B"}


def load_grid() -> list[list[str]]:
    grid = [
        line.split()
        for line in SOURCE_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if not grid:
        raise ValueError(f"Map is empty: {SOURCE_PATH}")
    column_count = len(grid[0])
    if any(len(row) != column_count for row in grid):
        raise ValueError("Every map row must contain the same number of cells")
    invalid_symbols = sorted({cell for row in grid for cell in row} - VALID_SYMBOLS)
    if invalid_symbols:
        raise ValueError(f"Unknown map symbols: {', '.join(invalid_symbols)}")
    return grid


def main() -> None:
    grid = load_grid()
    rows = len(grid)
    cols = len(grid[0])
    payload = {
        "image_path": "assets/maps/parking_map_20x20.png",
        "tile_size": TILE_SIZE,
        "grid_offset_x": 0,
        "grid_offset_y": 0,
        "rows": rows,
        "cols": cols,
        "grid": grid,
    }
    OUTPUT_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
