import unittest

from core.game_controller import GameController
from models.enums import CellType


MAP_PATH = "data/maps/default_map.txt"


class TestMapManager(unittest.TestCase):
    def test_map_20x32_loads(self) -> None:
        gc = GameController(MAP_PATH)
        state = gc.map_manager.get_state()
        self.assertEqual(state.rows, 20)
        self.assertEqual(state.cols, 32)
        self.assertGreaterEqual(len(state.gate_cells), 2)
        self.assertGreater(len(state.parking_slots), 0)

    def test_slot_rows_have_20_positions_each(self) -> None:
        gc = GameController(MAP_PATH)
        grid = gc.map_manager.get_state().grid
        car_rows = [row for row in grid if sum(cell == CellType.CAR_SLOT for cell in row) == 20]
        moto_rows = [row for row in grid if sum(cell == CellType.MOTO_SLOT for cell in row) == 20]
        self.assertEqual(len(car_rows), 2)
        self.assertEqual(len(moto_rows), 2)

    def test_map_static_indexes_are_cached(self) -> None:
        gc = GameController(MAP_PATH)
        state = gc.map_manager.get_state()
        self.assertEqual(len(state.car_slots), 40)
        self.assertEqual(len(state.motorbike_slots), 40)
        self.assertEqual(state.entry_gates, [(0, 0), (19, 0)])
        self.assertEqual(state.exit_gates, [(0, 31), (19, 31)])
        self.assertGreater(len(state.intersection_cells), 0)
        for intersection in state.intersection_cells:
            self.assertIn(intersection, state.intersection_neighbors)


if __name__ == "__main__":
    unittest.main()
