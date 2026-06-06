from src.smart_parking.models.vehicle import Vehicle


class IntersectionManager:
    def get_waiting_vehicles(self, intersection: tuple[int, int]) -> list[Vehicle]:
        pass

    def calculate_priority(self, vehicle: Vehicle) -> float:
        pass

    def select_next_vehicle(self, vehicles: list[Vehicle]) -> Vehicle | None:
        pass

    def resolve_cell_conflict(
        self,
        target_cell: tuple[int, int],
        candidate_vehicles: list[Vehicle],
    ) -> Vehicle | None:
        pass

