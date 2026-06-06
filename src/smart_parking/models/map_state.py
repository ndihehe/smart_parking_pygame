from dataclasses import dataclass, field


@dataclass
class MapState:
    grid: list[list[str]] = field(default_factory=list)
    gate_cells: list[tuple[int, int]] = field(default_factory=list)
    parking_slots: list[tuple[int, int]] = field(default_factory=list)
    static_obstacles: set[tuple[int, int]] = field(default_factory=set)
    dynamic_blocks: set[tuple[int, int]] = field(default_factory=set)

