from src.smart_parking.core.simulation import Simulation
from src.smart_parking.models.vehicle import Vehicle


def test_skeleton_imports() -> None:
    assert Simulation is not None
    assert Vehicle is not None

