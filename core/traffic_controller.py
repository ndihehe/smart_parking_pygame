from ai.decision.priority_rule import calculate_priority, resolve_conflict
from ai.pathfinding.router import find_path
from config import (
    INTERSECTION_CONGESTION_TIME,
    MIN_WAITING_VEHICLES,
    REROUTE_WAIT_THRESHOLD,
    WAIT_THRESHOLD,
)
from core.map_manager import MapManager
from models.enums import AlgorithmType, VehicleStatus, WaitReason
from models.guard import Guard
from models.vehicle import Vehicle
from utils.logger import Logger


class TrafficController:
    def __init__(self) -> None:
        self._intersection_timers: dict[tuple[int, int], float] = {}

    def update(
        self,
        vehicles: list[Vehicle],
        map_manager: MapManager,
        delta_time: float,
        guards: list[Guard] | None = None,
        algorithm: str | AlgorithmType = AlgorithmType.ASTAR,
    ) -> None:
        map_state = map_manager.state
        occupied_positions = {
            vehicle.position
            for vehicle in vehicles
            if vehicle.status != VehicleStatus.VIOLATION
        }
        waiting_by_position: dict[tuple[int, int], list[Vehicle]] = {}
        for vehicle in vehicles:
            if vehicle.status == VehicleStatus.WAITING:
                waiting_by_position.setdefault(vehicle.position, []).append(vehicle)

        for intersection in map_state.intersection_cells:
            neighbors = map_state.intersection_neighbors[intersection]
            waiting_vehicles: list[Vehicle] = []
            waiting_vehicles.extend(waiting_by_position.get(intersection, []))
            for neighbor in neighbors:
                waiting_vehicles.extend(waiting_by_position.get(neighbor, []))

            if waiting_vehicles:
                self._intersection_timers[intersection] = (
                    self._intersection_timers.get(intersection, 0.0) + delta_time
                )
                for vehicle in waiting_vehicles:
                    if vehicle.wait_reason == WaitReason.NONE:
                        vehicle.wait_reason = WaitReason.WAITING_FOR_INTERSECTION

            if (
                len(waiting_vehicles) >= MIN_WAITING_VEHICLES
                or any(vehicle.wait_time >= WAIT_THRESHOLD for vehicle in waiting_vehicles)
                or self._intersection_timers.get(intersection, 0.0)
                >= INTERSECTION_CONGESTION_TIME
            ):
                for vehicle in waiting_vehicles:
                    vehicle.wait_reason = WaitReason.TRAFFIC_CONGESTION
                self._handle_congestion(
                    intersection,
                    waiting_vehicles,
                    map_manager,
                    occupied_positions,
                    guards,
                    algorithm,
                )

        targets: dict[tuple[int, int], list[Vehicle]] = {}
        for vehicle in vehicles:
            if vehicle.status == VehicleStatus.MOVING and vehicle.path:
                next_cell = vehicle.path[0]
                targets.setdefault(next_cell, []).append(vehicle)

        self._resolve_head_on_swaps(
            vehicles,
            map_manager,
            guards,
            algorithm,
            delta_time,
        )

        for target_cell, candidate_vehicles in targets.items():
            if len(candidate_vehicles) > 1:
                winner = resolve_conflict(candidate_vehicles, target_cell)
                winner.wait_time = 0.0
                winner.wait_reason = (
                    WaitReason.EXITING
                    if winner.wait_reason == WaitReason.EXITING
                    else WaitReason.NONE
                )
                for vehicle in candidate_vehicles:
                    if vehicle != winner:
                        vehicle.status = VehicleStatus.WAITING
                        vehicle.wait_reason = (
                            WaitReason.EXITING
                            if vehicle.wait_reason == WaitReason.EXITING
                            else WaitReason.YIELDING
                        )
                        vehicle.wait_time += delta_time

    def _resolve_head_on_swaps(
        self,
        vehicles: list[Vehicle],
        map_manager: MapManager,
        guards: list[Guard] | None,
        algorithm: str | AlgorithmType,
        delta_time: float,
    ) -> None:
        moving = [
            vehicle
            for vehicle in vehicles
            if vehicle.status == VehicleStatus.MOVING and vehicle.path
        ]
        by_position = {vehicle.position: vehicle for vehicle in moving}
        handled: set[int] = set()

        for vehicle in moving:
            if vehicle.id in handled or not vehicle.path:
                continue
            next_cell = vehicle.path[0]
            other = by_position.get(next_cell)
            if (
                other is None
                or other.id == vehicle.id
                or other.id in handled
                or not other.path
                or other.path[0] != vehicle.position
            ):
                continue

            winner = resolve_conflict([vehicle, other], next_cell)
            loser = other if winner == vehicle else vehicle
            yield_cell = self._find_yield_cell(loser, winner, vehicles, map_manager)
            if yield_cell is not None:
                loser.path = [yield_cell] + loser.path
                loser.status = VehicleStatus.MOVING
                loser.wait_reason = (
                    WaitReason.EXITING
                    if loser.wait_reason == WaitReason.EXITING
                    else WaitReason.YIELDING
                )
                winner.status = VehicleStatus.WAITING
                winner.wait_reason = (
                    WaitReason.EXITING
                    if winner.wait_reason == WaitReason.EXITING
                    else WaitReason.YIELDING
                )
                winner.wait_time += delta_time
                Logger.log(
                    f"[TrafficController] Head-on avoided: Vehicle #{loser.id} "
                    f"moves aside to {yield_cell}, Vehicle #{winner.id} waits"
                )
            else:
                loser.status = VehicleStatus.WAITING
                loser.wait_reason = (
                    WaitReason.EXITING
                    if loser.wait_reason == WaitReason.EXITING
                    else WaitReason.YIELDING
                )
                loser.wait_time += delta_time
                winner.wait_time = 0.0
                winner.wait_reason = (
                    WaitReason.EXITING
                    if winner.wait_reason == WaitReason.EXITING
                    else WaitReason.NONE
                )
                Logger.log(
                    f"[TrafficController] No yield cell: Vehicle "
                    f"#{loser.id} aside, Vehicle #{winner.id} goes first"
                )
            handled.add(vehicle.id)
            handled.add(other.id)

    def _find_yield_cell(
        self,
        loser: Vehicle,
        winner: Vehicle,
        vehicles: list[Vehicle],
        map_manager: MapManager,
    ) -> tuple[int, int] | None:
        occupied_positions = {
            vehicle.position
            for vehicle in vehicles
            if vehicle.id not in {loser.id, winner.id}
            and vehicle.status != VehicleStatus.VIOLATION
        }
        forbidden = occupied_positions | {winner.position, winner.path[0], loser.path[0]}

        for neighbor in map_manager.state.intersection_neighbors.get(loser.position, []):
            if neighbor not in forbidden and map_manager.is_drive_cell(neighbor):
                return neighbor

        from utils.grid_utils import get_neighbors

        candidates = get_neighbors(
            loser.position,
            map_manager.state.rows,
            map_manager.state.cols,
        )
        for neighbor in candidates:
            if neighbor not in forbidden and map_manager.is_drive_cell(neighbor):
                return neighbor
        return None

    def _handle_congestion(
        self,
        intersection: tuple[int, int],
        waiting_vehicles: list[Vehicle],
        map_manager: MapManager,
        occupied_positions: set[tuple[int, int]],
        guards: list[Guard] | None,
        algorithm: str | AlgorithmType,
    ) -> None:
        if not waiting_vehicles:
            return

        if any(vehicle.wait_time >= REROUTE_WAIT_THRESHOLD for vehicle in waiting_vehicles):
            map_manager.add_dynamic_block(intersection)
            occupied_positions = {
                other_vehicle.position
                for other_vehicle in waiting_vehicles
            }
            for vehicle in waiting_vehicles:
                vehicle.status = VehicleStatus.REROUTING
                if vehicle.assigned_slot is not None:
                    blocked_positions = occupied_positions - {vehicle.position}
                    new_path = find_path(
                        algorithm,
                        vehicle.position,
                        vehicle.assigned_slot,
                        map_manager,
                        blocked_positions,
                    )
                    if new_path:
                        vehicle.path = new_path
                        vehicle.status = VehicleStatus.MOVING
                        vehicle.wait_reason = WaitReason.NONE
                        vehicle.wait_time = 0.0
                    else:
                        vehicle.wait_reason = WaitReason.NO_PATH
                else:
                    vehicle.status = VehicleStatus.WAITING
                    vehicle.wait_reason = WaitReason.NO_SLOT
            Logger.log(
                f"[TrafficController] Congestion at {intersection}, "
                f"rerouting affected vehicles"
            )
            self._intersection_timers[intersection] = 0.0
            return

        neighbors = map_manager.state.intersection_neighbors[intersection]
        all_directions_blocked = all(
            not map_manager.is_passable(neighbor)
            or neighbor in occupied_positions
            for neighbor in neighbors
        )

        if not all_directions_blocked:
            winner = max(
                waiting_vehicles,
                key=lambda vehicle: calculate_priority(
                    vehicle,
                    vehicle.assigned_slot
                    if vehicle.assigned_slot is not None
                    else intersection,
                ),
            )
            for vehicle in waiting_vehicles:
                vehicle.status = (
                    VehicleStatus.MOVING
                    if vehicle == winner
                    else VehicleStatus.WAITING
                )
                vehicle.wait_reason = (
                    WaitReason.NONE if vehicle == winner else WaitReason.YIELDING
                )
                if vehicle == winner:
                    vehicle.wait_time = 0.0
            Logger.log(
                f"[TrafficController] Vehicle #{winner.id} allowed through "
                f"{intersection} by priority"
            )

    def handle_obstacle(
        self,
        blocked_cell: tuple[int, int],
        vehicles: list[Vehicle],
        map_manager: MapManager,
        algorithm: str | AlgorithmType = AlgorithmType.ASTAR,
    ) -> None:
        map_manager.add_dynamic_block(blocked_cell)
        rerouted_count = 0
        occupied_positions = {
            vehicle.position
            for vehicle in vehicles
            if vehicle.status != VehicleStatus.VIOLATION
        }

        for vehicle in vehicles:
            if vehicle.status == VehicleStatus.MOVING and blocked_cell in vehicle.path:
                vehicle.status = VehicleStatus.REROUTING
                if vehicle.assigned_slot is not None:
                    new_path = find_path(
                        algorithm,
                        vehicle.position,
                        vehicle.assigned_slot,
                        map_manager,
                        occupied_positions - {vehicle.position},
                    )
                    if new_path:
                        vehicle.path = new_path
                        vehicle.status = VehicleStatus.MOVING
                        vehicle.wait_reason = WaitReason.NONE
                        vehicle.wait_time = 0.0
                    else:
                        vehicle.wait_reason = WaitReason.NO_PATH
                else:
                    vehicle.status = VehicleStatus.WAITING
                    vehicle.wait_reason = WaitReason.NO_SLOT
                rerouted_count += 1

        Logger.log(
            f"[TrafficController] Obstacle at {blocked_cell}, "
            f"{rerouted_count} vehicles rerouted"
        )

    def _dispatch_traffic_guard(
        self,
        position: tuple[int, int],
        map_manager: MapManager,
        guards: list[Guard] | None,
        algorithm: str | AlgorithmType = AlgorithmType.ASTAR,
    ) -> None:
        return
