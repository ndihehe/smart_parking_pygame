from config import CONGESTION_PENALTY, OBSTACLE_PENALTY
from models.enums import CellType
from models.map_state import MapState
from models.vehicle import Vehicle
from utils.grid_utils import get_neighbors, manhattan_distance
from utils.logger import Logger


class ParkingManager:
    def __init__(self) -> None:
        pass

    def find_slot(self, vehicle: Vehicle, map_state: MapState) -> tuple[int, int] | None:
        best_position: tuple[int, int] | None = None
        best_score: float | None = None

        for position, slot in map_state.parking_slots.items():
            if slot.slot_type != vehicle.type:
                continue
            if slot.is_occupied:
                continue
            if position in map_state.dynamic_blocks:
                continue

            neighbors = get_neighbors(slot.position, map_state.rows, map_state.cols)
            distance = manhattan_distance(vehicle.position, slot.position)
            congestion_penalty = (
                CONGESTION_PENALTY
                if any(neighbor in map_state.dynamic_blocks for neighbor in neighbors)
                else 0
            )
            obstacle_penalty = (
                OBSTACLE_PENALTY
                if any(neighbor in map_state.static_obstacles for neighbor in neighbors)
                else 0
            )
            score = distance + congestion_penalty + obstacle_penalty

            if best_score is None or score < best_score:
                best_position = position
                best_score = score

        if best_position is None or best_score is None:
            Logger.log(f"[ParkingManager] Vehicle #{vehicle.id} no valid slot found")
            return None

        Logger.log(
            f"[ParkingManager] Vehicle #{vehicle.id} assigned slot "
            f"{best_position} (score={best_score:.1f})"
        )
        return best_position

    def assign_slot(
        self,
        vehicle: Vehicle,
        position: tuple[int, int],
        map_state: MapState,
    ) -> None:
        map_state.parking_slots[position].is_occupied = True
        map_state.parking_slots[position].occupied_by = vehicle.id
        vehicle.assigned_slot = position

    def release_slot(self, position: tuple[int, int], map_state: MapState) -> None:
        map_state.parking_slots[position].is_occupied = False
        map_state.parking_slots[position].occupied_by = None
        Logger.log(f"[ParkingManager] Slot {position} released")

    def validate_parking(self, vehicle: Vehicle, map_state: MapState) -> str:
        position = vehicle.position
        slot = map_state.parking_slots.get(position)

        if slot is not None:
            if slot.slot_type == vehicle.type and position == vehicle.assigned_slot:
                return "OK"
            if slot.slot_type == vehicle.type and position != vehicle.assigned_slot:
                Logger.log(
                    f"[ParkingManager] Vehicle #{vehicle.id} parked at different "
                    f"slot {position}"
                )
                return "DIFFERENT_SLOT"
            Logger.log(
                f"[ParkingManager] Vehicle #{vehicle.id} invalid slot type at {position}"
            )
            return "WRONG_TYPE"

        row, col = position
        cell_type = map_state.grid[row][col]
        if cell_type == CellType.ROAD:
            Logger.log(
                f"[ParkingManager] Vehicle #{vehicle.id} illegal parking on road "
                f"at {position}"
            )
            return "ILLEGAL_ROAD"
        if cell_type == CellType.INTERSECTION:
            Logger.log(
                f"[ParkingManager] Vehicle #{vehicle.id} blocking intersection "
                f"at {position}"
            )
            return "BLOCKING_INTERSECTION"

        return "UNKNOWN"
