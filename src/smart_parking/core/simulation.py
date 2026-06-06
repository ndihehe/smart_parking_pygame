from src.smart_parking.core.map_manager import MapManager
from src.smart_parking.core.parking_manager import ParkingManager
from src.smart_parking.core.vehicle_manager import VehicleManager
from src.smart_parking.traffic.controller import TrafficController


class Simulation:
    def __init__(self) -> None:
        self.map_manager = MapManager()
        self.vehicle_manager = VehicleManager()
        self.parking_manager = ParkingManager()
        self.traffic_controller = TrafficController()

    def load_map(self, path: str) -> None:
        self.map_manager.load_map(path)

    def update(self, delta_time: float) -> None:
        self.traffic_controller.update(delta_time)
        self.vehicle_manager.update(delta_time)

    def spawn_vehicle(self, vehicle_type: str) -> None:
        self.vehicle_manager.spawn_vehicle(vehicle_type)

