import math


class Interaction:
    def __init__(self, simulation, cfg):
        self.simulation = simulation
        self.cfg = cfg
        self.dragged_node = None

    def mouse_pressed(self, x: float, y: float) -> None:
        nearest = None
        nearest_distance = self.cfg.DRAG_RADIUS
        for node in reversed(self.simulation.nodes):
            distance = math.hypot(node.x - x, node.y - y)
            if distance < nearest_distance:
                nearest, nearest_distance = node, distance
        if nearest is not None:
            self.dragged_node = nearest
            nearest.dragging = True
        else:
            self.simulation.add_node(x, y)

    def mouse_dragged(self, x: float, y: float) -> None:
        if self.dragged_node is not None:
            self.dragged_node.x = x
            self.dragged_node.y = y

    def mouse_released(self) -> None:
        if self.dragged_node is not None:
            self.dragged_node.dragging = False
        self.dragged_node = None

