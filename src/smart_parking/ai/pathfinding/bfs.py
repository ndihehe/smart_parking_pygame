from src.smart_parking.ai.pathfinding.base import Pathfinder


class BFSPathfinder(Pathfinder):
    def find_path(
        self,
        start: tuple[int, int],
        goal: tuple[int, int],
        grid: list[list[str]],
    ) -> list[tuple[int, int]]:
        pass

