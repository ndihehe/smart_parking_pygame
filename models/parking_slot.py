from dataclasses import dataclass

from models.enums import VehicleType


@dataclass
class ParkingSlot:
    position: tuple[int, int]
    slot_type: VehicleType
    is_occupied: bool = False
    occupied_by: int | None = None
