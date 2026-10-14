import unittest

from coordinates import (
    normalize_raw_coordinate,
    normalize_thermal_mount_coordinate,
)


class NormalizeRawCoordinateTests(unittest.TestCase):
    def test_sensor_corners(self) -> None:
        self.assertEqual(normalize_raw_coordinate(0, 0), (0.0, 0.0))
        self.assertEqual(normalize_raw_coordinate(31, 23), (1.0, 1.0))

    def test_geometric_center(self) -> None:
        u, v = normalize_raw_coordinate(15.5, 11.5)
        self.assertAlmostEqual(u, 0.5)
        self.assertAlmostEqual(v, 0.5)

    def test_axis_flips(self) -> None:
        self.assertEqual(
            normalize_raw_coordinate(0, 0, flip_x=True),
            (1.0, 0.0),
        )
        self.assertEqual(
            normalize_raw_coordinate(0, 0, flip_y=True),
            (0.0, 1.0),
        )
        self.assertEqual(
            normalize_raw_coordinate(31, 23, flip_x=True, flip_y=True),
            (0.0, 0.0),
        )

    def test_swap_axes_uses_each_sensor_axis_scale(self) -> None:
        self.assertEqual(
            normalize_raw_coordinate(31, 0, swap_axes=True),
            (0.0, 1.0),
        )
        self.assertEqual(
            normalize_raw_coordinate(0, 23, swap_axes=True),
            (1.0, 0.0),
        )

    def test_fixed_thermal_mount_mapping(self) -> None:
        self.assertEqual(
            normalize_thermal_mount_coordinate(31, 0),
            (0.0, 0.0),
        )
        self.assertEqual(
            normalize_thermal_mount_coordinate(0, 23),
            (1.0, 1.0),
        )
        self.assertEqual(
            normalize_thermal_mount_coordinate(15.5, 11.5),
            (0.5, 0.5),
        )

    def test_clamp_limits_out_of_range_values(self) -> None:
        self.assertEqual(
            normalize_raw_coordinate(-4, 30, clamp=True),
            (0.0, 1.0),
        )

    def test_unclamped_values_can_extend_past_unit_range(self) -> None:
        u, v = normalize_raw_coordinate(-1, 24)
        self.assertLess(u, 0.0)
        self.assertGreater(v, 1.0)

    def test_thermal_mount_clamps_by_default(self) -> None:
        self.assertEqual(
            normalize_thermal_mount_coordinate(40, -2),
            (0.0, 0.0),
        )


if __name__ == "__main__":
    unittest.main()
