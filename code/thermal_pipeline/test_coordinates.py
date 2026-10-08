import unittest

from coordinates import normalize_raw_coordinate


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

    def test_clamp_limits_out_of_range_values(self) -> None:
        self.assertEqual(
            normalize_raw_coordinate(-4, 30, clamp=True),
            (0.0, 1.0),
        )

    def test_unclamped_values_can_extend_past_unit_range(self) -> None:
        u, v = normalize_raw_coordinate(-1, 24)
        self.assertLess(u, 0.0)
        self.assertGreater(v, 1.0)


if __name__ == "__main__":
    unittest.main()
