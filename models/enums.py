from enum import Enum


class CellType(Enum):
    GATE = "G"
    ROAD = "R"
    INTERSECTION = "I"
    OBSTACLE = "X"
    BLOCKED = "B"
    CAR_SLOT = "C"
    MOTO_SLOT = "M"
    EMPTY = "."


class VehicleType(Enum):
    CAR = "CAR"
    MOTORBIKE = "MOTORBIKE"


class VehicleStatus(Enum):
    WAITING = "WAITING"
    MOVING = "MOVING"
    PARKED = "PARKED"
    MANUAL = "MANUAL"
    REROUTING = "REROUTING"
    VIOLATION = "VIOLATION"


class AlgorithmType(Enum):
    BFS = "BFS"
    DFS = "DFS"
    GREEDY = "GREEDY"
    ASTAR = "ASTAR"
