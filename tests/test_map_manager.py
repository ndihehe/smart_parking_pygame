import unittest

from core.game_controller import GameController
from models.enums import CellType


MAP_PATH = "data/maps/default_map.txt"


class TestMapManager(unittest.TestCase):
    def test_map_20x20_loads(self) -> None:
        gc = GameController(MAP_PATH)
        state = gc.map_manager.get_state()
        self.assertEqual(state.rows, 20)
        self.assertEqual(state.cols, 20)
        self.assertGreaterEqual(len(state.gate_cells), 2)
        self.assertGreater(len(state.parking_slots), 0)

    def test_slot_rows_match_current_layout(self) -> None:
        gc = GameController(MAP_PATH)
        grid = gc.map_manager.get_state().grid
        car_rows = [sum(cell == CellType.CAR_SLOT for cell in row) for row in grid]
        moto_rows = [sum(cell == CellType.MOTO_SLOT for cell in row) for row in grid]
        self.assertEqual([count for count in car_rows if count], [14, 14, 14, 14])
        self.assertEqual([count for count in moto_rows if count], [18, 18, 18, 18])

    def test_map_static_indexes_are_cached(self) -> None:
        gc = GameController(MAP_PATH)
        state = gc.map_manager.get_state()
        self.assertEqual(len(state.car_slots), 56)
        self.assertEqual(len(state.motorbike_slots), 72)
        self.assertEqual(state.entry_gates, [(8, 0), (9, 0)])
        self.assertEqual(state.exit_gates, [(8, 19), (9, 19)])
        self.assertEqual(len(state.lamp_cells), 26)
        self.assertGreater(len(state.car_inner_to_outer), 0)
        self.assertGreater(len(state.motorbike_inner_to_outer), 0)
        self.assertGreater(len(state.intersection_cells), 0)
        for intersection in state.intersection_cells:
            self.assertIn(intersection, state.intersection_neighbors)


if __name__ == "__main__":
    unittest.main()
