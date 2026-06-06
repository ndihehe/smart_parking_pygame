from abc import ABC, abstractmethod


class Pathfinder(ABC):
    @abstractmethod
    def find_path(
        self,
        start: tuple[int, int],
        goal: tuple[int, int],
        grid: list[list[str]],
    ) -> list[tuple[int, int]]:
        pass

