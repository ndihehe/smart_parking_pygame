from dataclasses import dataclass, field

from models.enums import CellType
from models.parking_slot import ParkingSlot


@dataclass
class MapState:
    grid: list[list[CellType]]
    rows: int
    cols: int
    gate_cells: list[tuple[int, int]] = field(default_factory=list)
    parking_slots: dict[tuple[int, int], ParkingSlot] = field(default_factory=dict)
    static_obstacles: set[tuple[int, int]] = field(default_factory=set)
    dynamic_blocks: set[tuple[int, int]] = field(default_factory=set)
