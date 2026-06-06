import heapq

from ai.pathfinding.heuristic import manhattan
from ai.pathfinding.path_utils import reconstruct_path
from core.map_manager import MapManager
from utils.grid_utils import get_neighbors


def greedy(
    start: tuple[int, int],
    goal: tuple[int, int],
    map_manager: MapManager,
) -> list[tuple[int, int]]:
    if start == goal:
        return []

    frontier: list[tuple[int, tuple[int, int]]] = []
    heapq.heappush(frontier, (manhattan(start, goal), start))
    visited = {start}
    came_from: dict[tuple[int, int], tuple[int, int]] = {}

    while frontier:
        _, current = heapq.heappop(frontier)

        if current == goal:
            return reconstruct_path(came_from, start, goal)

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
            heapq.heappush(frontier, (manhattan(neighbor, goal), neighbor))

    return []
