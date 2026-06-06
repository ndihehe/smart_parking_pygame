from core.map_manager import MapManager
from core.parking_manager import ParkingManager
from core.simulation_state import SimulationState
from core.traffic_controller import TrafficController
from core.vehicle_manager import VehicleManager


class GameController:
    def __init__(self) -> None:
        self.state = SimulationState()
        self.map_manager = MapManager(self.state)
        self.vehicle_manager = VehicleManager(self.state)
        self.parking_manager = ParkingManager(self.state)
        self.traffic_controller = TrafficController(self.state)

    def load_default_map(self) -> None:
        pass

    def update(self, delta_time: float) -> None:
        pass

    def spawn_vehicle(self, vehicle_type: str) -> None:
        pass

