import pygame
import unittest

from config import (
    CELL_SIZE,
    MANUAL_ENFORCE_THRESHOLD,
    VEHICLE_MOVE_INTERVAL,
    WAIT_THRESHOLD,
)
from core.game_controller import GameController
from models.enums import VehicleStatus, VehicleType, WaitReason
from ui.input_handler import InputHandler
from utils.grid_utils import get_neighbors


MAP_PATH = "data/maps/default_map.txt"


def drive_run(gc: GameController) -> tuple[tuple[int, int], ...]:
    state = gc.map_manager.get_state()
    for row in range(state.rows):
        for col in range(state.cols - 2):
            positions = ((row, col), (row, col + 1), (row, col + 2))
            if all(gc.map_manager.is_drive_cell(position) for position in positions):
                return positions
    raise AssertionError("Map has no three-cell drive run")


def turning_drive_path(
    gc: GameController,
) -> tuple[tuple[int, int], tuple[int, int], tuple[int, int]]:
    state = gc.map_manager.get_state()
    for row in range(state.rows):
        for col in range(state.cols):
            current = (row, col)
            if not gc.map_manager.is_drive_cell(current):
                continue
            for first in get_neighbors(current, state.rows, state.cols):
                if not gc.map_manager.is_drive_cell(first):
                    continue
                first_delta = (first[0] - row, first[1] - col)
                for second in get_neighbors(first, state.rows, state.cols):
                    second_delta = (second[0] - first[0], second[1] - first[1])
                    if (
                        second != current
                        and gc.map_manager.is_drive_cell(second)
                        and first_delta[0] * second_delta[0]
                        + first_delta[1] * second_delta[1]
                        == 0
                    ):
                        return current, first, second
    raise AssertionError("Map has no turning drive path")


