from dataclasses import dataclass, field


@dataclass
class MapState:
    grid: list[list[str]] = field(default_factory=list)
    gates: list[tuple[int, int]] = field(default_factory=list)
    parking_slots: list[tuple[int, int]] = field(default_factory=list)
    blocked_cells: set[tuple[int, int]] = field(default_factory=set)

