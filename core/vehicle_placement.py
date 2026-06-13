from core.map_manager import MapManager
from core.vehicle_manager import VehicleManager
from models.enums import VehicleType


class VehiclePlacement:
    def __init__(
        self,
        map_manager: MapManager,
        vehicle_manager: VehicleManager,
    ) -> None:
        self.map_manager = map_manager
        self.vehicle_manager = vehicle_manager

    def can_place(
        self,
        position: tuple[int, int],
        vehicle_type: VehicleType,
        exiting: bool,
    ) -> bool:
        if self._is_occupied(position):
            return False

        if self.map_manager.is_drive_cell(position):
            return True

        if not exiting:
            return False

        slot = self.map_manager.get_state().parking_slots.get(position)
        if slot is None:
            return False
        if slot.is_occupied or slot.is_reserved:
            return False
        return slot.slot_type is None or slot.slot_type == vehicle_type

    def place_vehicle(
        self,
        position: tuple[int, int],
        vehicle_type: VehicleType,
        exiting: bool,
    ):
        if not self.can_place(position, vehicle_type, exiting):
            return None
        return self.vehicle_manager.spawn_vehicle(vehicle_type, position)

    def _is_occupied(self, position: tuple[int, int]) -> bool:
        return any(
            vehicle.position == position
            for vehicle in self.vehicle_manager.get_all_vehicles()
        )