class TestTrafficController(unittest.TestCase):
    def test_manual_wrong_road_parking_creates_dynamic_block(self) -> None:
        gc = GameController(MAP_PATH)
        vehicle = gc.spawn_vehicle(VehicleType.CAR)
        gc.set_manual(vehicle.id)
        road_position = drive_run(gc)[0]
        vehicle.position = road_position
        result = gc.confirm_parking(vehicle.id)
        self.assertEqual(result, "ILLEGAL_ROAD")
        self.assertIn(road_position, gc.map_manager.get_state().dynamic_blocks)
        self.assertEqual(vehicle.status, VehicleStatus.VIOLATION)

    def test_manual_move_from_wrong_road_removes_dynamic_block(self) -> None:
        gc = GameController(MAP_PATH)
        vehicle = gc.spawn_vehicle(VehicleType.CAR)
        gc.set_manual(vehicle.id)
        road_position, next_position, _ = drive_run(gc)
        vehicle.position = road_position
        gc.confirm_parking(vehicle.id)
        gc.set_manual(vehicle.id)

        direction = (
            next_position[0] - road_position[0],
            next_position[1] - road_position[1],
        )
        gc.move_manual(vehicle.id, direction)

        self.assertEqual(vehicle.position, next_position)
        self.assertNotIn(road_position, gc.map_manager.get_state().dynamic_blocks)

    def test_violation_guard_returns_if_manual_vehicle_clears_block(self) -> None:
        gc = GameController(MAP_PATH)
        vehicle = gc.spawn_vehicle(VehicleType.CAR)
        gc.set_manual(vehicle.id)
        road_position, next_position, _ = drive_run(gc)
        vehicle.position = road_position
        gc.confirm_parking(vehicle.id)
        gc.set_manual(vehicle.id)
        gc.move_manual(
            vehicle.id,
            (
                next_position[0] - road_position[0],
                next_position[1] - road_position[1],
            ),
        )
        guard = gc.guards[0]
        guard.path = []

        gc._handle_guard_reached_violation(guard)

        self.assertEqual(vehicle.status, VehicleStatus.MANUAL)
        self.assertIn(guard.task, {"RETURNING", "IDLE"})
        self.assertIsNone(guard.target_vehicle_id)

    def test_violation_guard_forces_manual_vehicle_after_timeout(self) -> None:
        gc = GameController(MAP_PATH)
        vehicle = gc.spawn_vehicle(VehicleType.CAR)
        gc.set_manual(vehicle.id)
        road_position, next_position, _ = drive_run(gc)
        vehicle.position = road_position
        gc.confirm_parking(vehicle.id)
        gc.set_manual(vehicle.id)
        gc.move_manual(
            vehicle.id,
            (
                next_position[0] - road_position[0],
                next_position[1] - road_position[1],
            ),
        )
        vehicle.wait_time = MANUAL_ENFORCE_THRESHOLD
        guard = gc.guards[0]
        guard.path = []

        gc._handle_guard_reached_violation(guard)

        self.assertNotEqual(vehicle.status, VehicleStatus.MANUAL)
        self.assertEqual(vehicle.wait_time, 0.0)

    def test_wrong_type_parking_dispatches_guard_and_reassigns(self) -> None:
        gc = GameController(MAP_PATH)
        vehicle = gc.spawn_vehicle(VehicleType.MOTORBIKE)
        gc.set_manual(vehicle.id)
        vehicle.position = gc.map_manager.get_state().car_slots[0]
        result = gc.confirm_parking(vehicle.id)
        self.assertEqual(result, "WRONG_TYPE")
        self.assertTrue(gc.guards[0].is_active)
        for _ in range(80):
            gc.update(0.3)
            if vehicle.status == VehicleStatus.MOVING and vehicle.assigned_slot is not None:
                break
        self.assertIsNotNone(vehicle.assigned_slot)
        self.assertEqual(gc.map_manager.get_state().parking_slots[vehicle.assigned_slot].slot_type, VehicleType.MOTORBIKE)
        for _ in range(80):
            gc.update(0.3)
            if gc.guards[0].task == "IDLE":
                break
        self.assertEqual(gc.guards[0].task, "IDLE")
        self.assertEqual(gc.guards[0].position, gc.guards[0].home_position)

    def test_multiple_wrong_type_parking_dispatches_multiple_guards(self) -> None:
        gc = GameController(MAP_PATH)
        first = gc.spawn_vehicle(VehicleType.MOTORBIKE)
        second = gc.spawn_vehicle(VehicleType.MOTORBIKE)
        gc.set_manual(first.id)
        gc.set_manual(second.id)
        first.position, second.position = gc.map_manager.get_state().car_slots[:2]
        gc.confirm_parking(first.id)
        gc.confirm_parking(second.id)
        active_guards = [guard for guard in gc.guards if guard.task == "VIOLATION"]
        self.assertEqual(len(active_guards), 2)

    def test_reroute_failure_releases_old_slot_and_finds_another(self) -> None:
        gc = GameController(MAP_PATH)
        vehicle = gc.spawn_vehicle(VehicleType.CAR)
        old_slot = vehicle.assigned_slot
        gc.map_manager.add_dynamic_block(old_slot)
        vehicle.status = VehicleStatus.REROUTING
        gc.update(0.1)
        self.assertFalse(gc.map_manager.get_state().parking_slots[old_slot].is_reserved)
        self.assertTrue(vehicle.assigned_slot != old_slot or vehicle.status == VehicleStatus.WAITING)

    def test_waiting_yielding_vehicle_resumes_when_next_cell_clear(self) -> None:
        gc = GameController(MAP_PATH)
        start, next_position, _ = drive_run(gc)
        vehicle = gc.vehicle_manager.spawn_vehicle(VehicleType.CAR, start)
        vehicle.assigned_slot = gc.map_manager.get_state().car_slots[0]
        vehicle.path = [next_position]
        vehicle.status = VehicleStatus.WAITING
        vehicle.wait_reason = WaitReason.YIELDING
        vehicle.wait_time = VEHICLE_MOVE_INTERVAL
        gc._recover_waiting_vehicle(vehicle)
        self.assertEqual(vehicle.status, VehicleStatus.MOVING)
        self.assertEqual(vehicle.wait_reason, WaitReason.NONE)

    def test_unavailable_assigned_slot_releases_and_finds_another(self) -> None:
        gc = GameController(MAP_PATH)
        vehicle = gc.spawn_vehicle(VehicleType.CAR)
        old_slot = vehicle.assigned_slot
        state = gc.map_manager.get_state()
        state.parking_slots[old_slot].is_occupied = True
        state.parking_slots[old_slot].occupied_by = 999
        vehicle.status = VehicleStatus.REROUTING
        gc.update(0.1)
        self.assertNotEqual(vehicle.assigned_slot, old_slot)
        self.assertTrue(
            vehicle.status in (VehicleStatus.MOVING, VehicleStatus.WAITING)
        )

    def test_t_key_toggles_auto_spawn(self) -> None:
        gc = GameController(MAP_PATH)
        handler = InputHandler(gc)
        handler.handle_events([pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_t})])
        self.assertTrue(gc._auto_spawn_enabled)

    def test_number_keys_select_pathfinding_algorithm(self) -> None:
        gc = GameController(MAP_PATH)
        handler = InputHandler(gc)
        cases = [
            (pygame.K_1, "bfs"),
            (pygame.K_2, "dfs"),
            (pygame.K_3, "greedy"),
            (pygame.K_4, "astar"),
        ]
        for key, expected_algorithm in cases:
            handler.handle_events([pygame.event.Event(pygame.KEYDOWN, {"key": key})])
            self.assertEqual(gc.current_algorithm, expected_algorithm)

    def test_spawn_uses_left_entry_gates_only(self) -> None:
        gc = GameController(MAP_PATH)
        first = gc.spawn_vehicle(VehicleType.CAR)
        second = gc.spawn_vehicle(VehicleType.CAR)
        self.assertEqual(first.position[1], 0)
        self.assertEqual(second.position[1], 0)

    def test_full_vehicle_type_lot_blocks_spawn(self) -> None:
        gc = GameController(MAP_PATH)
        state = gc.map_manager.get_state()
        for slot in state.parking_slots.values():
            if slot.slot_type == VehicleType.CAR:
                slot.is_occupied = True
                slot.occupied_by = 999
        vehicle = gc.spawn_vehicle(VehicleType.CAR)
        self.assertIsNone(vehicle)

    def test_left_click_switches_vehicle_to_manual(self) -> None:
        gc = GameController(MAP_PATH)
        vehicle = gc.spawn_vehicle(VehicleType.CAR)
        handler = InputHandler(gc)
        event = pygame.event.Event(
            pygame.MOUSEBUTTONDOWN,
            {
                "button": 1,
                "pos": (
                    vehicle.position[1] * CELL_SIZE,
                    vehicle.position[0] * CELL_SIZE,
                ),
            },
        )
        handler.handle_events([event])
        self.assertEqual(vehicle.status, VehicleStatus.MANUAL)

    def test_right_click_sends_vehicle_to_right_exit(self) -> None:
        gc = GameController(MAP_PATH)
        vehicle = gc.spawn_vehicle(VehicleType.CAR)
        handler = InputHandler(gc)
        event = pygame.event.Event(
            pygame.MOUSEBUTTONDOWN,
            {
                "button": 3,
                "pos": (
                    vehicle.position[1] * CELL_SIZE,
                    vehicle.position[0] * CELL_SIZE,
                ),
            },
        )
        handler.handle_events([event])
        self.assertEqual(vehicle.wait_reason, WaitReason.EXITING)
        self.assertEqual(vehicle.path[-1][1], gc.map_manager.get_state().cols - 1)

    def test_exiting_vehicle_is_removed_at_right_exit(self) -> None:
        gc = GameController(MAP_PATH)
        vehicle = gc.spawn_vehicle(VehicleType.CAR)
        gc.start_exit(vehicle.id)
        for _ in range(100):
            gc.update(0.3)
            if gc.vehicle_manager.get_vehicle(vehicle.id) is None:
                break
        self.assertIsNone(gc.vehicle_manager.get_vehicle(vehicle.id))

    def test_exiting_vehicle_reroutes_around_blocking_vehicle(self) -> None:
        gc = GameController(MAP_PATH)
        exiting = gc.vehicle_manager.spawn_vehicle(
            VehicleType.CAR,
            gc.map_manager.get_state().entry_gates[0],
        )
        gc.start_exit(exiting.id)
        blocker = gc.vehicle_manager.spawn_vehicle(VehicleType.CAR, exiting.path[0])
        gc.vehicle_manager.set_manual(blocker.id)
        blocked_cell = blocker.position

        gc.update(0.3)

        self.assertEqual(exiting.status, VehicleStatus.MOVING)
        self.assertEqual(exiting.wait_reason, WaitReason.EXITING)
        self.assertTrue(exiting.path)
        self.assertNotEqual(exiting.path[0], blocked_cell)

    def test_exiting_vehicle_waiting_on_exit_gate_is_removed(self) -> None:
        gc = GameController(MAP_PATH)
        vehicle = gc.vehicle_manager.spawn_vehicle(
            VehicleType.CAR,
            gc.map_manager.get_state().exit_gates[0],
        )
        vehicle.status = VehicleStatus.WAITING
        vehicle.wait_reason = WaitReason.EXITING
        vehicle.path = []

        gc.update(0.1)

        self.assertIsNone(gc.vehicle_manager.get_vehicle(vehicle.id))

    def test_vehicle_blocked_by_vehicle_yields_without_reroute_loop(self) -> None:
        gc = GameController(MAP_PATH)
        start, blocked, after = drive_run(gc)
        first = gc.vehicle_manager.spawn_vehicle(VehicleType.CAR, start)
        second = gc.vehicle_manager.spawn_vehicle(VehicleType.CAR, blocked)
        first.path = [blocked, after]
        first.status = VehicleStatus.MOVING
        second.status = VehicleStatus.MANUAL
        gc.vehicle_manager.update(0.3, gc.map_manager.get_state())
        self.assertEqual(first.status, VehicleStatus.WAITING)
        self.assertEqual(first.wait_reason, WaitReason.YIELDING)
        self.assertEqual(first.path, [blocked, after])

    def test_game_controller_keeps_yielding_vehicle_waiting_before_reroute_threshold(self) -> None:
        gc = GameController(MAP_PATH)
        start, blocked, after = drive_run(gc)
        first = gc.vehicle_manager.spawn_vehicle(VehicleType.CAR, start)
        second = gc.vehicle_manager.spawn_vehicle(VehicleType.CAR, blocked)
        first.assigned_slot = gc.map_manager.get_state().car_slots[0]
        first.path = [blocked, after]
        first.status = VehicleStatus.MOVING
        second.status = VehicleStatus.MANUAL
        gc.update(0.3)
        gc.update(0.3)
        self.assertEqual(first.status, VehicleStatus.WAITING)
        self.assertEqual(first.wait_reason, WaitReason.YIELDING)
        self.assertEqual(first.path, [blocked, after])

    def test_cell_conflict_does_not_dispatch_guard(self) -> None:
        gc = GameController(MAP_PATH)
        first_position, target, second_position = drive_run(gc)
        first = gc.vehicle_manager.spawn_vehicle(VehicleType.CAR, first_position)
        second = gc.vehicle_manager.spawn_vehicle(VehicleType.CAR, second_position)
        first.assigned_slot, second.assigned_slot = gc.map_manager.get_state().car_slots[:2]
        first.path = [target]
        second.path = [target]
        first.status = VehicleStatus.MOVING
        second.status = VehicleStatus.MOVING
        gc.traffic_controller.update(
            [first, second],
            gc.map_manager,
            0.1,
            gc.guards,
        )
        self.assertEqual(gc.guards[0].task, "IDLE")
        self.assertIsNone(gc.guards[0].target_position)
        waiting = [vehicle for vehicle in (first, second) if vehicle.status == VehicleStatus.WAITING]
        self.assertEqual(len(waiting), 1)
        self.assertEqual(waiting[0].wait_reason, WaitReason.YIELDING)

    def test_wait_threshold_marks_intersection_congestion(self) -> None:
        gc = GameController(MAP_PATH)
        intersection = gc.map_manager.get_state().intersection_cells[0]
        vehicle = gc.vehicle_manager.spawn_vehicle(VehicleType.CAR, intersection)
        vehicle.status = VehicleStatus.WAITING
        vehicle.wait_time = WAIT_THRESHOLD
        for neighbor in gc.map_manager.get_state().intersection_neighbors[intersection]:
            gc.map_manager.add_dynamic_block(neighbor)
        gc.traffic_controller.update([vehicle], gc.map_manager, 0.0, gc.guards)
        self.assertEqual(vehicle.wait_reason, WaitReason.TRAFFIC_CONGESTION)

    def test_vehicle_direction_updates_from_path_shape(self) -> None:
        gc = GameController(MAP_PATH)
        straight_start, straight_next, straight_after = drive_run(gc)
        straight = gc.vehicle_manager.spawn_vehicle(VehicleType.CAR, straight_start)
        straight.path = [straight_next, straight_after]
        straight.status = VehicleStatus.MOVING
        gc.vehicle_manager.update(0.3, gc.map_manager.get_state())
        self.assertEqual(straight.direction, "STRAIGHT")

        gc = GameController(MAP_PATH)
        turn_start, turn_next, turn_after = turning_drive_path(gc)
        turning = gc.vehicle_manager.spawn_vehicle(VehicleType.CAR, turn_start)
        turning.path = [turn_next, turn_after]
        turning.status = VehicleStatus.MOVING
        gc.vehicle_manager.update(0.3, gc.map_manager.get_state())
        self.assertEqual(turning.direction, "TURN")


if __name__ == "__main__":
    unittest.main()
