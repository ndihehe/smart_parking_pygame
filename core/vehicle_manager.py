from config import VEHICLE_MOVE_INTERVAL
from models.enums import VehicleStatus, VehicleType, WaitReason
from models.map_state import MapState
from models.vehicle import Vehicle
from utils.logger import Logger


class VehicleManager:
    def __init__(self) -> None:
        self.vehicles: dict[int, Vehicle] = {}
        self._next_id: int = 0
        self._move_timer: float = 0.0

    def spawn_vehicle(self, vehicle_type: VehicleType, gate_position: tuple[int, int]) -> Vehicle:
        vehicle = Vehicle(
            id=self._next_id,
            type=vehicle_type,
            position=gate_position,
            status=VehicleStatus.WAITING,
        )
        self.vehicles[vehicle.id] = vehicle
        self._next_id += 1
        Logger.log(
            f"[VehicleManager] Vehicle #{vehicle.id} spawned as "
            f"{vehicle.type.value} at {vehicle.position}"
        )
        return vehicle

    def remove_vehicle(self, vehicle_id: int) -> None:
        if vehicle_id in self.vehicles:
            del self.vehicles[vehicle_id]
            Logger.log(f"[VehicleManager] Vehicle #{vehicle_id} removed")

    def get_vehicle(self, vehicle_id: int) -> Vehicle | None:
        return self.vehicles.get(vehicle_id)

    def get_all_vehicles(self) -> list[Vehicle]:
        return list(self.vehicles.values())

    def reset(self) -> None:
        self.vehicles.clear()
        self._next_id = 0
        self._move_timer = 0.0
        Logger.log("[VehicleManager] All vehicles cleared")

    def set_status(self, vehicle_id: int, status: VehicleStatus) -> None:
        vehicle = self.vehicles.get(vehicle_id)
        if vehicle is not None:
            vehicle.status = status
            if status in (
                VehicleStatus.MOVING,
                VehicleStatus.PARKED,
                VehicleStatus.MANUAL,
                VehicleStatus.ARRIVED,
            ):
                vehicle.wait_reason = WaitReason.NONE
                vehicle.wait_time = 0.0
            Logger.log(f"[VehicleManager] Vehicle #{vehicle_id} status -> {status.value}")

    def set_path(self, vehicle_id: int, path: list[tuple[int, int]]) -> None:
        vehicle = self.vehicles.get(vehicle_id)
        if vehicle is not None:
            vehicle.path = path

    def set_wait_reason(self, vehicle_id: int, reason: WaitReason) -> None:
        vehicle = self.vehicles.get(vehicle_id)
        if vehicle is not None:
            vehicle.wait_reason = reason

    def set_manual(self, vehicle_id: int) -> None:
        vehicle = self.vehicles.get(vehicle_id)
        if vehicle is not None:
            vehicle.status = VehicleStatus.MANUAL
            vehicle.path = []
            vehicle.wait_reason = WaitReason.NONE
            vehicle.wait_time = 0.0
            Logger.log(f"[VehicleManager] Vehicle #{vehicle_id} switched to MANUAL")

    def update(self, delta_time: float, map_state: MapState) -> None:
        self._move_timer += delta_time

        if self._move_timer >= VEHICLE_MOVE_INTERVAL:
            self._move_timer = 0.0
            occupied_positions = {
                vehicle.position
                for vehicle in self.vehicles.values()
                if not (
                    vehicle.status == VehicleStatus.WAITING
                    and vehicle.wait_reason == WaitReason.GUARD_ESCORT
                )
            }
            for vehicle in self.vehicles.values():
                if vehicle.status == VehicleStatus.MOVING and len(vehicle.path) > 0:
                    next_cell = vehicle.path[0]
                    is_exiting = vehicle.wait_reason == WaitReason.EXITING
                    occupied_positions.discard(vehicle.position)
                    slot = map_state.parking_slots.get(next_cell)
                    blocked_by_vehicle = next_cell in occupied_positions
                    blocked_by_map = (
                        next_cell in map_state.dynamic_blocks
                        or next_cell in map_state.static_obstacles
                    )
                    blocked_by_slot = (
                        slot is not None
                        and slot.is_occupied
                        and slot.occupied_by != vehicle.id
                    ) or (
                        slot is not None
                        and slot.is_reserved
                        and slot.reserved_by != vehicle.id
                    )
                    passable = (
                        not blocked_by_map
                        and (
                            map_state.grid[next_cell[0]][next_cell[1]].value in {"G", "R", "I"}
                            or next_cell in map_state.parking_slots
                        )
                        and not blocked_by_vehicle
                        and not blocked_by_slot
                    )

                    if passable:
                        if len(vehicle.path) > 1:
                            current_delta = (
                                next_cell[0] - vehicle.position[0],
                                next_cell[1] - vehicle.position[1],
                            )
                            next_delta = (
                                vehicle.path[1][0] - next_cell[0],
                                vehicle.path[1][1] - next_cell[1],
                            )
                            vehicle.direction = (
                                "STRAIGHT"
                                if current_delta == next_delta
                                else "TURN"
                            )
                        else:
                            vehicle.direction = "STRAIGHT"
                        vehicle.position = next_cell
                        occupied_positions.add(vehicle.position)
                        vehicle.path.pop(0)
                        if not vehicle.path:
                            vehicle.status = VehicleStatus.ARRIVED
                            if vehicle.wait_reason != WaitReason.EXITING:
                                vehicle.wait_reason = WaitReason.NONE
                            Logger.log(
                                f"[VehicleManager] Vehicle #{vehicle.id} "
                                f"arrived at {vehicle.position}"
                            )
                    else:
                        if blocked_by_vehicle and not is_exiting:
                            vehicle.status = VehicleStatus.WAITING
                            vehicle.wait_reason = WaitReason.YIELDING
                        else:
                            vehicle.status = VehicleStatus.REROUTING
                            vehicle.wait_reason = (
                                WaitReason.EXITING
                                if is_exiting
                                else WaitReason.BLOCKED_BY_OBSTACLE
                            )
                        Logger.log(
                            f"[VehicleManager] Vehicle #{vehicle.id} blocked at "
                            f"{next_cell}, set to {vehicle.status.value}"
                        )
                    occupied_positions.add(vehicle.position)

        for vehicle in self.vehicles.values():
            if vehicle.status in (VehicleStatus.WAITING, VehicleStatus.REROUTING):
                vehicle.wait_time += delta_time
