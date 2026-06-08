from dataclasses import dataclass

from models.enums import VehicleType


@dataclass
class ParkingSlot:
    position: tuple[int, int]
    slot_type: VehicleType | None
    is_reserved: bool = False
    reserved_by: int | None = None
    is_occupied: bool = False
    occupied_by: int | None = None
