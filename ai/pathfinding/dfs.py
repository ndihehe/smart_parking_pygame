from ai.pathfinding.path_utils import reconstruct_path
from core.map_manager import MapManager
from utils.grid_utils import get_neighbors


def dfs(
    start: tuple[int, int],
    goal: tuple[int, int],
    map_manager: MapManager,
    blocked_positions: set[tuple[int, int]] | None = None,
) -> list[tuple[int, int]]:
    if start == goal:
        return []
    blocked_positions = blocked_positions or set()

    stack = [start]
    visited = set()
    came_from: dict[tuple[int, int], tuple[int, int]] = {}

    while stack:
        current = stack.pop()
        if current in visited:
            continue

        visited.add(current)

        if current == goal:
            return reconstruct_path(came_from, start, goal)

        for neighbor in get_neighbors(
            current,
            map_manager.state.rows,
            map_manager.state.cols,
        ):
            if neighbor in visited:
                continue
            if neighbor != goal and not map_manager.is_passable(neighbor):
                continue
            if neighbor in blocked_positions and neighbor not in (start, goal):
                continue
            slot = map_manager.state.parking_slots.get(neighbor)
            if (
                slot is not None
                and neighbor != goal
                and (slot.is_reserved or slot.is_occupied)
            ):
                continue
            if neighbor not in came_from:
                came_from[neighbor] = current
            stack.append(neighbor)

    return []
