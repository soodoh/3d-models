"""Tests for the shallow spring-side-down Gridfinity Hawthorne-strainer cradle."""

from __future__ import annotations

import unittest

from print_models.catalog import load_models
from print_models.models.gridfinity_hawthorne_strainer import PARAMETERS, build


class HawthorneStrainerGeometryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.cradle = build()
        cls.shape = cls.cradle.val()

    def test_catalog_exposes_measured_strainer_dimensions(self) -> None:
        models = load_models()

        self.assertIn("gridfinity_hawthorne_strainer", models)
        self.assertEqual(PARAMETERS["unit_width"], 3)
        self.assertEqual(PARAMETERS["unit_depth"], 4)
        self.assertEqual(PARAMETERS["unit_height"], 4)
        self.assertEqual(PARAMETERS["pocket_depth_mm"], 18.0)
        self.assertEqual(PARAMETERS["spring_height_mm"], 18.0)
        self.assertEqual(PARAMETERS["overall_length_mm"], 137.0)
        self.assertEqual(PARAMETERS["widest_width_mm"], 99.0)
        self.assertEqual(PARAMETERS["handle_straight_width_mm"], 30.0)

    def test_cradle_preserves_three_by_four_four_unit_envelope(self) -> None:
        bounding_box = self.shape.BoundingBox()

        self.assertAlmostEqual(bounding_box.xlen, 125.5, places=3)
        self.assertAlmostEqual(bounding_box.ylen, 167.5, places=3)
        self.assertAlmostEqual(bounding_box.zlen, 31.8, places=3)
        self.assertEqual(len(self.cradle.solids().vals()), 1)

    def test_traced_head_well_is_deep_and_preserves_floor(self) -> None:
        import cadquery as cq

        self.assertTrue(self.shape.isInside(cq.Vector(0.0, 18.0, 9.5), 1e-6))
        self.assertFalse(self.shape.isInside(cq.Vector(0.0, 18.0, 10.5), 1e-6))
        self.assertTrue(self.shape.isInside(cq.Vector(52.0, 18.0, 27.5), 1e-6))

    def test_handle_track_is_shallower_than_head_well(self) -> None:
        import cadquery as cq

        self.assertTrue(self.shape.isInside(cq.Vector(0.0, -50.0, 24.5), 1e-6))
        self.assertFalse(self.shape.isInside(cq.Vector(0.0, -50.0, 25.5), 1e-6))
        self.assertFalse(self.shape.isInside(cq.Vector(0.0, 18.0, 10.5), 1e-6))

    def test_cutout_follows_the_photographed_outer_profile(self) -> None:
        import cadquery as cq

        self.assertFalse(self.shape.isInside(cq.Vector(50.0, 35.0, 27.0), 1e-6))
        self.assertTrue(self.shape.isInside(cq.Vector(52.0, 35.0, 27.0), 1e-6))
        self.assertTrue(self.shape.isInside(cq.Vector(30.0, -20.0, 27.0), 1e-6))
        self.assertFalse(self.shape.isInside(cq.Vector(15.5, -40.0, 27.0), 1e-6))
        self.assertTrue(self.shape.isInside(cq.Vector(17.5, -40.0, 27.0), 1e-6))
        self.assertFalse(self.shape.isInside(cq.Vector(0.0, 68.0, 27.0), 1e-6))
        self.assertTrue(self.shape.isInside(cq.Vector(0.0, 70.0, 27.0), 1e-6))

    def test_rejects_a_pocket_shallower_than_the_spring(self) -> None:
        with self.assertRaisesRegex(ValueError, "at least spring_height_mm"):
            build(pocket_depth_mm=17.0)

    def test_rejects_a_short_box_for_the_eighteen_mm_pocket(self) -> None:
        with self.assertRaisesRegex(ValueError, "preserving a 2 mm cavity floor"):
            build(unit_height=3)

    def test_rejects_a_footprint_that_cannot_fit_the_strainer_width(self) -> None:
        with self.assertRaisesRegex(ValueError, "safe deck ring"):
            build(unit_width=2)

    def test_rejects_a_footprint_that_cannot_fit_the_length(self) -> None:
        with self.assertRaisesRegex(ValueError, "safe deck ring"):
            build(unit_depth=3)


if __name__ == "__main__":
    unittest.main()
