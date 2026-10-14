"""Coordinate utilities for the MLX90640 thermal pipeline."""

from .coordinates import (
    normalize_raw_coordinate,
    normalize_thermal_mount_coordinate,
)

__all__ = ["normalize_raw_coordinate", "normalize_thermal_mount_coordinate"]
