from dataclasses import dataclass


@dataclass
class ParkingSlot:
    position: tuple[int, int]
    slot_type: str
    occupied_by: int | None = None

    def is_available(self) -> bool:
        return self.occupied_by is None

