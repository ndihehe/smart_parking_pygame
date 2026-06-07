import random

from ai.pathfinding.astar import astar
from config import AUTO_SPAWN_INTERVAL
from core.map_manager import MapManager
from core.parking_manager import ParkingManager
from core.traffic_controller import TrafficController
from core.vehicle_manager import VehicleManager
from models.enums import VehicleStatus, VehicleType
from models.vehicle import Vehicle
from utils.logger import Logger


class GameController:
    def __init__(self, map_filepath: str) -> None:
        self.map_manager = MapManager()
        self.map_manager.load_map(map_filepath)
        self.vehicle_manager = VehicleManager()
        self.parking_manager = ParkingManager()
        self.traffic_controller = TrafficController()
        self._auto_spawn_timer: float = 0.0
        self._auto_spawn_enabled: bool = False

    def update(self, delta_time: float) -> None:
        if self._auto_spawn_enabled:
            self._auto_spawn_timer += delta_time
            if self._auto_spawn_timer >= AUTO_SPAWN_INTERVAL:
                vehicle_type = random.choice(list(VehicleType))
                self.spawn_vehicle(vehicle_type, 0)
                self._auto_spawn_timer = 0.0

        self.vehicle_manager.update(delta_time, self.map_manager.get_state())
        self.traffic_controller.update(
            self.vehicle_manager.get_all_vehicles(),
            self.map_manager,
            delta_time,
        )

        for vehicle in self.vehicle_manager.get_all_vehicles():
            if vehicle.status == VehicleStatus.REROUTING:
                self._reroute_vehicle(vehicle)

    def spawn_vehicle(
        self,
        vehicle_type: VehicleType,
        gate_index: int = 0,
    ) -> Vehicle | None:
        gate_cells = self.map_manager.get_state().gate_cells
        if not gate_cells:
            Logger.log("[GameController] No gate available")
            return None

        occupied_positions = {
            vehicle.position
            for vehicle in self.vehicle_manager.get_all_vehicles()
        }
        gate_position = gate_cells[gate_index]
        if gate_position in occupied_positions:
            available_gate = next(
                (
                    gate_cell
                    for gate_cell in gate_cells
                    if gate_cell not in occupied_positions
                ),
                None,
            )
            if available_gate is None:
                Logger.log("[GameController] No gate available")
                return None
            gate_position = available_gate

        vehicle = self.vehicle_manager.spawn_vehicle(vehicle_type, gate_position)
        self._assign_and_path(vehicle)
        return vehicle

    def confirm_parking(self, vehicle_id: int) -> str:
        vehicle = self.vehicle_manager.get_vehicle(vehicle_id)
        if vehicle is None:
            return "NOT_FOUND"

        result = self.parking_manager.validate_parking(
            vehicle,
            self.map_manager.get_state(),
        )

        if result in ("OK", "DIFFERENT_SLOT"):
            self.vehicle_manager.set_status(vehicle_id, VehicleStatus.PARKED)
            self.parking_manager.assign_slot(
                vehicle,
                vehicle.position,
                self.map_manager.get_state(),
            )
        elif result in ("WRONG_TYPE", "ILLEGAL_ROAD", "BLOCKING_INTERSECTION"):
            self.vehicle_manager.set_status(vehicle_id, VehicleStatus.VIOLATION)
            self.map_manager.add_dynamic_block(vehicle.position)
            self.traffic_controller.handle_obstacle(
                vehicle.position,
                self.vehicle_manager.get_all_vehicles(),
                self.map_manager,
            )

        return result

    def set_manual(self, vehicle_id: int) -> None:
        self.vehicle_manager.set_manual(vehicle_id)

    def move_manual(self, vehicle_id: int, direction: tuple[int, int]) -> None:
        vehicle = self.vehicle_manager.get_vehicle(vehicle_id)
        if vehicle is None or vehicle.status != VehicleStatus.MANUAL:
            return

        new_position = (
            vehicle.position[0] + direction[0],
            vehicle.position[1] + direction[1],
        )
        occupied_positions = {
            other_vehicle.position
            for other_vehicle in self.vehicle_manager.get_all_vehicles()
            if other_vehicle.id != vehicle.id
        }
        slot = self.map_manager.get_state().parking_slots.get(new_position)
        slot_available = (
            slot is None
            or not slot.is_occupied
            or slot.occupied_by == vehicle.id
        )
        if (
            self.map_manager.is_passable(new_position)
            and new_position not in occupied_positions
            and slot_available
        ):
            vehicle.position = new_position
        else:
            Logger.log(
                f"[GameController] Vehicle #{vehicle.id} cannot move to {new_position}"
            )

    def toggle_auto_spawn(self) -> None:
        self._auto_spawn_enabled = not self._auto_spawn_enabled
        status = "enabled" if self._auto_spawn_enabled else "disabled"
        Logger.log(f"[GameController] Auto spawn {status}")

    def _assign_and_path(self, vehicle: Vehicle) -> None:
        slot = self.parking_manager.find_slot(vehicle, self.map_manager.get_state())
        if slot is None:
            self.vehicle_manager.set_status(vehicle.id, VehicleStatus.WAITING)
            return

        self.parking_manager.assign_slot(vehicle, slot, self.map_manager.get_state())
        path = astar(vehicle.position, slot, self.map_manager)
        if path:
            self.vehicle_manager.set_path(vehicle.id, path)
            self.vehicle_manager.set_status(vehicle.id, VehicleStatus.MOVING)
            Logger.log(
                f"[GameController] Vehicle #{vehicle.id} path found via A*, "
                f"length={len(path)}"
            )
        else:
            self.vehicle_manager.set_status(vehicle.id, VehicleStatus.WAITING)
            Logger.log(f"[GameController] Vehicle #{vehicle.id} no path found")

    def _reroute_vehicle(self, vehicle: Vehicle) -> None:
        if vehicle.assigned_slot is None:
            self.vehicle_manager.set_status(vehicle.id, VehicleStatus.WAITING)
            Logger.log(
                f"[GameController] Vehicle #{vehicle.id} reroute failed, set WAITING"
            )
            return

        path = astar(vehicle.position, vehicle.assigned_slot, self.map_manager)
        if path:
            self.vehicle_manager.set_path(vehicle.id, path)
            self.vehicle_manager.set_status(vehicle.id, VehicleStatus.MOVING)
            Logger.log(
                f"[GameController] Vehicle #{vehicle.id} rerouted, length={len(path)}"
            )
        else:
            self.vehicle_manager.set_status(vehicle.id, VehicleStatus.WAITING)
            Logger.log(
                f"[GameController] Vehicle #{vehicle.id} reroute failed, set WAITING"
            )
