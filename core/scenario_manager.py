from collections.abc import Iterable

from core.map_manager import MapManager
from core.simulation_state import VehiclePlan
from models.enums import VehicleType
from models.map_state import MapState
from utils.grid_utils import get_neighbors


ScenarioVehicle = tuple[VehicleType, tuple[int, int], VehiclePlan]


class ScenarioManager:
    def __init__(self, map_manager: MapManager) -> None:
        self.map_manager = map_manager

    def build_traffic_jam(self) -> list[ScenarioVehicle]:
        map_state = self.map_manager.get_state()
        center = self._find_best_congestion_center(map_state)
        drive_cells = self._nearby_drive_cells(center, map_state)
        if len(drive_cells) < 6:
            drive_cells = self._all_drive_cells(map_state)

        selected = drive_cells[:8]
        plans = [
            VehiclePlan.ENTERING,
            VehiclePlan.EXITING,
            VehiclePlan.ENTERING,
            VehiclePlan.EXITING,
            VehiclePlan.ENTERING,
            VehiclePlan.EXITING,
            VehiclePlan.ENTERING,
            VehiclePlan.EXITING,
        ]
        types = [
            VehicleType.CAR,
            VehicleType.CAR,
            VehicleType.MOTORBIKE,
            VehicleType.CAR,
            VehicleType.MOTORBIKE,
            VehicleType.CAR,
            VehicleType.CAR,
            VehicleType.MOTORBIKE,
        ]
        return [
            (vehicle_type, position, plan)
            for vehicle_type, position, plan in zip(types, selected, plans, strict=False)
        ]

    def _find_best_congestion_center(self, map_state: MapState) -> tuple[int, int]:
        if map_state.intersection_cells:
            center_row = map_state.rows // 2
            center_col = map_state.cols // 2
            return max(
                map_state.intersection_cells,
                key=lambda position: (
                    self._drive_degree(position, map_state),
                    -abs(position[0] - center_row) - abs(position[1] - center_col),
                    position[0],
                    position[1],
                ),
            )
        drive_cells = self._all_drive_cells(map_state)
        if not drive_cells:
            return (0, 0)
        return drive_cells[len(drive_cells) // 2]

    def _nearby_drive_cells(
        self,
        center: tuple[int, int],
        map_state: MapState,
    ) -> list[tuple[int, int]]:
        candidates = self._all_drive_cells(map_state)
        return sorted(
            candidates,
            key=lambda position: (
                abs(position[0] - center[0]) + abs(position[1] - center[1]),
                position,
            ),
        )[:18]

    def _all_drive_cells(self, map_state: MapState) -> list[tuple[int, int]]:
        return [
            (row, col)
            for row in range(map_state.rows)
            for col in range(map_state.cols)
            if self.map_manager.is_drive_cell((row, col))
        ]

    def _drive_degree(
        self,
        position: tuple[int, int],
        map_state: MapState,
    ) -> int:
        return sum(
            1
            for neighbor in get_neighbors(position, map_state.rows, map_state.cols)
            if self.map_manager.is_drive_cell(neighbor)
        )

    def _spread_positions(
        self,
        positions: Iterable[tuple[int, int]],
        limit: int,
    ) -> list[tuple[int, int]]:
        selected: list[tuple[int, int]] = []
        for position in positions:
            if any(self._are_adjacent(position, other) for other in selected):
                continue
            selected.append(position)
            if len(selected) == limit:
                return selected
        for position in positions:
            if position not in selected:
                selected.append(position)
            if len(selected) == limit:
                break
        return selected

    def _are_adjacent(
        self,
        first: tuple[int, int],
        second: tuple[int, int],
    ) -> bool:
        return second in get_neighbors(
            first,
            self.map_manager.get_state().rows,
            self.map_manager.get_state().cols,
        )
