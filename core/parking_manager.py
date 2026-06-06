from core.simulation_state import SimulationState
from models.vehicle import Vehicle


class ParkingManager:
    def __init__(self, state: SimulationState) -> None:
        self.state = state

    def find_available_slots(self, vehicle: Vehicle) -> list[tuple[int, int]]:
        pass

    def assign_slot(self, vehicle: Vehicle) -> tuple[int, int] | None:
        pass

    def validate_parking(self, vehicle: Vehicle) -> bool:
        pass

