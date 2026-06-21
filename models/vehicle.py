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
    heading: str = "east"
    wait_reason: WaitReason = WaitReason.NONE
    render_from: tuple[int, int] | None = None
    render_progress: float = 1.0

    def __post_init__(self) -> None:
        if self.render_from is None:
            self.render_from = self.position
