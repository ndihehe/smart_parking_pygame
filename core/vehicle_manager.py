from config import VEHICLE_MOVE_INTERVAL
from models.enums import VehicleStatus, VehicleType
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

    def set_status(self, vehicle_id: int, status: VehicleStatus) -> None:
        vehicle = self.vehicles.get(vehicle_id)
        if vehicle is not None:
            vehicle.status = status
            Logger.log(f"[VehicleManager] Vehicle #{vehicle_id} status -> {status.value}")

    def set_path(self, vehicle_id: int, path: list[tuple[int, int]]) -> None:
        vehicle = self.vehicles.get(vehicle_id)
        if vehicle is not None:
            vehicle.path = path

    def set_manual(self, vehicle_id: int) -> None:
        vehicle = self.vehicles.get(vehicle_id)
        if vehicle is not None:
            vehicle.status = VehicleStatus.MANUAL
            Logger.log(f"[VehicleManager] Vehicle #{vehicle_id} switched to MANUAL")

    def update(self, delta_time: float, map_state: MapState) -> None:
        self._move_timer += delta_time

        if self._move_timer >= VEHICLE_MOVE_INTERVAL:
            self._move_timer = 0.0
            occupied_positions = {
                vehicle.position
                for vehicle in self.vehicles.values()
            }
            for vehicle in self.vehicles.values():
                if vehicle.status == VehicleStatus.MOVING and len(vehicle.path) > 0:
                    next_cell = vehicle.path[0]
                    occupied_positions.discard(vehicle.position)
                    slot = map_state.parking_slots.get(next_cell)
                    passable = (
                        next_cell not in map_state.dynamic_blocks
                        and next_cell not in map_state.static_obstacles
                        and next_cell not in occupied_positions
                        and (
                            slot is None
                            or not slot.is_occupied
                            or slot.occupied_by == vehicle.id
                        )
                    )

                    if passable:
                        vehicle.position = next_cell
                        occupied_positions.add(vehicle.position)
                        vehicle.path.pop(0)
                        if not vehicle.path:
                            vehicle.status = VehicleStatus.PARKED
                            Logger.log(
                                f"[VehicleManager] Vehicle #{vehicle.id} "
                                f"parked at {vehicle.position}"
                            )
                    else:
                        vehicle.status = VehicleStatus.REROUTING
                        Logger.log(
                            f"[VehicleManager] Vehicle #{vehicle.id} blocked at "
                            f"{next_cell}, set to REROUTING"
                        )
                    occupied_positions.add(vehicle.position)

        for vehicle in self.vehicles.values():
            if vehicle.status in (VehicleStatus.WAITING, VehicleStatus.REROUTING):
                vehicle.wait_time += delta_time
