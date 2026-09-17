"""Tests for the compact four-teaspoon Gridfinity box."""

from __future__ import annotations

import unittest

from print_models.catalog import load_models
from print_models.models.gridfinity_teaspoon import PARAMETERS, _teaspoon_width_profile, build


class TeaspoonGeometryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.part = build()
        cls.shape = cls.part.val()

    def test_catalog_exposes_supplied_spoon_measurements(self) -> None:
        self.assertIn("gridfinity_teaspoon", load_models())
        self.assertEqual(PARAMETERS["unit_width"], 1)
        self.assertEqual(PARAMETERS["unit_depth"], 4)
        self.assertEqual(PARAMETERS["unit_height"], 6)
        self.assertEqual(PARAMETERS["spoon_length_mm"], 128.0)
        self.assertEqual(PARAMETERS["spoon_bowl_width_mm"], 30.5)
        self.assertEqual(PARAMETERS["spoon_handle_length_mm"], 99.0)
        self.assertEqual(PARAMETERS["spoon_handle_end_width_mm"], 3.8)
        self.assertEqual(PARAMETERS["spoon_handle_middle_width_mm"], 6.2)
        self.assertEqual(PARAMETERS["spoon_handle_neck_width_mm"], 4.0)
        self.assertEqual(PARAMETERS["stack_bowl_height_mm"], 22.0)
        self.assertEqual(PARAMETERS["stack_neck_height_mm"], 14.0)
        self.assertEqual(PARAMETERS["stack_handle_end_height_mm"], 29.0)
        self.assertEqual(PARAMETERS["fit_clearance_mm"], 1.0)

    def test_build_returns_one_valid_compact_gridfinity_solid(self) -> None:
        bounds = self.shape.BoundingBox()

        self.assertTrue(self.shape.isValid())
        self.assertEqual(len(self.part.solids().vals()), 1)
        self.assertEqual(len(self.part.shells().vals()), 1)
        self.assertAlmostEqual(bounds.xlen, 41.5, places=3)
        self.assertAlmostEqual(bounds.ylen, 167.5, places=3)
        self.assertAlmostEqual(bounds.zlen, 42.0, places=3)

    def test_side_walls_are_flush_with_the_cutout_infill(self) -> None:
        self.assertAlmostEqual(self.shape.BoundingBox().zmax, 42.0, places=3)

    def test_profile_uses_measured_handle_and_bowl_widths(self) -> None:
        profile = dict(
            _teaspoon_width_profile(
                spoon_length_mm=128.0,
                handle_length_mm=99.0,
                bowl_width_mm=30.5,
                handle_end_width_mm=3.8,
                handle_middle_width_mm=6.2,
                handle_neck_width_mm=4.0,
            )
        )

        self.assertAlmostEqual(profile[0.00] * 30.5, 3.8)
        self.assertAlmostEqual(profile[0.30] * 30.5, 6.2)
        self.assertAlmostEqual(profile[0.60] * 30.5, 4.0)
        self.assertAlmostEqual(profile[0.88] * 30.5, 30.5)
        self.assertEqual(profile[1.00], 0.0)

    def test_spoon_pocket_keeps_a_two_millimeter_floor(self) -> None:
        import cadquery as cq

        for x_position, y_position in ((0.0, -64.0), (0.0, 48.0), (14.0, 48.0)):
            with self.subTest(x_position=x_position, y_position=y_position):
                self.assertFalse(self.shape.isInside(cq.Vector(x_position, y_position, 9.5), 1e-6))
                self.assertTrue(self.shape.isInside(cq.Vector(x_position, y_position, 8.5), 1e-6))

    def test_wall_to_wall_finger_bay_crosses_the_lower_handle(self) -> None:
        import cadquery as cq

        for x_position in (-18.0, 0.0, 18.0):
            self.assertFalse(self.shape.isInside(cq.Vector(x_position, -31.0, 20.0), 1e-6))
        self.assertTrue(self.shape.isInside(cq.Vector(-20.0, -31.0, 20.0), 1e-6))
        self.assertTrue(self.shape.isInside(cq.Vector(20.0, -31.0, 20.0), 1e-6))
        self.assertTrue(self.shape.isInside(cq.Vector(10.0, -47.0, 20.0), 1e-6))
        self.assertTrue(self.shape.isInside(cq.Vector(10.0, -15.0, 20.0), 1e-6))

    def test_rejects_invalid_measurements_and_short_boxes(self) -> None:
        with self.assertRaisesRegex(ValueError, "positive integer"):
            build(unit_width=0)
        with self.assertRaisesRegex(ValueError, "shorter than"):
            build(spoon_handle_length_mm=128.0)
        with self.assertRaisesRegex(ValueError, "thickest handle width"):
            build(spoon_bowl_width_mm=6.0)
        with self.assertRaisesRegex(ValueError, "must exceed both"):
            build(spoon_handle_middle_width_mm=4.0)
        with self.assertRaisesRegex(ValueError, "unit_height is too short"):
            build(unit_height=5)


if __name__ == "__main__":
    unittest.main()
