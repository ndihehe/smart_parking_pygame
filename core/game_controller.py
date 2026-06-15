import copy
import random

from ai.pathfinding.router import find_path, normalize_algorithm_name
from config import (
    AUTO_SPAWN_INTERVAL,
    MANUAL_ENFORCE_THRESHOLD,
    REROUTE_WAIT_THRESHOLD,
    VEHICLE_MOVE_INTERVAL,
)
from core.map_manager import MapManager
from core.parking_manager import ParkingManager
from core.scenario_manager import ScenarioManager
from core.simulation_state import SimulationStatus, VehiclePlan
from core.traffic_controller import TrafficController
from core.vehicle_manager import VehicleManager
from core.vehicle_placement import VehiclePlacement
from models.enums import AlgorithmType, VehicleStatus, VehicleType, WaitReason
from models.guard import Guard
from models.vehicle import Vehicle
from utils.logger import Logger


class GameController:
    def __init__(
        self,
        map_filepath: str,
        algorithm: str | AlgorithmType = AlgorithmType.ASTAR,
    ) -> None:
        self.map_manager = MapManager()
        self.map_manager.load_map(map_filepath)
        self.vehicle_manager = VehicleManager()
        self.parking_manager = ParkingManager()
        self.traffic_controller = TrafficController()
        self.scenario_manager = ScenarioManager(self.map_manager)
        self.vehicle_placement = VehiclePlacement(self.map_manager, self.vehicle_manager)
        home_position = self.map_manager.get_state().gate_cells[0]
        self.guards: list[Guard] = [
            Guard(id=0, position=home_position, home_position=home_position)
        ]
        self._next_guard_id = 1
        self._auto_spawn_timer: float = 0.0
        self._auto_spawn_enabled: bool = False
        self.current_algorithm: str | AlgorithmType = normalize_algorithm_name(algorithm)
        self._tandem_exit_jobs: dict[int, dict[str, object]] = {}
        self.simulation_status = SimulationStatus.IDLE
        self.active_scenario: str | None = None
        self.placement_vehicle_type = VehicleType.CAR
        self.placement_plan = VehiclePlan.ENTERING
        self._vehicle_plans: dict[int, VehiclePlan] = {}
        self.simulation_speed = 1.0
        self.step_mode_enabled = False
        self._step_requested = False
        self._step_history: list[dict[str, object]] = []
        self._manual_snapshots: dict[int, dict[str, object]] = {}

    def update(self, delta_time: float) -> None:
        if self.simulation_status in {
            SimulationStatus.PLACING_VEHICLE,
            SimulationStatus.READY,
            SimulationStatus.PAUSED,
            SimulationStatus.FINISHED,
        }:
            return
        if self.step_mode_enabled:
            if not self._step_requested:
                return
            self._save_step_snapshot()
            delta_time = VEHICLE_MOVE_INTERVAL
            self._step_requested = False
        else:
            delta_time *= self.simulation_speed

        if self._auto_spawn_enabled:
            self._auto_spawn_timer += delta_time
            if self._auto_spawn_timer >= AUTO_SPAWN_INTERVAL:
                vehicle_type = random.choice(list(VehicleType))
                self.spawn_vehicle(vehicle_type, 0)
                self._auto_spawn_timer = 0.0

        self.traffic_controller.update(
            self.vehicle_manager.get_all_vehicles(),
            self.map_manager,
            delta_time,
            self.guards,
            self.current_algorithm,
        )
        self.vehicle_manager.update(delta_time, self.map_manager.get_state())
        self._update_manual_vehicle_timers(delta_time)
        self._update_tandem_exit_jobs()

        for vehicle in self.vehicle_manager.get_all_vehicles():
            if vehicle.position in self._exit_gates():
                self._finish_vehicle_exit(vehicle)
                continue
            if self._skip_standard_update_for_tandem_job(vehicle):
                continue
            if vehicle.status == VehicleStatus.REROUTING:
                self._reroute_vehicle(vehicle)
            elif vehicle.status == VehicleStatus.WAITING:
                self._recover_waiting_vehicle(vehicle)
            elif vehicle.status == VehicleStatus.ARRIVED:
                if self._is_exiting_vehicle(vehicle):
                    self._reroute_exiting_vehicle(vehicle)
                else:
                    self._validate_and_apply_parking(vehicle)
        self._update_guards(delta_time)
        self._update_finished_state()

    def spawn_vehicle(
        self,
        vehicle_type: VehicleType,
        gate_index: int = 0,
    ) -> Vehicle | None:
        if not self._has_available_slot(vehicle_type):
            label = "car" if vehicle_type == VehicleType.CAR else "motorbike"
            Logger.log(f"[GameController] {label} lot full, cannot spawn more vehicles")
            return None

        gate_cells = self._entry_gates()
        if not gate_cells:
            Logger.log("[GameController] No entry gate available")
            return None

        occupied_positions = {
            vehicle.position
            for vehicle in self.vehicle_manager.get_all_vehicles()
        }
        gate_position = gate_cells[min(gate_index, len(gate_cells) - 1)]
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
                Logger.log("[GameController] No entry gate available")
                return None
            gate_position = available_gate

        vehicle = self.vehicle_manager.spawn_vehicle(vehicle_type, gate_position)
        self._assign_and_path(vehicle)
        self._vehicle_plans[vehicle.id] = VehiclePlan.ENTERING
        if self.simulation_status in {SimulationStatus.IDLE, SimulationStatus.FINISHED}:
            self.simulation_status = SimulationStatus.RUNNING
        return vehicle

    def start_simulation(self) -> None:
        if self.simulation_status != SimulationStatus.READY:
            return

        for vehicle in self.vehicle_manager.get_all_vehicles():
            plan = self._vehicle_plans.get(vehicle.id)
            if plan == VehiclePlan.EXITING:
                self.start_exit(vehicle.id)
            elif plan == VehiclePlan.ENTERING:
                self._assign_and_path(vehicle)
            elif not vehicle.path and vehicle.status in {
                VehicleStatus.WAITING,
                VehicleStatus.MANUAL,
            }:
                self._assign_and_path(vehicle)
        self.simulation_status = SimulationStatus.RUNNING
        Logger.log("[GameController] Simulation started")

    def reset_simulation(self) -> None:
        self.vehicle_manager.reset()
        self.map_manager.get_state().dynamic_blocks.clear()
        for slot in self.map_manager.get_state().parking_slots.values():
            slot.is_reserved = False
            slot.reserved_by = None
            slot.is_occupied = False
            slot.occupied_by = None
        home_position = self.map_manager.get_state().gate_cells[0]
        self.guards = [Guard(id=0, position=home_position, home_position=home_position)]
        self._next_guard_id = 1
        self._auto_spawn_timer = 0.0
        self._auto_spawn_enabled = False
        self._tandem_exit_jobs.clear()
        self._vehicle_plans.clear()
        self._manual_snapshots.clear()
        self.active_scenario = None
        self.simulation_status = SimulationStatus.IDLE
        self.simulation_speed = 1.0
        self.step_mode_enabled = False
        self._step_requested = False
        self._step_history.clear()
        Logger.log("[GameController] Simulation reset")

    def prepare_traffic_jam_scenario(self) -> None:
        self.reset_simulation()
        for vehicle_type, position, plan in self.scenario_manager.build_traffic_jam():
            vehicle = self.vehicle_manager.spawn_vehicle(vehicle_type, position)
            self._vehicle_plans[vehicle.id] = plan
        self.active_scenario = "Traffic Jam Mode"
        self.simulation_status = SimulationStatus.READY
        Logger.log("[ScenarioManager] Traffic Jam Mode ready")

    def begin_vehicle_placement(self) -> None:
        self.simulation_status = SimulationStatus.PLACING_VEHICLE
        self.active_scenario = "Manual Placement"
        Logger.log("[GameController] Manual vehicle placement enabled")

    def set_placement_vehicle_type(self, vehicle_type: VehicleType) -> None:
        self.placement_vehicle_type = vehicle_type
        Logger.log(f"[GameController] Placement vehicle type -> {vehicle_type.value}")

    def set_placement_plan(self, plan: VehiclePlan) -> None:
        self.placement_plan = plan
        Logger.log(f"[GameController] Placement plan -> {plan.value}")

    def place_vehicle_at(self, position: tuple[int, int]) -> bool:
        if self.simulation_status != SimulationStatus.PLACING_VEHICLE:
            return False

        exiting = self.placement_plan == VehiclePlan.EXITING
        vehicle = self.vehicle_placement.place_vehicle(
            position,
            self.placement_vehicle_type,
            exiting,
        )
        if vehicle is None:
            Logger.log(f"[GameController] Cannot place vehicle at {position}")
            return False

        if exiting and position in self.map_manager.get_state().parking_slots:
            self.parking_manager.occupy_slot(
                vehicle,
                position,
                self.map_manager.get_state(),
            )
        self._vehicle_plans[vehicle.id] = self.placement_plan
        self.simulation_status = SimulationStatus.READY
        Logger.log(
            f"[GameController] Vehicle #{vehicle.id} placed at {position} "
            f"as {self.placement_plan.value}"
        )
        return True

    def set_simulation_speed(self, speed: float) -> None:
        self.simulation_speed = max(0.1, speed)
        self.step_mode_enabled = False
        Logger.log(f"[GameController] Simulation speed -> {self.simulation_speed:.2f}x")

    def toggle_step_mode(self) -> None:
        self.step_mode_enabled = not self.step_mode_enabled
        if self.step_mode_enabled:
            self.simulation_speed = 1.0
        status = "enabled" if self.step_mode_enabled else "disabled"
        Logger.log(f"[GameController] Step mode {status}")

    def request_next_step(self) -> None:
        if self.simulation_status == SimulationStatus.READY:
            self.start_simulation()
        if self.simulation_status == SimulationStatus.RUNNING:
            self.step_mode_enabled = True
            self._step_requested = True
            Logger.log("[GameController] Next simulation step requested")

    def request_previous_step(self) -> None:
        if not self._step_history:
            Logger.log("[GameController] No previous step available")
            return
        self._restore_step_snapshot(self._step_history.pop())
        self.step_mode_enabled = True
        self.simulation_status = SimulationStatus.RUNNING
        Logger.log("[GameController] Previous simulation step restored")

    def _save_step_snapshot(self) -> None:
        map_state = self.map_manager.get_state()
        self._step_history.append(
            {
                "vehicles": copy.deepcopy(self.vehicle_manager.vehicles),
                "next_vehicle_id": self.vehicle_manager._next_id,
                "vehicle_move_timer": self.vehicle_manager._move_timer,
                "dynamic_blocks": copy.deepcopy(map_state.dynamic_blocks),
                "parking_slots": copy.deepcopy(map_state.parking_slots),
                "guards": copy.deepcopy(self.guards),
                "next_guard_id": self._next_guard_id,
                "tandem_exit_jobs": copy.deepcopy(self._tandem_exit_jobs),
                "vehicle_plans": copy.deepcopy(self._vehicle_plans),
                "simulation_status": self.simulation_status,
            }
        )
        if len(self._step_history) > 50:
            self._step_history.pop(0)

    def _restore_step_snapshot(self, snapshot: dict[str, object]) -> None:
        map_state = self.map_manager.get_state()
        self.vehicle_manager.vehicles = copy.deepcopy(snapshot["vehicles"])
        self.vehicle_manager._next_id = int(snapshot["next_vehicle_id"])
        self.vehicle_manager._move_timer = float(snapshot["vehicle_move_timer"])
        map_state.dynamic_blocks = copy.deepcopy(snapshot["dynamic_blocks"])
        map_state.parking_slots = copy.deepcopy(snapshot["parking_slots"])
        self.guards = copy.deepcopy(snapshot["guards"])
        self._next_guard_id = int(snapshot["next_guard_id"])
        self._tandem_exit_jobs = copy.deepcopy(snapshot["tandem_exit_jobs"])
        self._vehicle_plans = copy.deepcopy(snapshot["vehicle_plans"])
        self.simulation_status = snapshot["simulation_status"]

    def confirm_parking(self, vehicle_id: int) -> str:
        vehicle = self.vehicle_manager.get_vehicle(vehicle_id)
        if vehicle is None:
            return "NOT_FOUND"

        return self._validate_and_apply_parking(vehicle)

    def _validate_and_apply_parking(self, vehicle: Vehicle) -> str:
        if vehicle.position in self._exit_gates():
            self._finish_vehicle_exit(vehicle)
            return "EXITED"

        result = self.parking_manager.validate_parking(
            vehicle,
            self.map_manager.get_state(),
        )

        if result in ("OK", "DIFFERENT_SLOT"):
            self.vehicle_manager.set_status(vehicle.id, VehicleStatus.PARKED)
            self.parking_manager.occupy_slot(
                vehicle,
                vehicle.position,
                self.map_manager.get_state(),
            )
            self._clear_vehicle_violation_response(vehicle)
            Logger.log(
                f"[GameController] Vehicle #{vehicle.id} parking accepted: {result}"
            )
        elif result in ("WRONG_TYPE", "ILLEGAL_ROAD", "BLOCKING_INTERSECTION"):
            self.parking_manager.release_vehicle_slot(vehicle, self.map_manager.get_state())
            self.vehicle_manager.set_status(vehicle.id, VehicleStatus.VIOLATION)
            vehicle.path = []
            violation_reasons = {
                "WRONG_TYPE": WaitReason.PARKING_VIOLATION_WRONG_TYPE,
                "ILLEGAL_ROAD": WaitReason.PARKING_VIOLATION_ILLEGAL_ROAD,
                "BLOCKING_INTERSECTION": WaitReason.PARKING_VIOLATION_BLOCKING_INTERSECTION,
            }
            vehicle.wait_reason = violation_reasons[result]
            Logger.log(
                f"[GameController] Parking violation detected for Vehicle #{vehicle.id}: {result}"
            )
            if result in ("ILLEGAL_ROAD", "BLOCKING_INTERSECTION"):
                self.map_manager.add_dynamic_block(vehicle.position)
                self.traffic_controller.handle_obstacle(
                    vehicle.position,
                    self.vehicle_manager.get_all_vehicles(),
                    self.map_manager,
                    self.current_algorithm,
                )
            self._dispatch_violation_guard(vehicle)
        else:
            Logger.log(
                f"[GameController] Vehicle #{vehicle.id} parking validation result: {result}"
            )

        return result

    def set_manual(self, vehicle_id: int) -> None:
        vehicle = self.vehicle_manager.get_vehicle(vehicle_id)
        if vehicle is None:
            return
        self._manual_snapshots[vehicle.id] = {
            "assigned_slot": vehicle.assigned_slot,
            "wait_reason": vehicle.wait_reason,
        }
        self.vehicle_manager.set_manual(vehicle_id)

    def cancel_manual(self, vehicle_id: int) -> None:
        vehicle = self.vehicle_manager.get_vehicle(vehicle_id)
        if vehicle is None or vehicle.status != VehicleStatus.MANUAL:
            return

        self._clear_manual_violation(vehicle)
        snapshot = self._manual_snapshots.pop(vehicle.id, {})
        if snapshot.get("wait_reason") == WaitReason.EXITING:
            self.start_exit(vehicle.id)
            Logger.log(f"[GameController] Vehicle #{vehicle.id} manual mode cancelled; resumed exit")
            return

        assigned_slot = snapshot.get("assigned_slot") or vehicle.assigned_slot
        if isinstance(assigned_slot, tuple):
            vehicle.assigned_slot = assigned_slot
            if vehicle.position == assigned_slot:
                self.vehicle_manager.set_status(vehicle.id, VehicleStatus.PARKED)
                Logger.log(
                    f"[GameController] Vehicle #{vehicle.id} manual mode cancelled; already parked"
                )
                return
            path = self._path_to_parking_slot(vehicle.position, assigned_slot, vehicle.id)
            if path:
                self.vehicle_manager.set_path(vehicle.id, path)
                self.vehicle_manager.set_status(vehicle.id, VehicleStatus.MOVING)
                Logger.log(
                    f"[GameController] Vehicle #{vehicle.id} manual mode cancelled; resumed route"
                )
                return

        self._assign_and_path(vehicle)
        if vehicle.status != VehicleStatus.MOVING:
            self.vehicle_manager.set_status(vehicle.id, VehicleStatus.WAITING)
            self.vehicle_manager.set_wait_reason(vehicle.id, WaitReason.NO_PATH)
        Logger.log(f"[GameController] Vehicle #{vehicle.id} manual mode cancelled")

    def _clear_manual_violation(self, vehicle: Vehicle) -> None:
        if vehicle.position in self.map_manager.get_state().dynamic_blocks:
            self.map_manager.remove_dynamic_block(vehicle.position)
        self._clear_vehicle_violation_response(vehicle)

    def _clear_vehicle_violation_response(self, vehicle: Vehicle) -> None:
        for guard in self.guards:
            if guard.task == "VIOLATION" and guard.target_vehicle_id == vehicle.id:
                Logger.log(
                    f"[Guard] Guard #{guard.id} cancelled violation escort for "
                    f"Vehicle #{vehicle.id}; violation cleared"
                )
                self._return_guard_home(guard)

    def start_exit(self, vehicle_id: int) -> None:
        vehicle = self.vehicle_manager.get_vehicle(vehicle_id)
        if vehicle is None:
            return

        self._vehicle_plans[vehicle.id] = VehiclePlan.EXITING

        if self._try_start_tandem_inner_exit(vehicle):
            return

        if vehicle.position in self._exit_gates():
            self._finish_vehicle_exit(vehicle)
            return

        exit_gate = self._nearest_available_exit_gate(vehicle.position, vehicle.id)
        if exit_gate is None:
            Logger.log(f"[GameController] Vehicle #{vehicle.id} cannot exit: no exit gate available")
            return

        self.parking_manager.release_vehicle_slot(vehicle, self.map_manager.get_state())
        path = self._path_from_parking_position_to_goal(
            vehicle.position,
            exit_gate,
            vehicle.id,
        )
        if path:
            self.vehicle_manager.set_path(vehicle.id, path)
            self.vehicle_manager.set_status(vehicle.id, VehicleStatus.MOVING)
            self.vehicle_manager.set_wait_reason(vehicle.id, WaitReason.EXITING)
            Logger.log(
                f"[GameController] Vehicle #{vehicle.id} leaving via exit {exit_gate}"
            )
        else:
            self.vehicle_manager.set_status(vehicle.id, VehicleStatus.WAITING)
            self.vehicle_manager.set_wait_reason(vehicle.id, WaitReason.NO_EXIT_PATH)
            Logger.log(f"[GameController] Vehicle #{vehicle.id} cannot find exit path")

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
            or (
                not slot.is_occupied
                and (
                    not slot.is_reserved
                    or slot.reserved_by == vehicle.id
                )
            )
            or slot.occupied_by == vehicle.id
        )
        if (
            self.map_manager.can_vehicle_enter(new_position)
            and new_position not in occupied_positions
            and slot_available
        ):
            old_position = vehicle.position
            vehicle.position = new_position
            if old_position in self.map_manager.get_state().dynamic_blocks:
                self.map_manager.remove_dynamic_block(old_position)
                vehicle.wait_time = 0.0
            old_slot = self.map_manager.get_state().parking_slots.get(old_position)
            if old_slot is not None and old_slot.occupied_by == vehicle.id:
                self.parking_manager.release_vehicle_slot(
                    vehicle,
                    self.map_manager.get_state(),
                )
        else:
            Logger.log(
                f"[GameController] Vehicle #{vehicle.id} cannot move to {new_position}"
            )

    def _update_manual_vehicle_timers(self, delta_time: float) -> None:
        for vehicle in self.vehicle_manager.get_all_vehicles():
            if vehicle.status == VehicleStatus.MANUAL:
                vehicle.wait_time += delta_time

    def _update_finished_state(self) -> None:
        vehicles = self.vehicle_manager.get_all_vehicles()
        if not vehicles and self.simulation_status == SimulationStatus.RUNNING:
            self.simulation_status = SimulationStatus.FINISHED
            Logger.log("[GameController] Simulation finished")

    def toggle_auto_spawn(self) -> None:
        self._auto_spawn_enabled = not self._auto_spawn_enabled
        status = "enabled" if self._auto_spawn_enabled else "disabled"
        Logger.log(f"[GameController] Auto spawn {status}")

    def set_pathfinding_algorithm(self, algorithm: str | AlgorithmType) -> None:
        self.current_algorithm = normalize_algorithm_name(algorithm)
        Logger.log(f"[GameController] Pathfinding algorithm -> {self.current_algorithm}")

    def _assign_and_path(self, vehicle: Vehicle) -> None:
        if vehicle.status == VehicleStatus.PARKED and vehicle.assigned_slot is not None:
            return

        slot = self.parking_manager.find_slot(vehicle, self.map_manager.get_state())
        if slot is None:
            self.vehicle_manager.set_status(vehicle.id, VehicleStatus.WAITING)
            self.vehicle_manager.set_wait_reason(vehicle.id, WaitReason.NO_SLOT)
            return

        self.parking_manager.assign_slot(vehicle, slot, self.map_manager.get_state())
        path = self._path_to_parking_slot(vehicle.position, slot, vehicle.id)
        if path:
            self.vehicle_manager.set_path(vehicle.id, path)
            self.vehicle_manager.set_status(vehicle.id, VehicleStatus.MOVING)
            Logger.log(
                f"[GameController] Vehicle #{vehicle.id} path found via "
                f"{self.current_algorithm.upper()}, "
                f"length={len(path)}"
            )
        else:
            self.parking_manager.release_vehicle_slot(vehicle, self.map_manager.get_state())
            self.vehicle_manager.set_status(vehicle.id, VehicleStatus.WAITING)
            self.vehicle_manager.set_wait_reason(vehicle.id, WaitReason.NO_PATH)
            Logger.log(f"[GameController] Vehicle #{vehicle.id} no path found")

    def _reroute_vehicle(self, vehicle: Vehicle) -> None:
        if self._is_exiting_vehicle(vehicle):
            self._reroute_exiting_vehicle(vehicle)
            return

        if vehicle.assigned_slot is None:
            self._assign_and_path(vehicle)
            return

        if not self._assigned_slot_available(vehicle):
            old_slot = vehicle.assigned_slot
            self.parking_manager.release_vehicle_slot(vehicle, self.map_manager.get_state())
            Logger.log(f"[GameController] Vehicle #{vehicle.id} released unavailable slot {old_slot}")
            self._assign_and_path(vehicle)
            if vehicle.status == VehicleStatus.WAITING:
                Logger.log(
                    f"[GameController] Vehicle #{vehicle.id} reroute failed, set WAITING"
                )
            return

        if vehicle.assigned_slot in self.map_manager.get_state().dynamic_blocks:
            old_slot = vehicle.assigned_slot
            self.parking_manager.release_vehicle_slot(vehicle, self.map_manager.get_state())
            Logger.log(f"[GameController] Vehicle #{vehicle.id} released blocked slot {old_slot}")
            self._assign_and_path(vehicle)
            if vehicle.status == VehicleStatus.WAITING:
                Logger.log(
                    f"[GameController] Vehicle #{vehicle.id} reroute failed, set WAITING"
                )
            return

        if vehicle.wait_reason == WaitReason.BLOCKED_BY_VEHICLE:
            path = self._path_to_parking_slot(
                vehicle.position,
                vehicle.assigned_slot,
                vehicle.id,
            )
            if path:
                if path == vehicle.path and not self._next_cell_available(vehicle):
                    self.vehicle_manager.set_status(vehicle.id, VehicleStatus.WAITING)
                    self.vehicle_manager.set_wait_reason(vehicle.id, WaitReason.YIELDING)
                    Logger.log(
                        f"[GameController] Vehicle #{vehicle.id} waiting; no alternate lane available"
                    )
                    return
                self.vehicle_manager.set_path(vehicle.id, path)
                self.vehicle_manager.set_status(vehicle.id, VehicleStatus.MOVING)
                Logger.log(
                    f"[GameController] Vehicle #{vehicle.id} rerouted around vehicle, "
                    f"length={len(path)}"
                )
                return

        path = self._path_to_parking_slot(
            vehicle.position,
            vehicle.assigned_slot,
            vehicle.id,
        )
        if path:
            self.vehicle_manager.set_path(vehicle.id, path)
            self.vehicle_manager.set_status(vehicle.id, VehicleStatus.MOVING)
            Logger.log(
                f"[GameController] Vehicle #{vehicle.id} rerouted, length={len(path)}"
            )
        else:
            old_slot = vehicle.assigned_slot
            self.parking_manager.release_vehicle_slot(vehicle, self.map_manager.get_state())
            Logger.log(f"[GameController] Vehicle #{vehicle.id} released slot {old_slot}")
            self._assign_and_path(vehicle)
            if vehicle.status == VehicleStatus.WAITING:
                Logger.log(
                    f"[GameController] Vehicle #{vehicle.id} reroute failed, set WAITING"
                )

    def _reroute_exiting_vehicle(self, vehicle: Vehicle) -> None:
        self.start_exit(vehicle.id)
        if self.vehicle_manager.get_vehicle(vehicle.id) is not None:
            Logger.log(f"[GameController] Vehicle #{vehicle.id} rerouting to exit")

    def _is_exiting_vehicle(self, vehicle: Vehicle) -> bool:
        return (
            vehicle.wait_reason == WaitReason.EXITING
            or self._vehicle_plans.get(vehicle.id) == VehiclePlan.EXITING
        )

    def _recover_waiting_vehicle(self, vehicle: Vehicle) -> None:
        if self._is_exiting_vehicle(vehicle):
            if vehicle.position in self._exit_gates():
                self._finish_vehicle_exit(vehicle)
                return
            if vehicle.path and self._next_cell_available(vehicle):
                self.vehicle_manager.set_status(vehicle.id, VehicleStatus.MOVING)
                self.vehicle_manager.set_wait_reason(vehicle.id, WaitReason.EXITING)
                Logger.log(f"[GameController] Vehicle #{vehicle.id} resumed exit route")
                return
            if vehicle.wait_time >= VEHICLE_MOVE_INTERVAL:
                self._reroute_exiting_vehicle(vehicle)
            return

        if vehicle.wait_reason == WaitReason.NO_EXIT_PATH:
            self.start_exit(vehicle.id)
            return

        if vehicle.wait_reason == WaitReason.YIELDING:
            if vehicle.wait_time < VEHICLE_MOVE_INTERVAL:
                return
            if vehicle.path and self._next_cell_available(vehicle):
                self.vehicle_manager.set_status(vehicle.id, VehicleStatus.MOVING)
                Logger.log(f"[GameController] Vehicle #{vehicle.id} resumed after yielding")
                return
            if vehicle.wait_time < REROUTE_WAIT_THRESHOLD:
                return

        if vehicle.wait_reason == WaitReason.GUARD_ESCORT and vehicle.path:
            if self._next_cell_available(vehicle):
                self.vehicle_manager.set_status(vehicle.id, VehicleStatus.MOVING)
                Logger.log(f"[Guard] Vehicle #{vehicle.id} resumed after guard hold")
                return
            if vehicle.wait_time < REROUTE_WAIT_THRESHOLD:
                return

        if vehicle.wait_reason in (
            WaitReason.NO_SLOT,
            WaitReason.NO_PATH,
            WaitReason.BLOCKED_BY_VEHICLE,
            WaitReason.BLOCKED_BY_OBSTACLE,
            WaitReason.TRAFFIC_CONGESTION,
            WaitReason.WAITING_FOR_INTERSECTION,
            WaitReason.GUARD_ESCORT,
            WaitReason.YIELDING,
        ):
            if vehicle.assigned_slot is None:
                self._assign_and_path(vehicle)
            else:
                self._reroute_vehicle(vehicle)

    def _next_cell_available(self, vehicle: Vehicle) -> bool:
        if not vehicle.path:
            return False

        next_cell = vehicle.path[0]
        map_state = self.map_manager.get_state()
        slot = map_state.parking_slots.get(next_cell)
        slot_available = (
            slot is None
            or (
                not slot.is_occupied
                and (
                    not slot.is_reserved
                    or slot.reserved_by == vehicle.id
                )
            )
            or slot.occupied_by == vehicle.id
        )
        return (
            self.map_manager.is_passable(next_cell)
            and next_cell not in self._occupied_positions(vehicle.id)
            and slot_available
        )

    def _assigned_slot_available(self, vehicle: Vehicle) -> bool:
        if vehicle.assigned_slot is None:
            return False

        slot = self.map_manager.get_state().parking_slots.get(vehicle.assigned_slot)
        if slot is None:
            return False

        if slot.is_occupied and slot.occupied_by != vehicle.id:
            return False

        return not slot.is_reserved or slot.reserved_by == vehicle.id

    def _has_available_slot(self, vehicle_type: VehicleType) -> bool:
        map_state = self.map_manager.get_state()
        slot_positions = (
            map_state.car_slots
            if vehicle_type == VehicleType.CAR
            else map_state.motorbike_slots
        )
        return any(
            not (slot := map_state.parking_slots[position]).is_occupied
            and not slot.is_reserved
            and position not in map_state.dynamic_blocks
            for position in slot_positions
        )

    def _entry_gates(self) -> list[tuple[int, int]]:
        return self.map_manager.get_state().entry_gates

    def _exit_gates(self) -> list[tuple[int, int]]:
        return self.map_manager.get_state().exit_gates

    def _nearest_available_exit_gate(
        self,
        position: tuple[int, int],
        vehicle_id: int,
    ) -> tuple[int, int] | None:
        occupied_positions = self._occupied_positions(vehicle_id)
        available_gates = [
            gate
            for gate in self._exit_gates()
            if gate not in occupied_positions
        ]
        if not available_gates:
            return None
        return min(
            available_gates,
            key=lambda gate: abs(position[0] - gate[0]) + abs(position[1] - gate[1]),
        )

    def _finish_vehicle_exit(self, vehicle: Vehicle) -> None:
        self.parking_manager.release_vehicle_slot(vehicle, self.map_manager.get_state())
        self._vehicle_plans.pop(vehicle.id, None)
        Logger.log(f"[GameController] Vehicle #{vehicle.id} exited the parking lot")
        self.vehicle_manager.remove_vehicle(vehicle.id)

    def _try_start_tandem_inner_exit(self, vehicle: Vehicle) -> bool:
        map_state = self.map_manager.get_state()
        outer_slot = map_state.motorbike_inner_to_outer.get(vehicle.position)
        if outer_slot is None:
            return False
        if vehicle.id in self._tandem_exit_jobs:
            return self._tandem_exit_jobs[vehicle.id].get("phase") != "INNER_EXITING"

        outer_vehicle = self._vehicle_at(outer_slot)
        if outer_vehicle is None:
            return False

        temp_position = self._temporary_drive_cell_for_tandem(
            outer_slot,
            {vehicle.id, outer_vehicle.id},
            vehicle.position,
        )
        if temp_position is None:
            temp_position = outer_slot
            Logger.log(
                f"[Guard] No temporary cell near {outer_slot}; holding outer "
                f"motorbike #{outer_vehicle.id} aside in place"
            )

        self.parking_manager.release_vehicle_slot(outer_vehicle, map_state)
        path = [] if temp_position == outer_vehicle.position else find_path(
            self.current_algorithm,
            outer_vehicle.position,
            temp_position,
            self.map_manager,
            self._occupied_positions(outer_vehicle.id),
        )
        if not path and outer_vehicle.position != temp_position:
            self.parking_manager.occupy_slot(
                outer_vehicle,
                outer_slot,
                map_state,
            )
            Logger.log(
                f"[Guard] Cannot move outer motorbike #{outer_vehicle.id} away from {outer_slot}"
            )
            return True

        outer_vehicle.path = path
        outer_vehicle.status = VehicleStatus.MOVING if path else VehicleStatus.WAITING
        outer_vehicle.wait_reason = WaitReason.GUARD_ESCORT
        vehicle.status = VehicleStatus.WAITING
        vehicle.wait_reason = WaitReason.GUARD_ESCORT
        self._tandem_exit_jobs[vehicle.id] = {
            "outer_id": outer_vehicle.id,
            "inner_slot": vehicle.position,
            "outer_slot": outer_slot,
            "temp_position": temp_position,
            "phase": "OUTER_MOVING_OUT",
        }
        Logger.log(
            f"[Guard] Assisting inner motorbike #{vehicle.id}: moving outer "
            f"#{outer_vehicle.id} to {temp_position}"
        )
        return True

    def _update_tandem_exit_jobs(self) -> None:
        for inner_id, job in list(self._tandem_exit_jobs.items()):
            phase = str(job["phase"])
            outer_id = int(job["outer_id"])
            inner_slot = job["inner_slot"]
            temp_position = job["temp_position"]
            if not isinstance(inner_slot, tuple) or not isinstance(temp_position, tuple):
                del self._tandem_exit_jobs[inner_id]
                continue
            inner_vehicle = self.vehicle_manager.get_vehicle(inner_id)
            outer_vehicle = self.vehicle_manager.get_vehicle(outer_id)

            if outer_vehicle is None:
                del self._tandem_exit_jobs[inner_id]
                continue

            if phase == "OUTER_MOVING_OUT":
                if outer_vehicle.position != temp_position or outer_vehicle.path:
                    continue
                outer_vehicle.status = VehicleStatus.WAITING
                outer_vehicle.wait_reason = WaitReason.GUARD_ESCORT
                if inner_vehicle is not None:
                    Logger.log(
                        f"[Guard] Outer motorbike #{outer_id} cleared access; "
                        f"inner #{inner_id} can exit"
                    )
                    self._tandem_exit_jobs[inner_id]["phase"] = "INNER_EXITING"
                    self.start_exit(inner_id)
                    self._reserve_tandem_inner_slot_for_outer(outer_vehicle, inner_slot)
                else:
                    del self._tandem_exit_jobs[inner_id]

            elif phase == "INNER_EXITING":
                outer_slot = job["outer_slot"]
                if not isinstance(outer_slot, tuple):
                    del self._tandem_exit_jobs[inner_id]
                    continue
                if (
                    inner_vehicle is not None
                    and inner_vehicle.position in {inner_slot, outer_slot}
                ):
                    continue
                outer_vehicle.wait_time = 0.0
                self.parking_manager.assign_slot(
                    outer_vehicle,
                    inner_slot,
                    self.map_manager.get_state(),
                )
                path = self._path_to_parking_slot(
                    outer_vehicle.position,
                    inner_slot,
                    outer_vehicle.id,
                )
                if path:
                    outer_vehicle.path = path
                    outer_vehicle.status = VehicleStatus.MOVING
                    outer_vehicle.wait_reason = WaitReason.GUARD_ESCORT
                    self._tandem_exit_jobs[inner_id]["phase"] = "OUTER_RETURNING_INNER"
                    Logger.log(
                        f"[Guard] Returning outer motorbike #{outer_id} to inner slot {inner_slot}"
                    )
                else:
                    outer_vehicle.position = inner_slot
                    outer_vehicle.path = []
                    outer_vehicle.status = VehicleStatus.ARRIVED
                    outer_vehicle.wait_reason = WaitReason.GUARD_ESCORT
                    self._tandem_exit_jobs[inner_id]["phase"] = "OUTER_RETURNING_INNER"
                    Logger.log(
                        f"[Guard] Directly repositioned outer motorbike #{outer_id} "
                        f"to inner slot {inner_slot}"
                    )

            elif phase == "OUTER_RETURNING_INNER":
                if outer_vehicle.position != inner_slot or outer_vehicle.path:
                    continue
                self._validate_and_apply_parking(outer_vehicle)
                del self._tandem_exit_jobs[inner_id]

    def _skip_standard_update_for_tandem_job(self, vehicle: Vehicle) -> bool:
        for inner_id, job in self._tandem_exit_jobs.items():
            outer_id = int(job["outer_id"])
            phase = str(job["phase"])
            if vehicle.id == inner_id and phase == "OUTER_MOVING_OUT":
                return True
            if vehicle.id == outer_id and phase in {
                "OUTER_MOVING_OUT",
                "INNER_EXITING",
                "OUTER_RETURNING_INNER",
            }:
                return vehicle.status in {
                    VehicleStatus.WAITING,
                    VehicleStatus.ARRIVED,
                }
        return False

    def _temporary_drive_cell_for_tandem(
        self,
        outer_slot: tuple[int, int],
        excluded_vehicle_ids: set[int],
        inner_slot: tuple[int, int] | None = None,
    ) -> tuple[int, int] | None:
        occupied_positions = {
            vehicle.position
            for vehicle in self.vehicle_manager.get_all_vehicles()
            if vehicle.id not in excluded_vehicle_ids
        }
        exit_delta = None
        if inner_slot is not None:
            exit_delta = (
                outer_slot[0] - inner_slot[0],
                outer_slot[1] - inner_slot[1],
            )
        candidates: list[tuple[int, int]] = []

        def is_clear_temporary_cell(position: tuple[int, int]) -> bool:
            if position in occupied_positions:
                return False
            slot = self.map_manager.get_state().parking_slots.get(position)
            if slot is None:
                return self.map_manager.is_drive_cell(position)
            return (
                slot.slot_type == VehicleType.MOTORBIKE
                and not slot.is_occupied
                and not slot.is_reserved
                and position != inner_slot
                and position != outer_slot
            )

        for neighbor in self.map_manager.get_state().intersection_neighbors.get(outer_slot, []):
            if is_clear_temporary_cell(neighbor):
                candidates.append(neighbor)
        from utils.grid_utils import get_neighbors

        for neighbor in get_neighbors(
            outer_slot,
            self.map_manager.get_state().rows,
            self.map_manager.get_state().cols,
        ):
            if (
                is_clear_temporary_cell(neighbor)
                and neighbor not in candidates
            ):
                candidates.append(neighbor)
        if not candidates:
            return None
        candidates.sort(
            key=lambda neighbor: (
                exit_delta is not None
                and (
                    neighbor[0] - outer_slot[0],
                    neighbor[1] - outer_slot[1],
                )
                == exit_delta,
                neighbor in self.map_manager.get_state().parking_slots,
                abs(neighbor[0] - outer_slot[0]) + abs(neighbor[1] - outer_slot[1]),
            )
        )
        return candidates[0]

    def _reserve_tandem_inner_slot_for_outer(
        self,
        outer_vehicle: Vehicle,
        inner_slot: tuple[int, int],
    ) -> None:
        map_state = self.map_manager.get_state()
        if outer_vehicle.assigned_slot is not None and outer_vehicle.assigned_slot != inner_slot:
            self.parking_manager.release_vehicle_slot(outer_vehicle, map_state)
        slot = map_state.parking_slots.get(inner_slot)
        if slot is not None:
            slot.is_reserved = True
            slot.reserved_by = outer_vehicle.id
            if slot.occupied_by == outer_vehicle.id:
                slot.is_occupied = False
                slot.occupied_by = None
        outer_vehicle.assigned_slot = inner_slot

    def _path_to_parking_slot(
        self,
        start: tuple[int, int],
        slot: tuple[int, int],
        vehicle_id: int,
    ) -> list[tuple[int, int]]:
        outer_slot = self.map_manager.get_state().motorbike_inner_to_outer.get(slot)
        if outer_slot is None:
            return find_path(
                self.current_algorithm,
                start,
                slot,
                self.map_manager,
                self._occupied_positions(vehicle_id),
            )

        path_to_outer = find_path(
            self.current_algorithm,
            start,
            outer_slot,
            self.map_manager,
            self._occupied_positions(vehicle_id),
        )
        if not path_to_outer:
            return []
        return path_to_outer + [slot]

    def _path_from_parking_position_to_goal(
        self,
        start: tuple[int, int],
        goal: tuple[int, int],
        vehicle_id: int,
    ) -> list[tuple[int, int]]:
        outer_slot = self.map_manager.get_state().motorbike_inner_to_outer.get(start)
        if outer_slot is None:
            return find_path(
                self.current_algorithm,
                start,
                goal,
                self.map_manager,
                self._occupied_positions(vehicle_id),
            )

        blocked_positions = self._occupied_positions(vehicle_id)
        if outer_slot in blocked_positions:
            return []

        path_from_outer = find_path(
            self.current_algorithm,
            outer_slot,
            goal,
            self.map_manager,
            blocked_positions,
        )
        if not path_from_outer:
            return []
        return [outer_slot] + path_from_outer

    def _vehicle_at(self, position: tuple[int, int]) -> Vehicle | None:
        return next(
            (
                vehicle
                for vehicle in self.vehicle_manager.get_all_vehicles()
                if vehicle.position == position
            ),
            None,
        )

    def _occupied_positions(self, excluded_vehicle_id: int | None = None) -> set[tuple[int, int]]:
        return {
            vehicle.position
            for vehicle in self.vehicle_manager.get_all_vehicles()
            if vehicle.id != excluded_vehicle_id
            and not self._is_temporarily_held_for_tandem_exit(vehicle.id)
        }

    def _is_temporarily_held_for_tandem_exit(self, vehicle_id: int) -> bool:
        vehicle = self.vehicle_manager.get_vehicle(vehicle_id)
        if (
            vehicle is not None
            and vehicle.status == VehicleStatus.WAITING
            and vehicle.wait_reason == WaitReason.GUARD_ESCORT
        ):
            return True
        for job in self._tandem_exit_jobs.values():
            if (
                int(job["outer_id"]) == vehicle_id
                and str(job["phase"]) == "INNER_EXITING"
            ):
                return True
        return False

    def _get_available_guard(self) -> Guard:
        available_guard = next(
            (guard for guard in self.guards if guard.task == "IDLE"),
            None,
        )
        if available_guard is not None:
            return available_guard

        home_position = self.map_manager.get_state().gate_cells[0]
        guard = Guard(
            id=self._next_guard_id,
            position=home_position,
            home_position=home_position,
        )
        self._next_guard_id += 1
        self.guards.append(guard)
        Logger.log(f"[Guard] Guard #{guard.id} entered service at {guard.home_position}")
        return guard

    def _dispatch_violation_guard(self, vehicle: Vehicle) -> None:
        guard = self._get_available_guard()
        path = find_path(
            self.current_algorithm,
            guard.position,
            vehicle.position,
            self.map_manager,
            self._occupied_positions(vehicle.id),
        )
        guard.target_vehicle_id = vehicle.id
        guard.target_position = vehicle.position
        guard.task = "VIOLATION"
        guard.path = path
        guard.is_active = True
        Logger.log(
            f"[Guard] Guard #{guard.id} dispatched to Vehicle #{vehicle.id} "
            f"at {vehicle.position}"
        )

    def _update_guards(self, delta_time: float) -> None:
        for guard in self.guards:
            if not guard.is_active:
                continue

            guard.move_timer += delta_time
            if guard.move_timer < VEHICLE_MOVE_INTERVAL:
                continue
            guard.move_timer = 0.0

            if guard.path:
                next_position = guard.path.pop(0)
                guard.facing_delta = (
                    next_position[0] - guard.position[0],
                    next_position[1] - guard.position[1],
                )
                guard.position = next_position
                guard.is_walking = True
                continue
            guard.is_walking = False

            if guard.task == "VIOLATION":
                self._handle_guard_reached_violation(guard)
            elif guard.task == "RETURNING":
                guard.task = "IDLE"
                guard.is_active = False
                guard.target_vehicle_id = None
                guard.target_position = None
                guard.is_walking = False
                Logger.log(f"[Guard] Guard #{guard.id} returned to post")

    def _handle_guard_reached_violation(self, guard: Guard) -> None:
        if guard.target_vehicle_id is None:
            self._return_guard_home(guard)
            return

        vehicle = self.vehicle_manager.get_vehicle(guard.target_vehicle_id)
        if vehicle is None:
            self._return_guard_home(guard)
            return

        has_active_block = vehicle.position in self.map_manager.get_state().dynamic_blocks
        if vehicle.status == VehicleStatus.PARKED:
            Logger.log(
                f"[Guard] Guard #{guard.id} cancelled violation escort for "
                f"Vehicle #{vehicle.id}; vehicle already parked"
            )
            self._return_guard_home(guard)
            return

        if (
            guard.target_position is not None
            and guard.target_position != vehicle.position
            and not has_active_block
            and not (
                vehicle.status == VehicleStatus.MANUAL
                and vehicle.wait_time >= MANUAL_ENFORCE_THRESHOLD
            )
        ):
            Logger.log(
                f"[Guard] Guard #{guard.id} cancelled stale violation escort for "
                f"Vehicle #{vehicle.id}"
            )
            self._return_guard_home(guard)
            return

        if (
            vehicle.status == VehicleStatus.MANUAL
            and not has_active_block
            and vehicle.wait_time < MANUAL_ENFORCE_THRESHOLD
        ):
            Logger.log(
                f"[Guard] Guard #{guard.id} cancelled violation escort for "
                f"Vehicle #{vehicle.id}; violation cleared"
            )
            self._return_guard_home(guard)
            return

        if has_active_block:
            self.map_manager.remove_dynamic_block(vehicle.position)

        self.vehicle_manager.set_status(vehicle.id, VehicleStatus.WAITING)
        self.vehicle_manager.set_wait_reason(vehicle.id, WaitReason.GUARD_ESCORT)
        Logger.log(
            f"[Guard] Guard #{guard.id} escorting Vehicle #{vehicle.id} "
            "to a valid slot"
        )
        self._assign_and_path(vehicle)
        self._return_guard_home(guard)

    def _return_guard_home(self, guard: Guard) -> None:
        guard.target_vehicle_id = None
        guard.target_position = guard.home_position
        guard.task = "RETURNING"
        guard.path = find_path(
            self.current_algorithm,
            guard.position,
            guard.home_position,
            self.map_manager,
            self._occupied_positions(None),
        )
        guard.is_active = True
        guard.is_walking = bool(guard.path)
        if not guard.path and guard.position == guard.home_position:
            guard.task = "IDLE"
            guard.is_active = False
            guard.target_position = None
            guard.is_walking = False
            Logger.log(f"[Guard] Guard #{guard.id} returned to post")
