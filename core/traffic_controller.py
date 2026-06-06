from core.simulation_state import SimulationState


class TrafficController:
    def __init__(self, state: SimulationState) -> None:
        self.state = state

    def update(self, delta_time: float) -> None:
        pass

    def detect_blocked_cells(self) -> list[tuple[int, int]]:
        pass

    def detect_intersection_conflicts(self) -> list[tuple[int, int]]:
        pass

