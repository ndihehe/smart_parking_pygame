from dataclasses import dataclass, field


@dataclass
class Guard:
    id: int
    position: tuple[int, int]
    home_position: tuple[int, int]
    target_vehicle_id: int | None = None
    target_position: tuple[int, int] | None = None
    task: str = "IDLE"
    path: list[tuple[int, int]] = field(default_factory=list)
    is_active: bool = False
    move_timer: float = 0.0
    is_walking: bool = False
    facing_delta: tuple[int, int] = (0, 1)
