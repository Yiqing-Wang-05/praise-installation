from dataclasses import dataclass


@dataclass
class Ripple:
    x: float
    y: float
    age: float = 0.0

    def update(self, dt: float) -> None:
        self.age += dt

    def alive(self, cfg) -> bool:
        return self.age < cfg.RIPPLE_DURATION

