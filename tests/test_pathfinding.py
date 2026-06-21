import unittest

from ai.pathfinding.router import find_path
from core.game_controller import GameController
from models.enums import AlgorithmType, VehicleType
from utils.grid_utils import get_neighbors


MAP_PATH = "data/maps/default_map.txt"


class TestPathfinding(unittest.TestCase):
    def _route_endpoints(self, gc: GameController):
        state = gc.map_manager.get_state()
        return state.entry_gates[0], state.exit_gates[0]

    def test_bfs_finds_path(self) -> None:
        gc = GameController(MAP_PATH)
        start, goal = self._route_endpoints(gc)
        path = find_path("bfs", start, goal, gc.map_manager)
        self.assertTrue(path)
        self.assertEqual(path[-1], goal)

    def test_dfs_finds_path(self) -> None:
        gc = GameController(MAP_PATH)
        start, goal = self._route_endpoints(gc)
        path = find_path("dfs", start, goal, gc.map_manager)
        self.assertTrue(path)
        self.assertEqual(path[-1], goal)

    def test_greedy_finds_path(self) -> None:
        gc = GameController(MAP_PATH)
        start, goal = self._route_endpoints(gc)
        path = find_path("greedy", start, goal, gc.map_manager)
        self.assertTrue(path)
        self.assertEqual(path[-1], goal)

    def test_astar_finds_path(self) -> None:
        gc = GameController(MAP_PATH)
        start, goal = self._route_endpoints(gc)
        path = find_path(AlgorithmType.ASTAR, start, goal, gc.map_manager)
        self.assertTrue(path)
        self.assertEqual(path[-1], goal)

    def test_pathfinding_avoids_blocked_vehicle_positions(self) -> None:
        gc = GameController(MAP_PATH)
        start, goal = self._route_endpoints(gc)
        initial_path = find_path("astar", start, goal, gc.map_manager)
        blocked = initial_path[0]
        path = find_path("astar", start, goal, gc.map_manager, {blocked})
        self.assertNotIn(blocked, path)
        self.assertEqual(path[-1], goal)

    def test_blocked_positions_can_prevent_path(self) -> None:
        gc = GameController(MAP_PATH)
        start, goal = self._route_endpoints(gc)
        blocked = {
            neighbor
            for neighbor in get_neighbors(start, gc.map_manager.state.rows, gc.map_manager.state.cols)
            if gc.map_manager.is_drive_cell(neighbor)
        }
        path = find_path("bfs", start, goal, gc.map_manager, blocked)
        self.assertEqual(path, [])

    def test_invalid_algorithm_name_raises(self) -> None:
        gc = GameController(MAP_PATH)
        with self.assertRaises(ValueError):
            start, goal = self._route_endpoints(gc)
            find_path("dijkstra", start, goal, gc.map_manager)

    def test_game_controller_uses_runtime_algorithm(self) -> None:
        gc = GameController(MAP_PATH, algorithm="bfs")
        vehicle = gc.spawn_vehicle(VehicleType.CAR)
        self.assertEqual(gc.current_algorithm, "bfs")
        self.assertTrue(vehicle.path)

    def test_vehicle_does_not_move_through_other_vehicle(self) -> None:
        gc = GameController(MAP_PATH)
        car = gc.spawn_vehicle(VehicleType.CAR)
        blocker = gc.vehicle_manager.spawn_vehicle(VehicleType.MOTORBIKE, car.path[0])
        gc.vehicle_manager.set_manual(blocker.id)
        old_position = car.position
        gc.update(0.3)
        self.assertEqual(car.position, old_position)
        self.assertNotEqual(car.position, blocker.position)


if __name__ == "__main__":
    unittest.main()
