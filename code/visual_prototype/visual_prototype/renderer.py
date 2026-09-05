import math

import py5

from .connections import bezier_points, choose_connections


def _bezier_position(points, t: float):
    p0, p1, p2, p3 = points
    u = 1.0 - t
    weights = (u**3, 3 * u * u * t, 3 * u * t * t, t**3)
    return tuple(sum(point[axis] * weight for point, weight in zip(points, weights))
                 for axis in (0, 1))


def _bezier_tangent(points, t: float):
    p0, p1, p2, p3 = points
    u = 1.0 - t
    dx = (3 * u * u * (p1[0] - p0[0]) + 6 * u * t * (p2[0] - p1[0])
          + 3 * t * t * (p3[0] - p2[0]))
    dy = (3 * u * u * (p1[1] - p0[1]) + 6 * u * t * (p2[1] - p1[1])
          + 3 * t * t * (p3[1] - p2[1]))
    length = max(math.hypot(dx, dy), 1.0)
    return dx / length, dy / length


def _offset_points(points, amount):
    dx, dy = points[-1][0] - points[0][0], points[-1][1] - points[0][1]
    length = max(math.hypot(dx, dy), 1.0)
    nx, ny = -dy / length, dx / length
    return tuple((x + nx * amount, y + ny * amount) for x, y in points)


