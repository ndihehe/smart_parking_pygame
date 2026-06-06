from models.enums import CellType, VehicleType
from models.map_state import MapState
from models.parking_slot import ParkingSlot
from utils.grid_utils import get_neighbors
from utils.logger import Logger


class MapManager:
    def __init__(self) -> None:
        self.state = MapState(grid=[], rows=0, cols=0)

    def load_map(self, filepath: str) -> None:
        grid: list[list[CellType]] = []
        gate_cells: list[tuple[int, int]] = []
        parking_slots: dict[tuple[int, int], ParkingSlot] = {}
        static_obstacles: set[tuple[int, int]] = set()

        with open(filepath, "r", encoding="utf-8") as map_file:
            for row_index, line in enumerate(map_file):
                symbols = line.strip().split()
                row: list[CellType] = []
                for col_index, symbol in enumerate(symbols):
                    cell_type = CellType(symbol)
                    position = (row_index, col_index)
                    row.append(cell_type)

                    if cell_type == CellType.GATE:
                        gate_cells.append(position)
                    elif cell_type == CellType.CAR_SLOT:
                        parking_slots[position] = ParkingSlot(position, VehicleType.CAR)
                    elif cell_type == CellType.MOTO_SLOT:
                        parking_slots[position] = ParkingSlot(position, VehicleType.MOTORBIKE)
                    elif cell_type == CellType.OBSTACLE:
                        static_obstacles.add(position)

                grid.append(row)

        rows = len(grid)
        cols = len(grid[0]) if rows > 0 else 0
        self.state = MapState(
            grid=grid,
            rows=rows,
            cols=cols,
            gate_cells=gate_cells,
            parking_slots=parking_slots,
            static_obstacles=static_obstacles,
            dynamic_blocks=set(),
        )
        self._validate_connectivity()
        Logger.log(f"[MapManager] Map loaded: {rows}x{cols}")

    def get_state(self) -> MapState:
        return self.state

    def add_dynamic_block(self, position: tuple[int, int]) -> None:
        self.state.dynamic_blocks.add(position)
        Logger.log(f"[MapManager] Dynamic block added at {position}")

    def remove_dynamic_block(self, position: tuple[int, int]) -> None:
        self.state.dynamic_blocks.discard(position)
        Logger.log(f"[MapManager] Dynamic block removed at {position}")

    def is_passable(self, position: tuple[int, int]) -> bool:
        row, col = position
        if not (0 <= row < self.state.rows and 0 <= col < self.state.cols):
            return False

        passable_types = {
            CellType.ROAD,
            CellType.INTERSECTION,
            CellType.GATE,
            CellType.CAR_SLOT,
            CellType.MOTO_SLOT,
        }
        return (
            self.state.grid[row][col] in passable_types
            and position not in self.state.static_obstacles
            and position not in self.state.dynamic_blocks
        )

    def _validate_connectivity(self) -> None:
        if not self.state.gate_cells:
            Logger.log("[MapManager] Connectivity check done. Reachable cells: 0")
            return

        start = self.state.gate_cells[0]
        stack = [start]
        reachable: set[tuple[int, int]] = set()

        while stack:
            current = stack.pop()
            if current in reachable:
                continue
            if not self.is_passable(current):
                continue

            reachable.add(current)
            for neighbor in get_neighbors(current, self.state.rows, self.state.cols):
                if neighbor not in reachable and self.is_passable(neighbor):
                    stack.append(neighbor)

        for position in self.state.parking_slots:
            if position not in reachable:
                Logger.log(f"[MapManager] WARNING: slot {position} is not reachable")

        count = len(reachable)
        Logger.log(f"[MapManager] Connectivity check done. Reachable cells: {count}")
