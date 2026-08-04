"""Tests for the support-free face-down Gridfinity OXO strainer holder."""

from __future__ import annotations

import math
import unittest

from print_models.catalog import load_models
from print_models.models.gridfinity_oxo_cocktail_strainer import (
    PARAMETERS,
    _build_face_down_pocket_cutter,
    _position_plan_cutter,
    build,
)

POCKET_PARAMETERS = {
    "pocket_bottom_z": 10.0,
    "deck_top_z": 28.0,
    "overall_length_mm": 214.0,
    "strainer_diameter_mm": 82.0,
    "small_handle_width_mm": 17.7,
    "wide_handle_width_mm": 26.0,
    "wide_handle_length_mm": 71.0,
    "handle_ferrule_length_mm": 12.0,
    "small_handle_height_mm": 3.5,
    "finger_scoop_diameter_mm": 20.0,
    "tip_loop_length_mm": 15.0,
    "tip_loop_outer_width_mm": 33.0,
    "fit_clearance_mm": 1.0,
}


class OxoCocktailStrainerPocketTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.cutter = _build_face_down_pocket_cutter(**POCKET_PARAMETERS)
        cls.shape = cls.cutter.val()

    def test_catalog_exposes_face_down_holder_dimensions(self) -> None:
        models = load_models()

        self.assertIn("gridfinity_oxo_cocktail_strainer", models)
        self.assertEqual(PARAMETERS["unit_width"], 5)
        self.assertEqual(PARAMETERS["unit_depth"], 3)
        self.assertEqual(PARAMETERS["unit_height"], 4)
        self.assertEqual(PARAMETERS["pocket_depth_mm"], 18.0)
        self.assertEqual(PARAMETERS["overall_length_mm"], 214.0)
        self.assertEqual(PARAMETERS["strainer_diameter_mm"], 82.0)
        self.assertEqual(PARAMETERS["finger_scoop_diameter_mm"], 20.0)
        self.assertEqual(PARAMETERS["strainer_rotation_degrees"], 24.7)

    def test_straight_pocket_preserves_cleared_plan_envelope(self) -> None:
        bounding_box = self.shape.BoundingBox()

        self.assertAlmostEqual(bounding_box.xlen, 216.0, places=3)
        self.assertAlmostEqual(bounding_box.ylen, 84.0, places=3)
        self.assertAlmostEqual(bounding_box.zmin, 10.0, places=3)
        self.assertAlmostEqual(bounding_box.zmax, 28.2, places=3)
        self.assertEqual(len(self.cutter.solids().vals()), 1)

    def test_pocket_has_separate_rail_recesses(self) -> None:
        import cadquery as cq

        for z in (10.1, 27.9):
            self.assertTrue(self.shape.isInside(cq.Vector(-20.0, 7.1, z), 1e-6))
            self.assertTrue(self.shape.isInside(cq.Vector(-20.0, -7.1, z), 1e-6))
            self.assertFalse(self.shape.isInside(cq.Vector(-20.0, 0.0, z), 1e-6))

    def test_pocket_has_paired_full_depth_finger_scoops(self) -> None:
        import cadquery as cq

        for z in (10.1, 27.9):
            self.assertTrue(self.shape.isInside(cq.Vector(-75.05, 20.0, z), 1e-6))
            self.assertTrue(self.shape.isInside(cq.Vector(-75.05, -20.0, z), 1e-6))

    def test_pocket_preserves_u_shaped_loop_recess(self) -> None:
        import cadquery as cq

        for z in (10.1, 27.9):
            self.assertTrue(self.shape.isInside(cq.Vector(99.0, 12.0, z), 1e-6))
            self.assertFalse(self.shape.isInside(cq.Vector(99.0, 0.0, z), 1e-6))
            self.assertTrue(self.shape.isInside(cq.Vector(107.0, 0.0, z), 1e-6))


class OxoCocktailStrainerGeometryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.rotation_degrees = 24.7
        cls.raw_cutter = _build_face_down_pocket_cutter(**POCKET_PARAMETERS)
        cls.positioned_cutter, cls.plan_x, cls.plan_y = _position_plan_cutter(
            cls.raw_cutter,
            rotation_degrees=cls.rotation_degrees,
            inner_x_min=-103.75,
            inner_x_max=103.75,
            inner_y_min=-61.75,
            inner_y_max=61.75,
        )
        cls.cradle = build()
        cls.shape = cls.cradle.val()

    @classmethod
    def positioned_point(cls, x: float, y: float, z: float):
        import cadquery as cq

        angle = math.radians(cls.rotation_degrees)
        return cq.Vector(
            x * math.cos(angle) - y * math.sin(angle) + cls.plan_x,
            x * math.sin(angle) + y * math.cos(angle) + cls.plan_y,
            z,
        )

    def test_diagonal_pocket_fits_three_by_five_footprint(self) -> None:
        bounding_box = self.positioned_cutter.val().BoundingBox()

        self.assertAlmostEqual(bounding_box.xlen, 198.935, places=3)
        self.assertAlmostEqual(bounding_box.ylen, 122.842, places=3)
        self.assertGreaterEqual(bounding_box.xmin, -103.75)
        self.assertLessEqual(bounding_box.xmax, 103.75)
        self.assertGreaterEqual(bounding_box.ymin, -61.75)
        self.assertLessEqual(bounding_box.ymax, 61.75)

    def test_holder_remains_entirely_within_four_unit_height(self) -> None:
        bounding_box = self.shape.BoundingBox()

        self.assertAlmostEqual(bounding_box.xlen, 209.5, places=3)
        self.assertAlmostEqual(bounding_box.ylen, 125.5, places=3)
        self.assertAlmostEqual(bounding_box.zlen, 31.8, places=3)
        self.assertEqual(len(self.cradle.solids().vals()), 1)

    def test_eighteen_mm_rim_pocket_preserves_safe_floor(self) -> None:
        below_floor = self.positioned_point(51.0, 0.0, 9.5)
        inside_pocket = self.positioned_point(51.0, 0.0, 10.5)
        near_deck = self.positioned_point(51.0, 0.0, 27.5)

        self.assertTrue(self.shape.isInside(below_floor, 1e-6))
        self.assertFalse(self.shape.isInside(inside_pocket, 1e-6))
        self.assertFalse(self.shape.isInside(near_deck, 1e-6))

    def test_thick_handle_recess_is_open_for_the_full_depth(self) -> None:
        for z in (10.5, 27.5):
            self.assertFalse(self.shape.isInside(self.positioned_point(-75.0, 0.0, z), 1e-6))

    def test_paired_finger_scoops_are_open_for_the_full_depth(self) -> None:
        for z in (10.5, 27.5):
            self.assertFalse(self.shape.isInside(self.positioned_point(-75.05, 20.0, z), 1e-6))
            self.assertFalse(self.shape.isInside(self.positioned_point(-75.05, -20.0, z), 1e-6))

    def test_rail_recesses_are_open_for_the_full_depth(self) -> None:
        for z in (10.5, 27.5):
            self.assertFalse(self.shape.isInside(self.positioned_point(-20.0, 7.1, z), 1e-6))
            self.assertTrue(self.shape.isInside(self.positioned_point(-20.0, 0.0, z), 1e-6))

    def test_rejects_unrotated_or_two_unit_deep_footprints(self) -> None:
        with self.assertRaisesRegex(ValueError, "does not fit"):
            build(strainer_rotation_degrees=0.0)
        with self.assertRaisesRegex(ValueError, "does not fit"):
            build(unit_depth=2)

    def test_rejects_pocket_that_cannot_preserve_the_cavity_floor(self) -> None:
        with self.assertRaisesRegex(ValueError, "preserving a 2 mm cavity floor"):
            build(pocket_depth_mm=20.0)


if __name__ == "__main__":
    unittest.main()
