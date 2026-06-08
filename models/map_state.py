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
    intersection_cells: list[tuple[int, int]] = field(default_factory=list)
    intersection_neighbors: dict[tuple[int, int], list[tuple[int, int]]] = field(default_factory=dict)
    entry_gates: list[tuple[int, int]] = field(default_factory=list)
    exit_gates: list[tuple[int, int]] = field(default_factory=list)
    car_slots: list[tuple[int, int]] = field(default_factory=list)
    motorbike_slots: list[tuple[int, int]] = field(default_factory=list)
    motorbike_outer_to_inner: dict[tuple[int, int], tuple[int, int]] = field(default_factory=dict)
    motorbike_inner_to_outer: dict[tuple[int, int], tuple[int, int]] = field(default_factory=dict)
    image_path: str | None = None
    tile_size: int = 32
    grid_offset_x: int = 0
    grid_offset_y: int = 0
