from dataclasses import dataclass
import math


@dataclass
class Node:
    node_id: int
    x: float
    y: float
    phase: float
    drift_phase_x: float
    drift_phase_y: float
    age: float = 0.0
    dragging: bool = False

    def update(self, dt: float, width: float, height: float, cfg) -> None:
        self.age += dt
        if not cfg.AUTO_MODE or self.dragging:
            return

        speed = cfg.ANIMATION_SPEED
        self.x += math.sin(self.age * 0.19 * speed + self.drift_phase_x) * cfg.DRIFT_SPEED * dt
        self.y += math.cos(self.age * 0.16 * speed + self.drift_phase_y) * cfg.DRIFT_SPEED * dt
        self.x = min(max(self.x, cfg.EDGE_MARGIN), width - cfg.EDGE_MARGIN)
        self.y = min(max(self.y, cfg.EDGE_MARGIN), height - cfg.EDGE_MARGIN)

    def pulse(self, now: float, cfg) -> float:
        wave = math.sin(now * cfg.BREATHING_SPEED * cfg.ANIMATION_SPEED * math.tau + self.phase)
        return wave * 0.5 + 0.5
