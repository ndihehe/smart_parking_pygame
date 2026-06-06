from dataclasses import dataclass, field

from models.enums import VehicleStatus, VehicleType


@dataclass
class Vehicle:
    id: int
    vehicle_type: VehicleType
    position: tuple[int, int]
    status: VehicleStatus = VehicleStatus.WAITING
    assigned_slot: tuple[int, int] | None = None
    path: list[tuple[int, int]] = field(default_factory=list)
    wait_time: float = 0.0

