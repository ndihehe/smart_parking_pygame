from ai.pathfinding.astar import astar
from ai.pathfinding.bfs import bfs
from ai.pathfinding.dfs import dfs
from ai.pathfinding.greedy import greedy
from core.map_manager import MapManager
from models.enums import AlgorithmType


def find_path(
    algorithm: str | AlgorithmType,
    start: tuple[int, int],
    goal: tuple[int, int],
    map_manager: MapManager,
    blocked_positions: set[tuple[int, int]] | None = None,
) -> list[tuple[int, int]]:
    algorithm_name = normalize_algorithm_name(algorithm)
    algorithms = {
        "bfs": bfs,
        "dfs": dfs,
        "greedy": greedy,
        "astar": astar,
    }
    pathfinder = algorithms[algorithm_name]
    return pathfinder(start, goal, map_manager, blocked_positions)


def normalize_algorithm_name(algorithm: str | AlgorithmType) -> str:
    if isinstance(algorithm, AlgorithmType):
        return algorithm.value.lower()

    algorithm_name = algorithm.strip().lower()
    aliases = {
        "a*": "astar",
        "a_star": "astar",
        "greedy_best_first": "greedy",
        "greedy_best_first_search": "greedy",
    }
    algorithm_name = aliases.get(algorithm_name, algorithm_name)

    if algorithm_name not in {"bfs", "dfs", "greedy", "astar"}:
        raise ValueError(f"Unknown pathfinding algorithm: {algorithm}")

    return algorithm_name
