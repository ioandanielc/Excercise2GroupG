from functools import partial
from typing import List

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from IPython.display import HTML
from matplotlib import animation
from tqdm import autonotebook as tqdm

from ex1.simulation import Simulation
from ex1.utility import read_scenario, State


def run_scenario(filepath: str, dijkstra: bool = True, model_demographic_speed: bool = False,
                 time_cap: float = None) -> 'Visualizer':
    """
    Runs a simulation of a given scenario and returns the visualizer.

    Args:
        filepath: Path of the scenario file to simulate.
        dijkstra: Use Dijkstra algorithm instead of A*.
        model_demographic_speed: Use the demographic speed model instead of the constant speed model.
        time_cap: Maximum time to simulate.

    Returns:
        Visualizer: A visualizer instance of the simulation.

    """
    scenario = read_scenario(filepath)
    states = Simulation(scenario, dijkstra=dijkstra, model_demographic_speed=model_demographic_speed,
                        time_cap=time_cap).get_states()

    vis = Visualizer(states)
    return vis


class Visualizer:
    def __init__(self, states: List[State], draw_every_cell: bool = False):
        """
        Initializes the Visualizer object.

        Args:
            states: List of State objects to visualize.
            draw_every_cell: Whether to draw every cell of the field (may be slow).

        """
        self.states = states
        plt.ioff()
        self.fig, ax = plt.subplots()
        plt.ion()
        if draw_every_cell:
            ax.set_xticks(np.arange(0, states[0].field[1] + 1, 1))
            ax.set_yticks(np.arange(0, states[0].field[0] + 1, 1))
        plt.grid()

        ax.set_xlim((0, states[0].field[1]))
        ax.set_ylim((0, states[0].field[0]))

        colors = ['b', 'r', 'g']
        cmap = matplotlib.colors.ListedColormap(colors)
        self.sc_plot = ax.scatter([], [], c=[], cmap=cmap)
        self.anim = self._draw()

    def get_anim(self) -> animation.FuncAnimation:
        """
        Returns the animation.

        Returns:
            FuncAnimation: The animation instance.

        """
        return self.anim

    def _draw(self) -> animation.FuncAnimation:
        """
        Draws the animation.

        Returns:
            FuncAnimation: The animation instance.

        """
        offsets = []
        colors = []
        for state in self.states:
            points = np.asarray((list(state.pedestrians) + list(state.obstacles) + list(state.target)))
            points[..., 0], points[..., 1] = points[..., 1], points[..., 0].copy()
            offsets.append(points)
            color = np.concatenate((
                np.zeros(len(state.pedestrians)),
                np.zeros(len(state.obstacles)) + 1,
                np.zeros(len(state.target)) + 2,
            ))
            colors.append(color)

        def init(sc_plot):
            sc_plot.set_offsets([[0, 0]])
            return (sc_plot,)

        pbar = tqdm.tqdm(total=len(self.states))

        def animate(i, sc_plot):
            pbar.update(1)
            sc_plot.set_offsets(offsets[i])
            sc_plot.set_array(colors[i])
            return (sc_plot,)

        self.anim = animation.FuncAnimation(self.fig, partial(animate, sc_plot=self.sc_plot),
                                            init_func=partial(init, sc_plot=self.sc_plot), frames=len(self.states),
                                            interval=500, blit=True)
        return self.anim

    def get_video(self):
        """
        Creates the html video tag where video can be downloaded as a file
        :return: HTML
        """
        return HTML(self.anim.to_html5_video())
