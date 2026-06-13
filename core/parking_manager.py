from ai.decision.slot_scoring import score_slot
from models.enums import CellType, VehicleType
from models.map_state import MapState
from models.vehicle import Vehicle
from utils.logger import Logger


class ParkingManager:
    def find_slot(self, vehicle: Vehicle, map_state: MapState) -> tuple[int, int] | None:
        best_position: tuple[int, int] | None = None
        best_score: float | None = None

        slot_positions = (
            map_state.car_slots
            if vehicle.type == VehicleType.CAR
            else map_state.motorbike_slots
        )

        for position in slot_positions:
            slot = map_state.parking_slots[position]
            if slot.is_occupied:
                continue
            if slot.is_reserved and slot.reserved_by != vehicle.id:
                continue
            if not self._motorbike_access_available(vehicle, position, map_state):
                continue
            if position in map_state.dynamic_blocks:
                continue

            score = score_slot(vehicle, slot.position, map_state)
            if (
                vehicle.type == VehicleType.MOTORBIKE
                and position in map_state.motorbike_inner_to_outer
            ):
                score -= 1000

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
        if vehicle.assigned_slot is not None and vehicle.assigned_slot != position:
            self.release_vehicle_slot(vehicle, map_state)
        map_state.parking_slots[position].is_reserved = True
        map_state.parking_slots[position].reserved_by = vehicle.id
        if vehicle.type == VehicleType.MOTORBIKE and position in map_state.motorbike_inner_to_outer:
            outer_position = map_state.motorbike_inner_to_outer[position]
            outer_slot = map_state.parking_slots.get(outer_position)
            if outer_slot is not None and not outer_slot.is_occupied:
                outer_slot.is_reserved = True
                outer_slot.reserved_by = vehicle.id
        vehicle.assigned_slot = position

    def release_slot(self, position: tuple[int, int], map_state: MapState) -> None:
        map_state.parking_slots[position].is_reserved = False
        map_state.parking_slots[position].reserved_by = None
        map_state.parking_slots[position].is_occupied = False
        map_state.parking_slots[position].occupied_by = None
        Logger.log(f"[ParkingManager] Slot {position} released")

    def release_vehicle_slot(self, vehicle: Vehicle, map_state: MapState) -> None:
        if vehicle.assigned_slot is None:
            return
        self._release_access_reservation(vehicle, map_state)
        slot = map_state.parking_slots.get(vehicle.assigned_slot)
        if slot is not None:
            if slot.reserved_by == vehicle.id:
                slot.is_reserved = False
                slot.reserved_by = None
            if slot.occupied_by == vehicle.id:
                slot.is_occupied = False
                slot.occupied_by = None
        vehicle.assigned_slot = None

    def occupy_slot(
        self,
        vehicle: Vehicle,
        position: tuple[int, int],
        map_state: MapState,
    ) -> None:
        slot = map_state.parking_slots[position]
        self._release_access_reservation(vehicle, map_state)
        slot.is_reserved = False
        slot.reserved_by = None
        slot.is_occupied = True
        slot.occupied_by = vehicle.id
        vehicle.assigned_slot = position

    def _motorbike_access_available(
        self,
        vehicle: Vehicle,
        position: tuple[int, int],
        map_state: MapState,
    ) -> bool:
        if vehicle.type != VehicleType.MOTORBIKE:
            return True

        outer_position = map_state.motorbike_inner_to_outer.get(position)
        if outer_position is None:
            return True

        outer_slot = map_state.parking_slots.get(outer_position)
        if outer_slot is None:
            return False

        return (
            not outer_slot.is_occupied
            and (
                not outer_slot.is_reserved
                or outer_slot.reserved_by == vehicle.id
            )
        )

    def _release_access_reservation(self, vehicle: Vehicle, map_state: MapState) -> None:
        assigned_slot = vehicle.assigned_slot
        if assigned_slot is None:
            return

        outer_position = map_state.motorbike_inner_to_outer.get(assigned_slot)
        if outer_position is None:
            return

        outer_slot = map_state.parking_slots.get(outer_position)
        if outer_slot is not None and outer_slot.reserved_by == vehicle.id and not outer_slot.is_occupied:
            outer_slot.is_reserved = False
            outer_slot.reserved_by = None

    def validate_parking(self, vehicle: Vehicle, map_state: MapState) -> str:
        position = vehicle.position
        slot = map_state.parking_slots.get(position)

        if slot is not None:
            type_matches = slot.slot_type is None or slot.slot_type == vehicle.type
            if type_matches and position == vehicle.assigned_slot:
                Logger.log(
                    f"[ParkingManager] Vehicle #{vehicle.id} parking validation OK "
                    f"at assigned slot {position}"
                )
                return "OK"
            if type_matches and position != vehicle.assigned_slot:
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

        Logger.log(
            f"[ParkingManager] Vehicle #{vehicle.id} parking validation unknown "
            f"at {position}"
        )
        return "UNKNOWN"
