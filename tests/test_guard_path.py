import unittest

from ai.pathfinding.guard_path import find_guard_path
from core.game_controller import GameController


MAP_PATH = "data/maps/default_map.txt"


class TestGuardPath(unittest.TestCase):
    def test_guard_can_cross_motorbike_slots_to_reach_inner_row(self) -> None:
        gc = GameController(MAP_PATH)
        state = gc.map_manager.get_state()
        inner_slot = next(iter(state.motorbike_inner_to_outer))

        path = find_guard_path(state.gate_cells[0], inner_slot, gc.map_manager)

        self.assertTrue(path)
        self.assertEqual(path[-1], inner_slot)
        self.assertTrue(
            any(position in state.motorbike_slots for position in path[:-1])
        )
        self.assertTrue(
            all(position not in state.static_obstacles for position in path)
        )


if __name__ == "__main__":
    unittest.main()
