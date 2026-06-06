from src.smart_parking.models.vehicle import Vehicle


class TrafficController:
    def update(self, delta_time: float) -> None:
        pass

    def detect_congestion(self) -> list[tuple[int, int]]:
        pass

    def handle_obstacle(self, blocked_cell: tuple[int, int]) -> None:
        pass

    def request_reroute(self, vehicle: Vehicle) -> None:
        pass

