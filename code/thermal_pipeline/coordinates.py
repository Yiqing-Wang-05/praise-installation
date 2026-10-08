"""Normalize raw MLX90640 pixel coordinates without display assumptions."""

from __future__ import annotations


SENSOR_MAX_X = 31.0
SENSOR_MAX_Y = 23.0


def normalize_raw_coordinate(
    x: float,
    y: float,
    *,
    flip_x: bool = False,
    flip_y: bool = False,
    clamp: bool = False,
) -> tuple[float, float]:
    """Convert an MLX90640 coordinate to normalized ``(u, v)`` space.

    The sensor coordinate range is x=0..31 and y=0..23. When ``clamp`` is
    false, out-of-range inputs remain out of range after normalization. When
    true, each normalized axis is limited to 0.0..1.0.
    """
    u = float(x) / SENSOR_MAX_X
    v = float(y) / SENSOR_MAX_Y

    if flip_x:
        u = 1.0 - u
    if flip_y:
        v = 1.0 - v

    if clamp:
        u = min(1.0, max(0.0, u))
        v = min(1.0, max(0.0, v))

    return u, v
