import time

import py5

from . import config
from .interaction import Interaction
from .renderer import Renderer
from .simulation import Simulation


simulation = Simulation(config)
interaction = Interaction(simulation, config)
renderer = Renderer(config)
_last_time = 0.0


def settings():
    if config.FULLSCREEN:
        py5.full_screen(py5.P2D)
    else:
        py5.size(1280, 720, py5.P2D)
    py5.smooth(4)


def setup():
    global _last_time
    py5.frame_rate(config.TARGET_FPS)
    simulation.reset(py5.width, py5.height)
    _last_time = time.perf_counter()


def draw():
    global _last_time
    now = time.perf_counter()
    dt = min(now - _last_time, 0.05)
    _last_time = now
    simulation.update(dt, py5.width, py5.height)
    renderer.draw(simulation, now)


def mouse_pressed():
    interaction.mouse_pressed(py5.mouse_x, py5.mouse_y)


def mouse_dragged():
    interaction.mouse_dragged(py5.mouse_x, py5.mouse_y)


def mouse_released():
    interaction.mouse_released()


def key_pressed():
    if py5.key in ("a", "A"):
        config.AUTO_MODE = not config.AUTO_MODE
    elif py5.key in ("r", "R"):
        simulation.reset(py5.width, py5.height)


def run():
    py5.run_sketch(sketch_functions=globals(), block=True)
