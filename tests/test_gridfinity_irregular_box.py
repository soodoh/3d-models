"""Geometry tests for the split irregular Gridfinity box."""

from __future__ import annotations

import unittest

import cadquery as cq

from print_models.catalog import load_models
from print_models.models import gridfinity_irregular_box


class GridfinityIrregularBoxTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.whole_box = gridfinity_irregular_box._build_whole_box(
            unit_height=6,
            wall_thickness_mm=1.0,
        )
        cls.parts = gridfinity_irregular_box.build()

    def assert_inside(self, x: float, y: float, z: float) -> None:
        self.assertTrue(self.whole_box.val().isInside(cq.Vector(x, y, z), 1e-5))

    def assert_outside(self, x: float, y: float, z: float) -> None:
        self.assertFalse(self.whole_box.val().isInside(cq.Vector(x, y, z), 1e-5))

    def test_registered_with_fixed_split_output_names(self) -> None:
        self.assertIn(gridfinity_irregular_box.NAME, load_models())
        self.assertEqual(
            tuple(self.parts),
            (
                "3x3_plus_1x4x6u_primary",
                "3x3_plus_1x4x6u_second_1x2_open",
            ),
        )

    def test_has_requested_irregular_floor_footprint(self) -> None:
        floor_z = 6.0
        for x in (-126.0, -84.0, -42.0):
            for y in (-42.0, 0.0, 42.0):
                with self.subTest(x=x, y=y):
                    self.assert_inside(x, y, floor_z)
        for x in (0.0, 42.0, 84.0, 126.0):
            with self.subTest(x=x):
                self.assert_inside(x, 0.0, floor_z)
                self.assert_outside(x, 42.0, floor_z)
                self.assert_outside(x, -42.0, floor_z)

        bounding_box = self.whole_box.val().BoundingBox()
        self.assertAlmostEqual(bounding_box.xlen, 293.5, places=6)
        self.assertAlmostEqual(bounding_box.ylen, 125.5, places=6)
        self.assertAlmostEqual(bounding_box.zlen, 45.8, places=6)

    def test_shared_boundaries_are_open_through_the_full_height(self) -> None:
        for z in (7.1, 20.0, 44.0, 45.7):
            with self.subTest(z=z, boundary="main_to_arm"):
                self.assert_outside(-21.25, 0.0, z)
            with self.subTest(z=z, boundary="row_to_main"):
                self.assert_outside(-84.0, 20.75, z)
                self.assert_outside(-84.0, -20.75, z)

        self.assert_inside(42.0, 20.25, 20.0)
        self.assert_inside(-84.0, 62.25, 20.0)

    def test_convex_corner_walls_have_no_gaps(self) -> None:
        corner_wall_points = (
            (-145.0, 61.0),
            (-145.0, -61.0),
            (-23.0, 61.0),
            (-23.0, -61.0),
            (145.0, 19.0),
            (145.0, -19.0),
        )
        for x, y in corner_wall_points:
            with self.subTest(x=x, y=y):
                self.assert_inside(x, y, 20.0)

    def test_opposite_wall_has_no_row_end_cutouts(self) -> None:
        for z in (20.0, 44.0, 45.5):
            for y in (-20.5, -20.0, -19.0, 19.0, 20.0, 20.5):
                with self.subTest(z=z, y=y):
                    self.assert_inside(-146.5, y, z)

    def test_stacking_lip_is_continuous_around_irregular_perimeter(self) -> None:
        lip_points = (
            (-145.5, 0.0),
            (-84.0, 61.5),
            (-84.0, -61.5),
            (-22.5, 42.0),
            (-22.5, -42.0),
            (42.0, 19.5),
            (42.0, -19.5),
            (145.5, 0.0),
            (-22.5, 22.0),
            (-22.5, -22.0),
            (-20.0, 19.5),
            (-20.0, -19.5),
        )
        for x, y in lip_points:
            with self.subTest(x=x, y=y):
                self.assert_outside(x, y, 20.0)
                self.assert_inside(x, y, 44.0)

    def test_splits_final_open_one_by_two_section_as_second_part(self) -> None:
        primary = self.parts["3x3_plus_1x4x6u_primary"]
        second_part = self.parts["3x3_plus_1x4x6u_second_1x2_open"]
        primary_bounds = primary.val().BoundingBox()
        second_part_bounds = second_part.val().BoundingBox()

        self.assertAlmostEqual(primary_bounds.xmax, gridfinity_irregular_box.PART_SPLIT_X_MM)
        self.assertAlmostEqual(second_part_bounds.xmin, gridfinity_irregular_box.PART_SPLIT_X_MM)
        self.assertAlmostEqual(primary_bounds.xlen, 209.75, places=6)
        self.assertAlmostEqual(primary_bounds.ylen, 125.5, places=6)
        self.assertAlmostEqual(second_part_bounds.xlen, 83.75, places=6)
        self.assertAlmostEqual(second_part_bounds.ylen, 41.5, places=6)

        for z in (7.1, 20.0, 44.0):
            with self.subTest(z=z):
                self.assertFalse(
                    second_part.val().isInside(
                        cq.Vector(gridfinity_irregular_box.PART_SPLIT_X_MM + 0.1, 0.0, z),
                        1e-5,
                    )
                )

    def test_split_parts_are_valid_and_preserve_whole_volume(self) -> None:
        for part in self.parts.values():
            self.assertTrue(part.val().isValid())
            self.assertEqual(len(part.solids().vals()), 1)

        split_volume = sum(part.val().Volume() for part in self.parts.values())
        self.assertAlmostEqual(split_volume, self.whole_box.val().Volume(), places=3)

    def test_validates_parameters(self) -> None:
        for invalid_height in (True, 0, 1.5):
            with self.subTest(unit_height=invalid_height):
                with self.assertRaisesRegex(ValueError, "unit_height must be a positive integer"):
                    gridfinity_irregular_box.build(unit_height=invalid_height)

        with self.assertRaisesRegex(ValueError, "wall_thickness_mm must be greater than zero"):
            gridfinity_irregular_box.build(wall_thickness_mm=0.0)
        with self.assertRaisesRegex(ValueError, "leaves no interior space"):
            gridfinity_irregular_box.build(wall_thickness_mm=21.0)


if __name__ == "__main__":
    unittest.main()
