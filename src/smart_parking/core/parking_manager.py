from src.smart_parking.models.vehicle import Vehicle


class ParkingManager:
    def find_valid_slots(self, vehicle: Vehicle) -> list[tuple[int, int]]:
        pass

    def score_slot(self, vehicle: Vehicle, slot: tuple[int, int]) -> float:
        pass

    def assign_slot(self, vehicle: Vehicle) -> tuple[int, int] | None:
        pass

    def validate_parking_position(self, vehicle: Vehicle) -> bool:
        pass

