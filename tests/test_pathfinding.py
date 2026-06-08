import unittest

from ai.pathfinding.router import find_path
from core.game_controller import GameController
from models.enums import AlgorithmType, VehicleType


MAP_PATH = "data/maps/default_map.txt"


class TestPathfinding(unittest.TestCase):
    def test_bfs_finds_path(self) -> None:
        gc = GameController(MAP_PATH)
        path = find_path("bfs", (0, 0), (3, 1), gc.map_manager)
        self.assertTrue(path)
        self.assertEqual(path[-1], (3, 1))

    def test_dfs_finds_path(self) -> None:
        gc = GameController(MAP_PATH)
        path = find_path("dfs", (0, 0), (3, 1), gc.map_manager)
        self.assertTrue(path)
        self.assertEqual(path[-1], (3, 1))

    def test_greedy_finds_path(self) -> None:
        gc = GameController(MAP_PATH)
        path = find_path("greedy", (0, 0), (3, 1), gc.map_manager)
        self.assertTrue(path)
        self.assertEqual(path[-1], (3, 1))

    def test_astar_finds_path(self) -> None:
        gc = GameController(MAP_PATH)
        path = find_path(AlgorithmType.ASTAR, (0, 0), (3, 1), gc.map_manager)
        self.assertTrue(path)
        self.assertEqual(path[-1], (3, 1))

    def test_pathfinding_avoids_blocked_vehicle_positions(self) -> None:
        gc = GameController(MAP_PATH)
        path = find_path("astar", (0, 0), (3, 1), gc.map_manager, {(1, 0)})
        self.assertNotIn((1, 0), path)
        self.assertEqual(path[-1], (3, 1))

    def test_blocked_positions_can_prevent_path(self) -> None:
        gc = GameController(MAP_PATH)
        path = find_path("bfs", (0, 0), (3, 1), gc.map_manager, {(0, 1), (1, 0)})
        self.assertEqual(path, [])

    def test_invalid_algorithm_name_raises(self) -> None:
        gc = GameController(MAP_PATH)
        with self.assertRaises(ValueError):
            find_path("dijkstra", (0, 0), (3, 1), gc.map_manager)

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
