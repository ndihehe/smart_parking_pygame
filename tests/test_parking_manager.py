import unittest

from core.game_controller import GameController
from models.enums import CellType, VehicleStatus, VehicleType, WaitReason
from utils.logger import Logger


MAP_PATH = "data/maps/default_map.txt"


class TestParkingManager(unittest.TestCase):
    def test_vehicle_type_gets_matching_slot(self) -> None:
        gc = GameController(MAP_PATH)
        vehicle = gc.spawn_vehicle(VehicleType.MOTORBIKE)
        self.assertIsNotNone(vehicle)
        slot = gc.map_manager.get_state().parking_slots[vehicle.assigned_slot]
        self.assertEqual(slot.slot_type, VehicleType.MOTORBIKE)

    def test_release_old_slot_when_slot_changes(self) -> None:
        gc = GameController(MAP_PATH)
        vehicle = gc.spawn_vehicle(VehicleType.CAR)
        state = gc.map_manager.get_state()
        old_slot = vehicle.assigned_slot
        new_slot = next(
            position
            for position, slot in state.parking_slots.items()
            if slot.slot_type == VehicleType.CAR and position != old_slot
        )
        gc.parking_manager.assign_slot(vehicle, new_slot, state)
        self.assertFalse(state.parking_slots[old_slot].is_reserved)
        self.assertIsNone(state.parking_slots[old_slot].reserved_by)
        self.assertEqual(vehicle.assigned_slot, new_slot)

    def test_validate_assigned_slot_logs_ok(self) -> None:
        Logger.clear()
        gc = GameController(MAP_PATH)
        vehicle = gc.spawn_vehicle(VehicleType.CAR)
        vehicle.position = vehicle.assigned_slot
        result = gc.parking_manager.validate_parking(vehicle, gc.map_manager.get_state())
        self.assertEqual(result, "OK")
        self.assertTrue(any("validation OK" in line for line in Logger.get_logs()))

    def test_validate_different_valid_slot(self) -> None:
        gc = GameController(MAP_PATH)
        vehicle = gc.spawn_vehicle(VehicleType.CAR)
        state = gc.map_manager.get_state()
        other_slot = next(
            position
            for position, slot in state.parking_slots.items()
            if slot.slot_type == VehicleType.CAR and position != vehicle.assigned_slot
        )
        vehicle.position = other_slot
        result = gc.parking_manager.validate_parking(vehicle, state)
        self.assertEqual(result, "DIFFERENT_SLOT")

    def test_validate_road_intersection_and_wrong_type(self) -> None:
        gc = GameController(MAP_PATH)
        vehicle = gc.spawn_vehicle(VehicleType.MOTORBIKE)
        state = gc.map_manager.get_state()

        vehicle.position = next(
            (row_index, col_index)
            for row_index, row in enumerate(state.grid)
            for col_index, cell in enumerate(row)
            if cell == CellType.ROAD
        )
        self.assertEqual(gc.parking_manager.validate_parking(vehicle, state), "ILLEGAL_ROAD")

        vehicle.position = state.intersection_cells[0]
        self.assertEqual(
            gc.parking_manager.validate_parking(vehicle, state),
            "BLOCKING_INTERSECTION",
        )

        vehicle.position = state.car_slots[0]
        self.assertEqual(gc.parking_manager.validate_parking(vehicle, state), "WRONG_TYPE")

    def test_auto_arrived_parking_uses_validate_parking(self) -> None:
        Logger.clear()
        gc = GameController(MAP_PATH)
        vehicle = gc.spawn_vehicle(VehicleType.CAR)
        vehicle.position = vehicle.assigned_slot
        vehicle.path = []
        vehicle.status = VehicleStatus.ARRIVED
        gc.update(0.1)
        self.assertEqual(vehicle.status, VehicleStatus.PARKED)
        self.assertTrue(any("parking accepted: OK" in line for line in Logger.get_logs()))

    def test_car_can_use_inner_tandem_slot(self) -> None:
        gc = GameController(MAP_PATH)
        state = gc.map_manager.get_state()
        inner_slot, outer_slot = next(iter(state.car_inner_to_outer.items()))
        vehicle = gc.vehicle_manager.spawn_vehicle(VehicleType.CAR, state.entry_gates[0])

        gc.parking_manager.assign_slot(vehicle, inner_slot, state)

        self.assertEqual(vehicle.assigned_slot, inner_slot)
        self.assertTrue(state.parking_slots[outer_slot].is_reserved)
        self.assertEqual(state.parking_slots[outer_slot].reserved_by, vehicle.id)

    def test_car_inner_slot_is_blocked_when_outer_slot_is_occupied(self) -> None:
        gc = GameController(MAP_PATH)
        state = gc.map_manager.get_state()
        inner_slot, outer_slot = next(iter(state.car_inner_to_outer.items()))
        outer_vehicle = gc.vehicle_manager.spawn_vehicle(VehicleType.CAR, outer_slot)
        gc.parking_manager.occupy_slot(outer_vehicle, outer_slot, state)
        newcomer = gc.vehicle_manager.spawn_vehicle(VehicleType.CAR, state.entry_gates[0])

        self.assertFalse(
            gc.parking_manager._tandem_access_available(newcomer, inner_slot, state)
        )

    def test_wrong_type_parking_is_marked_as_active_block(self) -> None:
        gc = GameController(MAP_PATH)
        vehicle = gc.spawn_vehicle(VehicleType.MOTORBIKE)
        gc.set_manual(vehicle.id)
        vehicle.position = gc.map_manager.get_state().car_slots[0]

        self.assertEqual(gc.confirm_parking(vehicle.id), "WRONG_TYPE")
        self.assertEqual(vehicle.status, VehicleStatus.VIOLATION)
        self.assertEqual(
            vehicle.wait_reason,
            WaitReason.PARKING_VIOLATION_WRONG_TYPE,
        )
        self.assertIn(vehicle.position, gc.map_manager.get_state().dynamic_blocks)


if __name__ == "__main__":
    unittest.main()
