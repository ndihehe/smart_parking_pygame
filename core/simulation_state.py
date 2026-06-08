from enum import Enum


class SimulationStatus(Enum):
    IDLE = "IDLE"
    PLACING_VEHICLE = "PLACING_VEHICLE"
    READY = "READY"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    FINISHED = "FINISHED"


class VehiclePlan(Enum):
    ENTERING = "ENTERING"
    EXITING = "EXITING"
