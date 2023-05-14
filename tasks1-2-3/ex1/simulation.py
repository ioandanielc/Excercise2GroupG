import heapq as heap
import itertools
import math
from collections import defaultdict
from copy import deepcopy
from math import ceil
from typing import Union

import numpy as np

from ex1.utility import State, read_scenario


class Simulation:
    """Class to run the simulation."""

    def __init__(self, scenario, dijkstra=True, model_demographic_speed=False, time_cap: int = None):
        self.scenario = scenario
        self.speed = self.generate_speed_for_pedestrians(model_demographic_speed, len(scenario.pedestrians))
        self.utility = self.generate_utility(scenario, dijkstra)
        self.states = self.generate_states(scenario, self.utility, self.speed, time_cap)

    @staticmethod
    def generate_speed_for_pedestrians(model_demographic_speed, num_of_pedestrians):
        """Generates a list of speeds for the pedestrians.

        python
        Copy code
            Args:
                model_demographic_speed (bool): Whether to use a demographic model to generate the speeds.
                    speed corresponding to each age group: 20yo, 30yo, 40yo, 50yo, 60yo, 70yo, rimea Table 7, page 20
                    Age group Number of agents Min. [m/s] Max. [m/s]
                    20y.o. 10 1.60 1.64
                    30y.o. 10 1.52 1.56
                    40y.o. 10 1.46 1.50
                    50y.o. 10 1.39 1.43
                    60y.o. 5 1.27 1.27
                    70y.o. 5 1.07 1.07

                num_of_pedestrians (int): Number of pedestrians in the scenario.

            Returns:
                numpy.ndarray: Array containing the speeds of the pedestrians.
            """

        if not model_demographic_speed:
            return np.ones(num_of_pedestrians)
        speed_for_age_group = [1.6, 1.52, 1.46, 1.39, 1.27, 1.07]
        probability_for_age_group = [0.2, 0.2, 0.2, 0.2, 0.1, 0.1]
        return np.random.choice(speed_for_age_group, size=num_of_pedestrians, p=probability_for_age_group)

    @classmethod
    def generate_utility(cls, scenario: State, dijkstra: bool = True):
        """
        Generates the utility map for the given scenario.

        Args:
            scenario (State): The initial state of the scenario.
            dijkstra (bool, optional): Whether to use Dijkstra's algorithm to compute the utility map.
                Defaults to True.

        Returns:
            numpy.ndarray: Array containing the utility values for each cell in the scenario.
        """
        if dijkstra:
            visited = set()
            pq = []
            node_costs = defaultdict(lambda: math.inf)
            for endnonde in scenario.target:
                node_costs[tuple(endnonde)] = 0
                heap.heappush(pq, (0, endnonde))

            while pq:
                _, node = heap.heappop(pq)
                visited.add(tuple(node))

                neighbours = cls.get_neighbours(node, scenario)
                unvisited_neighbours = list(filter(lambda x: x not in visited, neighbours))

                if len(unvisited_neighbours) == 0:
                    continue

                neighbour_distances = cls.get_all_neighbours_distance(node, unvisited_neighbours)
                for neighbor, neighbour_distance in zip(unvisited_neighbours, neighbour_distances):
                    new_cost = node_costs[tuple(node)] + neighbour_distance
                    if node_costs[neighbor] > new_cost:
                        # parentsMap[neighbor] = node
                        node_costs[neighbor] = new_cost
                        heap.heappush(pq, (new_cost, neighbor))

            utility_map = np.ones((scenario.field[0], scenario.field[1]))
            utility_map[:] = np.inf
            keys = np.asarray(list(node_costs.keys()))
            utility_map[keys[:, 0], keys[:, 1]] = list(node_costs.values())
            utility_map = np.round(utility_map, 2)
            return utility_map

        else:
            grid = np.asarray([(a, b) for a in range(scenario.field[0]) for b in range(scenario.field[1])])
            distances = np.linalg.norm(grid[:, np.newaxis, :] - list(scenario.target), axis=-1)
            utility_map = distances.min(axis=-1).reshape((scenario.field[0], scenario.field[1]))
            return utility_map

    @classmethod
    def generate_states(cls, scenario: State, utility, speed, time_cap):
        """
        Generate a list of states representing the movement of pedestrians over time.

        Args:
            cls: The class of the method.
            scenario (State): The initial state of the scenario.
            utility (np.ndarray): A 2D array representing the utility of each position for the pedestrians.
            speed (List[float]): A list of speeds for each pedestrian.
            time_cap (Optional[int]): The maximum timestamp allowed for the generated states.

        Returns:
            List[State]: A list of states representing the movement of pedestrians over time.

        """
        states = [(0, deepcopy(scenario))]
        actions = [*((0, ped, ped_speed) for ped, ped_speed in zip(scenario.pedestrians, speed))]
        while actions:
            current_timestamp, ped, ped_speed = heap.heappop(actions)
            if time_cap is not None and current_timestamp > time_cap:
                break
            old_timestamp, current_state = deepcopy(states[-1])
            current_state: State

            neighbours = cls.get_neighbours(ped, current_state)
            neighbours = cls.filter_occupied_neighbours(neighbours, current_state)
            neighbours = itertools.chain(neighbours, (ped,))
            neighbours = np.array(list(neighbours))

            neighbour_utility = utility[neighbours[:, 0], neighbours[:, 1]]
            neighbour_distance = cls.get_all_neighbours_distance(ped, neighbours)
            best_neighbour_idx = (neighbour_utility + neighbour_distance).argmin()

            best_neighbour = neighbours[best_neighbour_idx]

            step_time = neighbour_distance[best_neighbour_idx] / ped_speed
            new_ped_position = tuple(best_neighbour)
            current_state.pedestrians.remove(ped)
            next_action_time = round(current_timestamp + step_time, 2)

            if new_ped_position in current_state.target:
                print(f"Pedestrian with speed {ped_speed} reached target in {next_action_time} time units")
            else:
                current_state.pedestrians.add(new_ped_position)
                heap.heappush(actions, (next_action_time, new_ped_position, ped_speed))

            states.append((current_timestamp, current_state))

        # to improve visualization performance keep only last state in every second timestep
        filtered_states = [states[0]]
        for i in range(len(states) - 1):
            if ceil(states[i][0]) != ceil(states[i + 1][0]):
                filtered_states.append((ceil(states[i][0]), states[i][1]))
        filtered_states.append((ceil(states[-1][0]), states[-1][1]))
        filtered_states_without_timestamps = [state for ts, state in filtered_states]

        return filtered_states_without_timestamps

    @classmethod
    def get_all_neighbours_distance(cls, cell_1: tuple, cells: Union[list, np.ndarray]) -> np.ndarray:
        """Calculate the Euclidean distance between cell_1 and all cells in cells.

        Args:
        - cell_1 (tuple): The coordinates of the first cell.
        - cells (Union[list, np.ndarray]): A list or numpy array of coordinates representing the cells
          for which to calculate the distance from cell_1.

        Returns:
        - np.ndarray: A numpy array containing the distances between cell_1 and all cells in cells.
        """
        diagonal = np.abs(np.subtract(cells, cell_1)).sum(-1) == 2
        distance = np.ones(diagonal.shape)
        distance[diagonal] = 1.4
        return distance

    @staticmethod
    def get_neighbours(ped, current_state):
        """Return a generator of all neighboring cells that are not obstacles.

        Args:
        - ped (tuple): The coordinates of the pedestrian for which to find neighbors.
        - current_state (State): The current state of the scenario.

        Returns:
        - filter: A generator of all neighboring cells that are not obstacles.
        """
        neighbours = itertools.product((ped[0] - 1, ped[0], ped[0] + 1), (ped[1] - 1, ped[1], ped[1] + 1))
        neighbours = filter(
            lambda coord: 0 <= coord[0] < current_state.field[0] and 0 <= coord[1] < current_state.field[1], neighbours)
        neighbours = filter(lambda neighbour: neighbour not in current_state.obstacles, neighbours)
        return neighbours

    @staticmethod
    def filter_occupied_neighbours(neighbours, current_state):
        """Return a generator of neighboring cells that are not occupied by other pedestrians.

        Args:
        - neighbours (filter): A generator of neighboring cells to check.
        - current_state (State): The current state of the scenario.

        Returns:
        - filter: A generator of neighboring cells that are not occupied by other pedestrians.
        """
        return filter(lambda neighbour: neighbour not in current_state.pedestrians, neighbours)

    def get_states(self):
        """Return the states of the scenario generated by the simulation.

        Returns:
        - list: A list of tuples containing the time and the state of the scenario at that time.
        """
        return self.states


def main():
    scenario = read_scenario('scenarios/scenario_task_2.json')
    sim = Simulation(scenario, dijkstra=False)
    print(sim.get_states())


if __name__ == '__main__':
    main()
