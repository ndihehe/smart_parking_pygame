from dataclasses import dataclass, field

from models.enums import VehicleStatus, VehicleType, WaitReason


@dataclass
class Vehicle:
    id: int
    type: VehicleType
    position: tuple[int, int]
    assigned_slot: tuple[int, int] | None = None
    path: list[tuple[int, int]] = field(default_factory=list)
    status: VehicleStatus = VehicleStatus.WAITING
    wait_time: float = 0.0
    priority_score: float = 0.0
    direction: str = "STRAIGHT"
    wait_reason: WaitReason = WaitReason.NONE
