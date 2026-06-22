from collections import deque

from core.map_manager import MapManager
from models.enums import CellType
from utils.grid_utils import get_neighbors


def find_guard_path(
    start: tuple[int, int],
    goal: tuple[int, int],
    map_manager: MapManager,
    blocked_positions: set[tuple[int, int]] | None = None,
) -> list[tuple[int, int]]:
    """Find a walking route that may cross roads and every parking slot."""
    if start == goal:
        return []

    state = map_manager.get_state()
    blocked_positions = blocked_positions or set()
    walkable_types = {
        CellType.GATE,
        CellType.ROAD,
        CellType.INTERSECTION,
        CellType.PARKING_SLOT,
        CellType.CAR_SLOT,
        CellType.MOTO_SLOT,
    }
    frontier = deque([start])
    came_from: dict[tuple[int, int], tuple[int, int]] = {}
    visited = {start}

    while frontier:
        current = frontier.popleft()
        for neighbor in get_neighbors(current, state.rows, state.cols):
            if neighbor in visited:
                continue
            if neighbor != goal and neighbor in blocked_positions:
                continue
            row, col = neighbor
            if state.grid[row][col] not in walkable_types:
                continue
            if neighbor in state.static_obstacles:
                continue

            came_from[neighbor] = current
            if neighbor == goal:
                path = [goal]
                while path[-1] != start:
                    path.append(came_from[path[-1]])
                path.reverse()
                return path[1:]

            visited.add(neighbor)
            frontier.append(neighbor)

    return []
