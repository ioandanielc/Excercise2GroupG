import json
from dataclasses import dataclass
from types import SimpleNamespace
from typing import Tuple


@dataclass
class State:
    """Class to store the current state of the simulation."""
    field: Tuple[int, int]
    pedestrians: set
    obstacles: set
    target: set


def read_scenario(filepath):
    """Function to read a scenario from a JSON file.

    Args:
        filepath (str): Path to the JSON file containing the scenario.

    Returns:
        State: The initial state of the scenario.
    """
    with open(filepath) as f:
        scenario = json.load(f, object_hook=lambda d: SimpleNamespace(**d))
    scenario.pedestrians = set(tuple(coordinate) for coordinate in scenario.pedestrians)
    scenario.obstacles = set(tuple(coordinate) for coordinate in scenario.obstacles)
    scenario.target = set(tuple(coordinate) for coordinate in scenario.target)
    return State(scenario.field, scenario.pedestrians, scenario.obstacles, scenario.target)
