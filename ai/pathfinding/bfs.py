from collections import deque

from ai.pathfinding.path_utils import reconstruct_path
from core.map_manager import MapManager
from utils.grid_utils import get_neighbors


def bfs(
    start: tuple[int, int],
    goal: tuple[int, int],
    map_manager: MapManager,
) -> list[tuple[int, int]]:
    if start == goal:
        return []

    frontier = deque([start])
    visited = {start}
    came_from: dict[tuple[int, int], tuple[int, int]] = {}

    while frontier:
        current = frontier.popleft()

        for neighbor in get_neighbors(
            current,
            map_manager.state.rows,
            map_manager.state.cols,
        ):
            if neighbor in visited:
                continue
            if not map_manager.is_passable(neighbor):
                continue

            visited.add(neighbor)
            came_from[neighbor] = current

            if neighbor == goal:
                return reconstruct_path(came_from, start, goal)

            frontier.append(neighbor)

    return []
