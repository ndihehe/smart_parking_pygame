from src.smart_parking.models.map_state import MapState


class MapManager:
    def __init__(self) -> None:
        self.state = MapState()

    def load_map(self, path: str) -> None:
        pass

    def generate_map(self, rows: int, cols: int) -> None:
        pass

    def validate_connectivity(self) -> bool:
        pass

    def add_dynamic_block(self, cell: tuple[int, int]) -> None:
        pass

    def remove_dynamic_block(self, cell: tuple[int, int]) -> None:
        pass

    def is_walkable(self, cell: tuple[int, int]) -> bool:
        pass

