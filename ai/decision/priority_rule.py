from config import (
    DIRECTION_BONUS_STRAIGHT,
    DIRECTION_BONUS_TURN,
    WAIT_TIME_WEIGHT,
)
from models.vehicle import Vehicle
from utils.grid_utils import manhattan_distance


def calculate_priority(vehicle: Vehicle, goal: tuple[int, int]) -> float:
    distance_to_target = manhattan_distance(vehicle.position, goal)
    direction_bonus = (
        DIRECTION_BONUS_STRAIGHT
        if vehicle.direction == "STRAIGHT"
        else DIRECTION_BONUS_TURN
    )
    score = (
        vehicle.wait_time * WAIT_TIME_WEIGHT
        - distance_to_target
        + direction_bonus
        - vehicle.id * 0.001
    )
    return score


def resolve_conflict(vehicles: list[Vehicle], goal: tuple[int, int]) -> Vehicle:
    return max(vehicles, key=lambda vehicle: calculate_priority(vehicle, goal))
