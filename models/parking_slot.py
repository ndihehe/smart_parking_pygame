from dataclasses import dataclass


@dataclass
class ParkingSlot:
    position: tuple[int, int]
    slot_type: str
    vehicle_id: int | None = None

    def is_available(self) -> bool:
        return self.vehicle_id is None

