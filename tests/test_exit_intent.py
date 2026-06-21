import unittest

from config import REROUTE_WAIT_THRESHOLD
from core.game_controller import GameController
from core.simulation_state import SimulationStatus, VehiclePlan
from models.enums import VehicleStatus, VehicleType, WaitReason


MAP_PATH = "data/maps/default_map.txt"
APP_MAP_PATH = "data/map_layout.json"


class TestExitIntent(unittest.TestCase):
    def test_controller_vehicle_type_selection_does_not_require_place_mode(self) -> None:
        gc = GameController(MAP_PATH)

        gc.set_placement_vehicle_type(VehicleType.MOTORBIKE)
        gc.set_placement_vehicle_type(VehicleType.CAR)

        self.assertEqual(gc.placement_vehicle_type, VehicleType.CAR)
        self.assertNotEqual(gc.simulation_status, SimulationStatus.PLACING_VEHICLE)
        self.assertEqual(gc.vehicle_manager.get_all_vehicles(), [])

    def test_assign_and_path_does_not_reassign_parked_vehicle(self) -> None:
        gc = GameController(MAP_PATH)
        vehicle = gc.spawn_vehicle(VehicleType.CAR)
        parked_slot = vehicle.assigned_slot
        vehicle.position = parked_slot
        vehicle.path = []
        vehicle.status = VehicleStatus.PARKED

        gc._assign_and_path(vehicle)

        self.assertEqual(vehicle.assigned_slot, parked_slot)
        self.assertEqual(vehicle.position, parked_slot)
        self.assertEqual(vehicle.path, [])
        self.assertEqual(vehicle.status, VehicleStatus.PARKED)

    def test_exiting_vehicle_wins_target_cell_conflict(self) -> None:
        gc = GameController(MAP_PATH)
        exiting = gc.vehicle_manager.spawn_vehicle(VehicleType.CAR, (0, 0))
        entering = gc.vehicle_manager.spawn_vehicle(VehicleType.CAR, (0, 2))
        exiting.path = [(0, 1)]
        entering.path = [(0, 1)]
        exiting.status = VehicleStatus.MOVING
        entering.status = VehicleStatus.MOVING
        exiting.wait_reason = WaitReason.EXITING

        gc.traffic_controller.update(
            [exiting, entering],
            gc.map_manager,
            0.1,
            gc.guards,
        )

        self.assertEqual(exiting.status, VehicleStatus.MOVING)
        self.assertEqual(exiting.wait_reason, WaitReason.EXITING)
        self.assertEqual(entering.status, VehicleStatus.WAITING)
        self.assertEqual(entering.wait_reason, WaitReason.YIELDING)

    def test_exiting_vehicle_does_not_get_new_slot_after_yield_reason(self) -> None:
        gc = GameController(MAP_PATH)
        vehicle = gc.spawn_vehicle(VehicleType.CAR)
        gc.start_exit(vehicle.id)

        vehicle.status = VehicleStatus.WAITING
        vehicle.wait_reason = WaitReason.YIELDING
        vehicle.path = []
        vehicle.wait_time = REROUTE_WAIT_THRESHOLD

        gc._recover_waiting_vehicle(vehicle)

        self.assertIsNone(vehicle.assigned_slot)
        self.assertEqual(vehicle.status, VehicleStatus.MOVING)
        self.assertEqual(vehicle.wait_reason, WaitReason.EXITING)
        self.assertEqual(gc._vehicle_plans[vehicle.id], VehiclePlan.EXITING)

    def test_arrived_exiting_vehicle_reroutes_instead_of_parking(self) -> None:
        gc = GameController(MAP_PATH)
        vehicle = gc.spawn_vehicle(VehicleType.CAR)
        old_slot = vehicle.assigned_slot
        gc.start_exit(vehicle.id)

        vehicle.position = old_slot
        vehicle.status = VehicleStatus.ARRIVED
        vehicle.wait_reason = WaitReason.NONE
        vehicle.path = []

        gc.update(0.1)

        self.assertIsNone(vehicle.assigned_slot)
        self.assertEqual(vehicle.status, VehicleStatus.MOVING)
        self.assertEqual(vehicle.wait_reason, WaitReason.EXITING)

    def test_tandem_outer_motorbike_reserves_inner_slot_while_inner_exits(self) -> None:
        gc = GameController(APP_MAP_PATH)
        state = gc.map_manager.get_state()
        inner_slot, outer_slot = next(iter(state.motorbike_inner_to_outer.items()))
        inner = gc.vehicle_manager.spawn_vehicle(VehicleType.MOTORBIKE, inner_slot)
        outer = gc.vehicle_manager.spawn_vehicle(VehicleType.MOTORBIKE, outer_slot)
        gc.parking_manager.occupy_slot(inner, inner_slot, state)
        gc.parking_manager.occupy_slot(outer, outer_slot, state)

        gc.start_exit(inner.id)
        job = gc._tandem_exit_jobs[inner.id]
        temp_position = job["temp_position"]
        self.assertIsInstance(temp_position, tuple)
        outer.position = temp_position
        outer.path = []

        gc._update_tandem_exit_jobs()

        self.assertEqual(job["phase"], "INNER_EXITING")
        self.assertEqual(outer.assigned_slot, inner_slot)
        self.assertTrue(state.parking_slots[inner_slot].is_reserved)
        self.assertEqual(state.parking_slots[inner_slot].reserved_by, outer.id)
        self.assertFalse(state.parking_slots[outer_slot].is_reserved)
        self.assertIsNone(state.parking_slots[outer_slot].reserved_by)
        newcomer = gc.vehicle_manager.spawn_vehicle(
            VehicleType.MOTORBIKE,
            state.entry_gates[0],
        )
        self.assertNotEqual(gc.parking_manager.find_slot(newcomer, state), inner_slot)

    def test_tandem_outer_motorbike_returns_after_inner_clears_access(self) -> None:
        gc = GameController(APP_MAP_PATH)
        state = gc.map_manager.get_state()
        inner_slot, outer_slot = next(iter(state.motorbike_inner_to_outer.items()))
        inner = gc.vehicle_manager.spawn_vehicle(VehicleType.MOTORBIKE, inner_slot)
        outer = gc.vehicle_manager.spawn_vehicle(VehicleType.MOTORBIKE, outer_slot)
        gc.parking_manager.occupy_slot(inner, inner_slot, state)
        gc.parking_manager.occupy_slot(outer, outer_slot, state)

        gc.start_exit(inner.id)
        job = gc._tandem_exit_jobs[inner.id]
        temp_position = job["temp_position"]
        self.assertIsInstance(temp_position, tuple)
        outer.position = temp_position
        outer.path = []
        gc._update_tandem_exit_jobs()
        self.assertTrue(inner.path)
        if len(inner.path) > 1:
            inner.position = inner.path[1]
            inner.path = inner.path[2:]
        else:
            inner.position = inner.path[0]
            inner.path = []

        gc._update_tandem_exit_jobs()

        self.assertEqual(job["phase"], "OUTER_RETURNING_INNER")
        self.assertEqual(outer.assigned_slot, inner_slot)
        self.assertIn(outer.status, {VehicleStatus.MOVING, VehicleStatus.ARRIVED})

    def test_tandem_inner_motorbike_exits_when_outer_is_parked_ahead(self) -> None:
        gc = GameController(APP_MAP_PATH)
        state = gc.map_manager.get_state()
        inner_slot, outer_slot = next(iter(state.motorbike_inner_to_outer.items()))
        inner = gc.vehicle_manager.spawn_vehicle(VehicleType.MOTORBIKE, inner_slot)
        outer = gc.vehicle_manager.spawn_vehicle(VehicleType.MOTORBIKE, outer_slot)
        gc.parking_manager.occupy_slot(inner, inner_slot, state)
        gc.parking_manager.occupy_slot(outer, outer_slot, state)
        inner.status = VehicleStatus.PARKED
        outer.status = VehicleStatus.PARKED

        gc.start_exit(inner.id)

        for _ in range(120):
            gc.update(0.3)
            if gc.vehicle_manager.get_vehicle(inner.id) is None:
                break

        self.assertIsNone(gc.vehicle_manager.get_vehicle(inner.id))
        self.assertEqual(outer.status, VehicleStatus.PARKED)
        self.assertEqual(outer.assigned_slot, inner_slot)

    def test_tandem_inner_car_exits_when_outer_is_parked_ahead(self) -> None:
        gc = GameController(MAP_PATH)
        state = gc.map_manager.get_state()
        inner_slot, outer_slot = next(iter(state.car_inner_to_outer.items()))
        inner = gc.vehicle_manager.spawn_vehicle(VehicleType.CAR, inner_slot)
        outer = gc.vehicle_manager.spawn_vehicle(VehicleType.CAR, outer_slot)
        gc.parking_manager.occupy_slot(inner, inner_slot, state)
        gc.parking_manager.occupy_slot(outer, outer_slot, state)
        inner.status = VehicleStatus.PARKED
        outer.status = VehicleStatus.PARKED

        gc.start_exit(inner.id)

        self.assertIn(inner.id, gc._tandem_exit_jobs)
        for _ in range(120):
            gc.update(0.3)
            if gc.vehicle_manager.get_vehicle(inner.id) is None:
                break

        self.assertIsNone(gc.vehicle_manager.get_vehicle(inner.id))
        self.assertEqual(outer.status, VehicleStatus.PARKED)
        self.assertEqual(outer.assigned_slot, inner_slot)

    def test_guard_sends_violating_exiting_vehicle_to_exit_not_parking(self) -> None:
        gc = GameController(APP_MAP_PATH)
        vehicle = gc.spawn_vehicle(VehicleType.CAR)
        self.assertIsNotNone(vehicle)
        gc.start_exit(vehicle.id)
        gc.set_manual(vehicle.id)
        vehicle.position = (8, 5)

        self.assertEqual(gc.confirm_parking(vehicle.id), "ILLEGAL_ROAD")
        guard = next(guard for guard in gc.guards if guard.task == "VIOLATION")
        guard.position = vehicle.position
        guard.path = []
        gc._handle_guard_reached_violation(guard)

        self.assertIsNone(vehicle.assigned_slot)
        self.assertEqual(vehicle.status, VehicleStatus.MOVING)
        self.assertEqual(vehicle.wait_reason, WaitReason.EXITING)
        self.assertTrue(vehicle.path)
        self.assertIn(vehicle.path[-1], gc.map_manager.get_state().exit_gates)


if __name__ == "__main__":
    unittest.main()
