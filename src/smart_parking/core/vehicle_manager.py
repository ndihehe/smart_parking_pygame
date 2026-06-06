from src.smart_parking.models.vehicle import Vehicle


class VehicleManager:
    def __init__(self) -> None:
        self.vehicles: list[Vehicle] = []

    def spawn_vehicle(self, vehicle_type: str) -> Vehicle | None:
        pass

    def update(self, delta_time: float) -> None:
        pass

    def move_vehicle(self, vehicle: Vehicle, target_cell: tuple[int, int]) -> None:
        pass

    def enable_manual_control(self, vehicle_id: int) -> None:
        pass

    def confirm_parking(self, vehicle_id: int) -> None:
        pass

