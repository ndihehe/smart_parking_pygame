from enum import Enum


class CellType(str, Enum):
    GATE = "G"
    ROAD = "R"
    INTERSECTION = "I"
    STATIC_OBSTACLE = "X"
    DYNAMIC_BLOCK = "B"
    MOTORBIKE_SLOT = "M"
    CAR_SLOT = "C"
    EMPTY = "."


class VehicleType(str, Enum):
    CAR = "CAR"
    MOTORBIKE = "MOTORBIKE"


class VehicleStatus(str, Enum):
    WAITING = "WAITING"
    MOVING = "MOVING"
    PARKED = "PARKED"
    MANUAL = "MANUAL"
    REROUTING = "REROUTING"
    VIOLATION = "VIOLATION"

