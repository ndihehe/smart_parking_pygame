from config import CELL_SIZE


def get_neighbors(position: tuple[int, int], rows: int, cols: int) -> list[tuple[int, int]]:
    row, col = position
    candidates = [
        (row - 1, col),
        (row + 1, col),
        (row, col - 1),
        (row, col + 1),
    ]
    return [
        candidate
        for candidate in candidates
        if is_within_bounds(candidate, rows, cols)
    ]


def manhattan_distance(a: tuple[int, int], b: tuple[int, int]) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def is_within_bounds(position: tuple[int, int], rows: int, cols: int) -> bool:
    row, col = position
    return 0 <= row < rows and 0 <= col < cols


def cell_to_pixel(position: tuple[int, int]) -> tuple[int, int]:
    row, col = position
    return col * CELL_SIZE, row * CELL_SIZE
