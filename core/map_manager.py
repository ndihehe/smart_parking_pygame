from core.simulation_state import SimulationState


class MapManager:
    def __init__(self, state: SimulationState) -> None:
        self.state = state

    def load_map(self, path: str) -> None:
        pass

    def validate_map(self) -> bool:
        pass

    def get_cell(self, row: int, col: int) -> str | None:
        pass

    def is_cell_walkable(self, row: int, col: int) -> bool:
        pass

