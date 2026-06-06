from config import CONGESTION_PENALTY, OBSTACLE_PENALTY
from models.map_state import MapState
from models.vehicle import Vehicle
from utils.grid_utils import get_neighbors, manhattan_distance


def score_slot(
    vehicle: Vehicle,
    slot_position: tuple[int, int],
    map_state: MapState,
) -> float:
    neighbors = get_neighbors(slot_position, map_state.rows, map_state.cols)
    distance = manhattan_distance(vehicle.position, slot_position)
    congestion_penalty = (
        CONGESTION_PENALTY
        if any(neighbor in map_state.dynamic_blocks for neighbor in neighbors)
        else 0
    )
    obstacle_penalty = (
        OBSTACLE_PENALTY
        if any(neighbor in map_state.static_obstacles for neighbor in neighbors)
        else 0
    )
    return distance + congestion_penalty + obstacle_penalty
