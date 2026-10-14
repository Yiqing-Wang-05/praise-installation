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
    swap_axes: bool = False,
    clamp: bool = False,
) -> tuple[float, float]:
    """Convert an MLX90640 coordinate to normalized ``(u, v)`` space.

    The sensor coordinate range is x=0..31 and y=0..23. When ``clamp`` is
    false, out-of-range inputs remain out of range after normalization. When
    true, each normalized axis is limited to 0.0..1.0. Sensor-axis flips are
    applied before ``swap_axes`` exchanges normalized x/y into output u/v.
    """
    normalized_x = float(x) / SENSOR_MAX_X
    normalized_y = float(y) / SENSOR_MAX_Y

    if flip_x:
        normalized_x = 1.0 - normalized_x
    if flip_y:
        normalized_y = 1.0 - normalized_y

    if swap_axes:
        u, v = normalized_y, normalized_x
    else:
        u, v = normalized_x, normalized_y

    if clamp:
        u = min(1.0, max(0.0, u))
        v = min(1.0, max(0.0, v))

    return u, v


def normalize_thermal_mount_coordinate(
    centroid_x: float,
    centroid_y: float,
    *,
    clamp: bool = True,
) -> tuple[float, float]:
    """Map the fixed installed sensor orientation into canonical table UV.

    Canonical ``u`` increases from real-world left to right. Canonical ``v``
    increases from the audience side / screen bottom toward the far side /
    screen top. Raw centroid values remain in the sensor's 32x24 axes.

    This mounting therefore maps ``u = centroid_y / 23`` and
    ``v = 1 - centroid_x / 31``.
    """
    return normalize_raw_coordinate(
        centroid_x,
        centroid_y,
        flip_x=True,
        swap_axes=True,
        clamp=clamp,
    )
