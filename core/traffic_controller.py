from ai.decision.priority_rule import calculate_priority, resolve_conflict
from ai.pathfinding.astar import astar
from config import (
    INTERSECTION_CONGESTION_TIME,
    MIN_WAITING_VEHICLES,
    REROUTE_WAIT_THRESHOLD,
)
from core.map_manager import MapManager
from models.enums import CellType, VehicleStatus
from models.vehicle import Vehicle
from utils.grid_utils import get_neighbors
from utils.logger import Logger


class TrafficController:
    def __init__(self) -> None:
        self._intersection_timers: dict[tuple[int, int], float] = {}

    def update(
        self,
        vehicles: list[Vehicle],
        map_manager: MapManager,
        delta_time: float,
    ) -> None:
        intersections: list[tuple[int, int]] = []
        for row in range(map_manager.state.rows):
            for col in range(map_manager.state.cols):
                if map_manager.state.grid[row][col] == CellType.INTERSECTION:
                    intersections.append((row, col))

        for intersection in intersections:
            neighbors = get_neighbors(
                intersection,
                map_manager.state.rows,
                map_manager.state.cols,
            )
            waiting_vehicles = [
                vehicle
                for vehicle in vehicles
                if vehicle.status == VehicleStatus.WAITING
                and (
                    vehicle.position == intersection
                    or vehicle.position in neighbors
                )
            ]

            if waiting_vehicles:
                self._intersection_timers[intersection] = (
                    self._intersection_timers.get(intersection, 0.0) + delta_time
                )

            if (
                len(waiting_vehicles) >= MIN_WAITING_VEHICLES
                or self._intersection_timers.get(intersection, 0.0)
                >= INTERSECTION_CONGESTION_TIME
            ):
                self._handle_congestion(intersection, waiting_vehicles, map_manager)

        targets: dict[tuple[int, int], list[Vehicle]] = {}
        for vehicle in vehicles:
            if vehicle.status == VehicleStatus.MOVING and vehicle.path:
                next_cell = vehicle.path[0]
                targets.setdefault(next_cell, []).append(vehicle)

        for target_cell, candidate_vehicles in targets.items():
            if len(candidate_vehicles) > 1:
                winner = resolve_conflict(candidate_vehicles, target_cell)
                for vehicle in candidate_vehicles:
                    if vehicle != winner:
                        vehicle.status = VehicleStatus.WAITING
                        vehicle.wait_time += delta_time

    def _handle_congestion(
        self,
        intersection: tuple[int, int],
        waiting_vehicles: list[Vehicle],
        map_manager: MapManager,
    ) -> None:
        if not waiting_vehicles:
            return

        if any(vehicle.wait_time >= REROUTE_WAIT_THRESHOLD for vehicle in waiting_vehicles):
            map_manager.add_dynamic_block(intersection)
            for vehicle in waiting_vehicles:
                vehicle.status = VehicleStatus.REROUTING
                if vehicle.assigned_slot is not None:
                    new_path = astar(vehicle.position, vehicle.assigned_slot, map_manager)
                    if new_path:
                        vehicle.path = new_path
                        vehicle.status = VehicleStatus.MOVING
                    else:
                        vehicle.status = VehicleStatus.WAITING
                else:
                    vehicle.status = VehicleStatus.WAITING
            Logger.log(
                f"[TrafficController] Congestion at {intersection}, "
                f"rerouting affected vehicles"
            )
            self._intersection_timers[intersection] = 0.0
            return

        neighbors = get_neighbors(
            intersection,
            map_manager.state.rows,
            map_manager.state.cols,
        )
        all_directions_blocked = all(
            not map_manager.is_passable(neighbor)
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
            Logger.log(
                f"[TrafficController] Vehicle #{winner.id} allowed through "
                f"{intersection} by priority"
            )

    def handle_obstacle(
        self,
        blocked_cell: tuple[int, int],
        vehicles: list[Vehicle],
        map_manager: MapManager,
    ) -> None:
        map_manager.add_dynamic_block(blocked_cell)
        rerouted_count = 0

        for vehicle in vehicles:
            if vehicle.status == VehicleStatus.MOVING and blocked_cell in vehicle.path:
                vehicle.status = VehicleStatus.REROUTING
                if vehicle.assigned_slot is not None:
                    new_path = astar(vehicle.position, vehicle.assigned_slot, map_manager)
                    if new_path:
                        vehicle.path = new_path
                        vehicle.status = VehicleStatus.MOVING
                    else:
                        vehicle.status = VehicleStatus.WAITING
                else:
                    vehicle.status = VehicleStatus.WAITING
                rerouted_count += 1

        Logger.log(
            f"[TrafficController] Obstacle at {blocked_cell}, "
            f"{rerouted_count} vehicles rerouted"
        )
