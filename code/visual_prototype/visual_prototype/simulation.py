import math
import random

from .node import Node
from .ripples import Ripple


class Simulation:
    def __init__(self, cfg):
        self.cfg = cfg
        self.nodes = []
        self.ripples = []
        self.next_id = 1

    def reset(self, width: float, height: float) -> None:
        self.nodes.clear()
        self.ripples.clear()
        count = min(max(self.cfg.INITIAL_NODES, self.cfg.MIN_NODES), self.cfg.MAX_NODES)
        center_x, center_y = width * 0.5, height * 0.5
        radius_x, radius_y = width * 0.29, height * 0.25
        for index in range(count):
            angle = math.tau * index / count + random.uniform(-0.28, 0.28)
            x = center_x + math.cos(angle) * radius_x * random.uniform(0.65, 1.0)
            y = center_y + math.sin(angle) * radius_y * random.uniform(0.65, 1.0)
            self.add_node(x, y, with_ripple=False)

    def add_node(self, x: float, y: float, with_ripple: bool = True):
        if len(self.nodes) >= self.cfg.MAX_NODES:
            return None
        node = Node(
            self.next_id,
            x,
            y,
            random.uniform(0.0, math.tau),
            random.uniform(0.0, math.tau),
            random.uniform(0.0, math.tau),
        )
        self.next_id += 1
        self.nodes.append(node)
        if with_ripple:
            self.ripples.append(Ripple(x, y))
        return node

    def update(self, dt: float, width: float, height: float) -> None:
        for node in self.nodes:
            node.update(dt, width, height, self.cfg)
        for ripple in self.ripples:
            ripple.update(dt)
        self.ripples = [ripple for ripple in self.ripples if ripple.alive(self.cfg)]

