from core.simulation_state import SimulationState
from models.vehicle import Vehicle


class VehicleManager:
    def __init__(self, state: SimulationState) -> None:
        self.state = state

    def create_vehicle(self, vehicle_type: str) -> Vehicle:
        pass

    def add_vehicle(self, vehicle: Vehicle) -> None:
        pass

    def update_vehicles(self, delta_time: float) -> None:
        pass

