import json
from pathlib import Path

from models.enums import CellType, VehicleType
from models.map_state import MapState
from models.parking_slot import ParkingSlot
from utils.grid_utils import get_neighbors
from utils.logger import Logger


class MapManager:
    def __init__(self) -> None:
        self.state = MapState(grid=[], rows=0, cols=0)

    def load_map(self, filepath: str) -> None:
        if filepath.lower().endswith(".json"):
            self._load_json_map(filepath)
        else:
            self._load_text_map(filepath)

    def _load_text_map(self, filepath: str) -> None:
        grid: list[list[CellType]] = []
        gate_cells: list[tuple[int, int]] = []
        parking_slots: dict[tuple[int, int], ParkingSlot] = {}
        static_obstacles: set[tuple[int, int]] = set()
        intersection_cells: list[tuple[int, int]] = []
        car_slots: list[tuple[int, int]] = []
        motorbike_slots: list[tuple[int, int]] = []

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
                    elif cell_type == CellType.INTERSECTION:
                        intersection_cells.append(position)
                    elif cell_type == CellType.PARKING_SLOT:
                        parking_slots[position] = ParkingSlot(position, None)
                        car_slots.append(position)
                        motorbike_slots.append(position)
                    elif cell_type == CellType.CAR_SLOT:
                        parking_slots[position] = ParkingSlot(position, VehicleType.CAR)
                        car_slots.append(position)
                    elif cell_type == CellType.MOTO_SLOT:
                        parking_slots[position] = ParkingSlot(position, VehicleType.MOTORBIKE)
                        motorbike_slots.append(position)
                    elif cell_type == CellType.OBSTACLE:
                        static_obstacles.add(position)

                grid.append(row)

        rows = len(grid)
        cols = len(grid[0]) if rows > 0 else 0
        last_col = cols - 1
        entry_gates = sorted(gate for gate in gate_cells if gate[1] == 0)[:2]
        exit_gates = sorted(gate for gate in gate_cells if gate[1] == last_col)[:2]
        intersection_neighbors = {
            position: get_neighbors(position, rows, cols)
            for position in intersection_cells
        }
        self.state = MapState(
            grid=grid,
            rows=rows,
            cols=cols,
            gate_cells=gate_cells,
            parking_slots=parking_slots,
            static_obstacles=static_obstacles,
            dynamic_blocks=set(),
            intersection_cells=intersection_cells,
            intersection_neighbors=intersection_neighbors,
            entry_gates=entry_gates,
            exit_gates=exit_gates,
            car_slots=car_slots,
            motorbike_slots=motorbike_slots,
        )
        self._validate_connectivity()
        Logger.log(f"[MapManager] Map loaded: {rows}x{cols}")

    def _load_json_map(self, filepath: str) -> None:
        path = Path(filepath)
        payload = json.loads(path.read_text(encoding="utf-8"))
        raw_grid = payload["grid"]
        grid: list[list[CellType]] = []
        gate_cells: list[tuple[int, int]] = []
        parking_slots: dict[tuple[int, int], ParkingSlot] = {}
        static_obstacles: set[tuple[int, int]] = set()
        intersection_cells: list[tuple[int, int]] = []
        car_slots: list[tuple[int, int]] = []
        motorbike_slots: list[tuple[int, int]] = []

        for row_index, raw_row in enumerate(raw_grid):
            row: list[CellType] = []
            for col_index, symbol in enumerate(raw_row):
                cell_type = CellType(symbol)
                position = (row_index, col_index)
                row.append(cell_type)

                if cell_type == CellType.GATE:
                    gate_cells.append(position)
                elif cell_type == CellType.INTERSECTION:
                    intersection_cells.append(position)
                elif cell_type == CellType.PARKING_SLOT:
                    parking_slots[position] = ParkingSlot(position, None)
                    car_slots.append(position)
                    motorbike_slots.append(position)
                elif cell_type == CellType.CAR_SLOT:
                    parking_slots[position] = ParkingSlot(position, VehicleType.CAR)
                    car_slots.append(position)
                elif cell_type == CellType.MOTO_SLOT:
                    parking_slots[position] = ParkingSlot(position, VehicleType.MOTORBIKE)
                    motorbike_slots.append(position)
                elif cell_type in {CellType.OBSTACLE, CellType.BLOCKED}:
                    static_obstacles.add(position)

            grid.append(row)

        rows = int(payload.get("rows", len(grid)))
        cols = int(payload.get("cols", len(grid[0]) if rows > 0 else 0))
        (
            parking_slots,
            car_slots,
            motorbike_slots,
            motorbike_outer_to_inner,
            motorbike_inner_to_outer,
        ) = self._build_reachable_parking_slots(
            grid,
            rows,
            cols,
        )
        last_col = cols - 1
        entry_gates = sorted(gate for gate in gate_cells if gate[1] == 0)[:4]
        exit_gates = sorted(gate for gate in gate_cells if gate[1] == last_col)[:4]
        if not entry_gates:
            entry_gates = sorted(gate_cells)[:4]
        if not exit_gates:
            exit_gates = sorted(gate_cells, reverse=True)[:4]

        intersection_neighbors = {
            position: get_neighbors(position, rows, cols)
            for position in intersection_cells
        }
        self.state = MapState(
            grid=grid,
            rows=rows,
            cols=cols,
            gate_cells=gate_cells,
            parking_slots=parking_slots,
            static_obstacles=static_obstacles,
            dynamic_blocks=set(),
            intersection_cells=intersection_cells,
            intersection_neighbors=intersection_neighbors,
            entry_gates=entry_gates,
            exit_gates=exit_gates,
            car_slots=car_slots,
            motorbike_slots=motorbike_slots,
            motorbike_outer_to_inner=motorbike_outer_to_inner,
            motorbike_inner_to_outer=motorbike_inner_to_outer,
            image_path=payload.get("image_path"),
            tile_size=int(payload.get("tile_size", 32)),
            grid_offset_x=int(payload.get("grid_offset_x", 0)),
            grid_offset_y=int(payload.get("grid_offset_y", 0)),
        )
        self._validate_connectivity()
        Logger.log(f"[MapManager] JSON map loaded: {rows}x{cols}")

    def _build_reachable_parking_slots(
        self,
        grid: list[list[CellType]],
        rows: int,
        cols: int,
    ) -> tuple[
        dict[tuple[int, int], ParkingSlot],
        list[tuple[int, int]],
        list[tuple[int, int]],
        dict[tuple[int, int], tuple[int, int]],
        dict[tuple[int, int], tuple[int, int]],
    ]:
        parking_slots: dict[tuple[int, int], ParkingSlot] = {}
        car_slots: list[tuple[int, int]] = []
        motorbike_slots: list[tuple[int, int]] = []
        motorbike_outer_to_inner: dict[tuple[int, int], tuple[int, int]] = {}
        motorbike_inner_to_outer: dict[tuple[int, int], tuple[int, int]] = {}
        drive_types = {CellType.GATE, CellType.ROAD, CellType.INTERSECTION}
        motorbike_cells = {
            (row_index, col_index)
            for row_index, row in enumerate(grid)
            for col_index, cell_type in enumerate(row)
            if cell_type == CellType.MOTO_SLOT
        }

        for row_index, row in enumerate(grid):
            for col_index, cell_type in enumerate(row):
                if cell_type not in {
                    CellType.PARKING_SLOT,
                    CellType.CAR_SLOT,
                    CellType.MOTO_SLOT,
                }:
                    continue

                position = (row_index, col_index)
                touches_drive_cell = any(
                    grid[neighbor_row][neighbor_col] in drive_types
                    for neighbor_row, neighbor_col in get_neighbors(position, rows, cols)
                )
                if cell_type == CellType.PARKING_SLOT:
                    if not touches_drive_cell:
                        continue
                    parking_slots[position] = ParkingSlot(position, None)
                    car_slots.append(position)
                    motorbike_slots.append(position)
                elif cell_type == CellType.CAR_SLOT:
                    if not touches_drive_cell:
                        continue
                    parking_slots[position] = ParkingSlot(position, VehicleType.CAR)
                    car_slots.append(position)
                elif cell_type == CellType.MOTO_SLOT:
                    if not touches_drive_cell:
                        continue
                    parking_slots[position] = ParkingSlot(position, VehicleType.MOTORBIKE)
                    motorbike_slots.append(position)
                    inner_slot = self._find_inner_motorbike_slot(
                        position,
                        motorbike_cells,
                        grid,
                        rows,
                        cols,
                        drive_types,
                    )
                    if inner_slot is not None and inner_slot not in parking_slots:
                        parking_slots[inner_slot] = ParkingSlot(inner_slot, VehicleType.MOTORBIKE)
                        motorbike_slots.append(inner_slot)
                        motorbike_outer_to_inner[position] = inner_slot
                        motorbike_inner_to_outer[inner_slot] = position

        return (
            parking_slots,
            car_slots,
            motorbike_slots,
            motorbike_outer_to_inner,
            motorbike_inner_to_outer,
        )

    def _find_inner_motorbike_slot(
        self,
        outer_slot: tuple[int, int],
        motorbike_cells: set[tuple[int, int]],
        grid: list[list[CellType]],
        rows: int,
        cols: int,
        drive_types: set[CellType],
    ) -> tuple[int, int] | None:
        inner_candidates: list[tuple[int, int]] = []
        for neighbor in get_neighbors(outer_slot, rows, cols):
            if neighbor not in motorbike_cells:
                continue
            touches_drive = any(
                grid[neighbor_row][neighbor_col] in drive_types
                for neighbor_row, neighbor_col in get_neighbors(neighbor, rows, cols)
            )
            if not touches_drive:
                inner_candidates.append(neighbor)

        if not inner_candidates:
            return None

        return min(inner_candidates, key=lambda item: (item[0], item[1]))

    def get_state(self) -> MapState:
        return self.state

    def add_dynamic_block(self, position: tuple[int, int]) -> None:
        self.state.dynamic_blocks.add(position)
        Logger.log(f"[MapManager] Dynamic block added at {position}")

    def remove_dynamic_block(self, position: tuple[int, int]) -> None:
        self.state.dynamic_blocks.discard(position)
        Logger.log(f"[MapManager] Dynamic block removed at {position}")

    def is_passable(self, position: tuple[int, int]) -> bool:
        return self.is_drive_cell(position)

    def is_drive_cell(self, position: tuple[int, int]) -> bool:
        row, col = position
        if not (0 <= row < self.state.rows and 0 <= col < self.state.cols):
            return False

        passable_types = {
            CellType.ROAD,
            CellType.INTERSECTION,
            CellType.GATE,
        }
        return (
            self.state.grid[row][col] in passable_types
            and position not in self.state.static_obstacles
            and position not in self.state.dynamic_blocks
        )

    def is_parking_cell(self, position: tuple[int, int]) -> bool:
        row, col = position
        if not (0 <= row < self.state.rows and 0 <= col < self.state.cols):
            return False
        return self.state.grid[row][col] in {
            CellType.PARKING_SLOT,
            CellType.CAR_SLOT,
            CellType.MOTO_SLOT,
        }

    def can_vehicle_enter(self, position: tuple[int, int]) -> bool:
        return (
            self.is_drive_cell(position)
            or (
                position in self.state.parking_slots
                and position not in self.state.static_obstacles
                and position not in self.state.dynamic_blocks
            )
        )

    def get_cell_at_pixel(self, x: int, y: int) -> tuple[int, int] | None:
        grid_x = x - self.state.grid_offset_x
        grid_y = y - self.state.grid_offset_y
        if grid_x < 0 or grid_y < 0:
            return None
        row = grid_y // self.state.tile_size
        col = grid_x // self.state.tile_size
        if 0 <= row < self.state.rows and 0 <= col < self.state.cols:
            return row, col
        return None

    def get_pixel_center(self, row: int, col: int) -> tuple[int, int]:
        return (
            self.state.grid_offset_x + col * self.state.tile_size + self.state.tile_size // 2,
            self.state.grid_offset_y + row * self.state.tile_size + self.state.tile_size // 2,
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
            reaches_slot = position in reachable or any(
                neighbor in reachable
                for neighbor in get_neighbors(position, self.state.rows, self.state.cols)
            )
            outer_slot = self.state.motorbike_inner_to_outer.get(position)
            if outer_slot is not None:
                reaches_slot = reaches_slot or outer_slot in reachable or any(
                    neighbor in reachable
                    for neighbor in get_neighbors(outer_slot, self.state.rows, self.state.cols)
                )
            if not reaches_slot:
                Logger.log(f"[MapManager] WARNING: slot {position} is not reachable")

        count = len(reachable)
        Logger.log(f"[MapManager] Connectivity check done. Reachable cells: {count}")
