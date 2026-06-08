import heapq

from ai.pathfinding.heuristic import manhattan
from ai.pathfinding.path_utils import reconstruct_path
from core.map_manager import MapManager
from utils.grid_utils import get_neighbors


def astar(
    start: tuple[int, int],
    goal: tuple[int, int],
    map_manager: MapManager,
    blocked_positions: set[tuple[int, int]] | None = None,
) -> list[tuple[int, int]]:
    if start == goal:
        return []
    blocked_positions = blocked_positions or set()

    frontier: list[tuple[int, tuple[int, int]]] = []
    heapq.heappush(frontier, (manhattan(start, goal), start))
    came_from: dict[tuple[int, int], tuple[int, int]] = {}
    cost_so_far: dict[tuple[int, int], int] = {start: 0}

    while frontier:
        _, current = heapq.heappop(frontier)

        if current == goal:
            return reconstruct_path(came_from, start, goal)

        for neighbor in get_neighbors(
            current,
            map_manager.state.rows,
            map_manager.state.cols,
        ):
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

            new_cost = cost_so_far[current] + 1
            if neighbor not in cost_so_far or new_cost < cost_so_far[neighbor]:
                cost_so_far[neighbor] = new_cost
                priority = new_cost + manhattan(neighbor, goal)
                heapq.heappush(frontier, (priority, neighbor))
                came_from[neighbor] = current

    return []