class Renderer:
    def __init__(self, cfg):
        self.cfg = cfg

    def draw(self, simulation, now: float) -> None:
        py5.background(*self.cfg.BACKGROUND_RGB)
        py5.blend_mode(py5.ADD)
        self._draw_ambient(simulation.nodes, now)
        self._draw_connections(simulation.nodes, now)
        self._draw_ripples(simulation.ripples)
        for node in simulation.nodes:
            self._draw_node(node, now)
        py5.blend_mode(py5.BLEND)

    def _draw_ambient(self, nodes, now):
        if not nodes:
            return
        center_x = sum(node.x for node in nodes) / len(nodes)
        center_y = sum(node.y for node in nodes) / len(nodes)
        activity = sum(node.pulse(now, self.cfg) for node in nodes) / len(nodes)
        diameter = min(py5.width, py5.height) * self.cfg.AMBIENT_RADIUS * (0.9 + activity * 0.18)
        py5.no_stroke()
        for layer in range(8, 0, -1):
            fraction = layer / 8
            py5.fill(*self.cfg.NODE_COLOR,
                     self.cfg.AMBIENT_GLOW * (1.15 - fraction) ** 2)
            py5.circle(center_x, center_y, diameter * fraction)

    def _draw_connections(self, nodes, now: float) -> None:
        for connection in choose_connections(nodes, self.cfg):
            points = bezier_points(connection, now, self.cfg)
            proximity = max(0.0, 1.0 - connection.distance / self.cfg.CONNECTION_DISTANCE)
            growth = min(connection.a.age, connection.b.age) / self.cfg.CONNECTION_GROWTH_TIME
            growth = min(max(growth, 0.0), 1.0)
            growth = growth * growth * (3.0 - 2.0 * growth)
            hierarchy = 1.0 if connection.trunk else 0.58
            alpha = (105 * self.cfg.LINE_BRIGHTNESS * hierarchy
                     * (0.5 + proximity * 0.5) * growth)

            # A soft sheath and several close filaments create a mycelial strand.
            py5.no_fill()
            py5.stroke(*self.cfg.LINE_COLOR, alpha * 0.12)
            py5.stroke_weight(self.cfg.LINE_WEIGHT * 7.0)
            py5.bezier(*points[0], *points[1], *points[2], *points[3])
            for offset, strength, weight in ((-1.0, 0.24, 0.7),
                                             (0.0, 1.0, 1.0),
                                             (1.0, 0.18, 0.58)):
                strand = _offset_points(points, offset * self.cfg.FILAMENT_SPREAD)
                py5.stroke(*self.cfg.LINE_COLOR, alpha * strength)
                py5.stroke_weight(self.cfg.LINE_WEIGHT * weight)
                py5.bezier(*strand[0], *strand[1], *strand[2], *strand[3])

            if connection.trunk:
                self._draw_side_branch(connection, points, alpha)

            # A single low-contrast current, closer to a shimmer than a particle.
            travel = ((now * self.cfg.ENERGY_SPEED * self.cfg.ANIMATION_SPEED
                       + connection.a.node_id * 0.137) % 1.18) - 0.09
            if 0.0 <= travel <= 1.0:
                x, y = _bezier_position(points, travel)
                py5.no_stroke()
                py5.fill(*self.cfg.CORE_COLOR, alpha * 0.22)
                py5.circle(x, y, 7.5)
                py5.fill(*self.cfg.CORE_COLOR, alpha * 0.72)
                py5.circle(x, y, 2.0)

    def _draw_side_branch(self, connection, points, alpha):
        seed = (connection.a.node_id * 31 + connection.b.node_id * 17) % 100
        if seed / 100.0 > self.cfg.SIDE_BRANCH_AMOUNT:
            return
        t = 0.34 + (seed % 25) / 100.0
        x, y = _bezier_position(points, t)
        tx, ty = _bezier_tangent(points, t)
        side = -1 if seed % 2 else 1
        nx, ny = -ty * side, tx * side
        length = 20.0 + seed % 24
        end = (x + tx * length * 0.34 + nx * length,
               y + ty * length * 0.34 + ny * length)
        c1 = (x + tx * length * 0.18 + nx * length * 0.18,
              y + ty * length * 0.18 + ny * length * 0.18)
        c2 = (end[0] - tx * length * 0.18, end[1] - ty * length * 0.18)
        py5.no_fill()
        py5.stroke(*self.cfg.LINE_COLOR, alpha * 0.12)
        py5.stroke_weight(self.cfg.LINE_WEIGHT * 3.4)
        py5.bezier(x, y, *c1, *c2, *end)
        py5.stroke(*self.cfg.LINE_COLOR, alpha * 0.42)
        py5.stroke_weight(self.cfg.LINE_WEIGHT * 0.55)
        py5.bezier(x, y, *c1, *c2, *end)

    def _draw_node(self, node, now: float) -> None:
        pulse = node.pulse(now, self.cfg)
        size = self.cfg.NODE_SIZE * (1.0 + (pulse * 2.0 - 1.0) * self.cfg.BREATHING_AMOUNT)
        brightness = 1.0 - self.cfg.BREATHING_BRIGHTNESS + pulse * self.cfg.BREATHING_BRIGHTNESS
        glow_breath = 1.0 - self.cfg.BREATHING_GLOW + pulse * self.cfg.BREATHING_GLOW
        halo = size * self.cfg.GLOW_RADIUS * self.cfg.GLOW * glow_breath

        py5.no_stroke()
        # Outer haze: broad and quiet.
        for layer in range(self.cfg.GLOW_LAYERS, 0, -1):
            fraction = layer / self.cfg.GLOW_LAYERS
            diameter = size + halo * fraction
            alpha = 6.0 * self.cfg.GLOW * brightness * (1.12 - fraction) ** 2.0
            py5.fill(*self.cfg.NODE_COLOR, alpha)
            py5.circle(node.x, node.y, diameter)

        # Inner glow: denser concentric light before the near-white core.
        for layer in range(6, 0, -1):
            fraction = layer / 6
            py5.fill(*self.cfg.NODE_COLOR, 21 * brightness * (1.2 - fraction))
            py5.circle(node.x, node.y,
                       size * (1.0 + self.cfg.INNER_GLOW_SIZE * fraction))
        py5.fill(*self.cfg.NODE_COLOR, 205 * brightness)
        py5.circle(node.x, node.y, size * 1.2)
        py5.fill(*self.cfg.CORE_COLOR, 255 * self.cfg.CORE_BRIGHTNESS * brightness)
        py5.circle(node.x, node.y, size * 0.58)
        py5.fill(255, 250, 233, 245 * brightness)
        py5.circle(node.x, node.y, size * 0.22)

    def _draw_ripples(self, ripples) -> None:
        py5.no_fill()
        for ripple in ripples:
            progress = min(ripple.age / self.cfg.RIPPLE_DURATION, 1.0)
            eased = 1.0 - (1.0 - progress) ** 3
            diameter = 12.0 + self.cfg.RIPPLE_MAX_RADIUS * 2.0 * eased
            alpha = 68.0 * (1.0 - progress) ** 2 * self.cfg.RIPPLE_STRENGTH
            py5.stroke(*self.cfg.RIPPLE_COLOR, alpha)
            py5.stroke_weight(1.25)
            py5.circle(ripple.x, ripple.y, diameter)
