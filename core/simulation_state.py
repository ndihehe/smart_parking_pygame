from dataclasses import dataclass, field

from models.map_state import MapState
from models.vehicle import Vehicle


@dataclass
class SimulationState:
    map_state: MapState = field(default_factory=MapState)
    vehicles: list[Vehicle] = field(default_factory=list)
    selected_vehicle_id: int | None = None
    running: bool = True

