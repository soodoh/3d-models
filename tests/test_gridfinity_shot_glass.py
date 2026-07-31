"""Tests for the upright Gridfinity shot-glass holder."""

from __future__ import annotations

import unittest

from print_models.catalog import load_models
from print_models.models.gridfinity_shot_glass import (
    PARAMETERS,
    _build_shot_glass_cutter,
    _shot_glass_radius_at_height,
    build,
)


class ShotGlassProfileTests(unittest.TestCase):
    def setUp(self) -> None:
        self.parameters = {
            "glass_height_mm": 60.0,
            "bottom_diameter_mm": 38.0,
            "top_diameter_mm": 50.0,
        }

    def test_catalog_exposes_requested_shot_glass_dimensions(self) -> None:
        models = load_models()

        self.assertIn("gridfinity_shot_glass", models)
        self.assertEqual(PARAMETERS["glass_height_mm"], 60.0)
        self.assertEqual(PARAMETERS["bottom_diameter_mm"], 38.0)
        self.assertEqual(PARAMETERS["top_diameter_mm"], 50.0)
        self.assertEqual(PARAMETERS["pocket_depth_mm"], 18.0)
        self.assertEqual(PARAMETERS["fit_clearance_mm"], 1.0)

    def test_profile_is_a_straight_taper_between_measured_diameters(self) -> None:
        self.assertAlmostEqual(_shot_glass_radius_at_height(0.0, **self.parameters), 19.0)
        self.assertAlmostEqual(_shot_glass_radius_at_height(18.0, **self.parameters), 20.8)
        self.assertAlmostEqual(_shot_glass_radius_at_height(30.0, **self.parameters), 22.0)
        self.assertAlmostEqual(_shot_glass_radius_at_height(60.0, **self.parameters), 25.0)

    def test_cutter_applies_clearance_radially_without_adding_height(self) -> None:
        cutter = _build_shot_glass_cutter(
            glass_bottom_z=10.0,
            fit_clearance_mm=1.0,
            **self.parameters,
        )
        bounding_box = cutter.val().BoundingBox()

        self.assertAlmostEqual(bounding_box.xlen, 52.0, places=3)
        self.assertAlmostEqual(bounding_box.ylen, 52.0, places=3)
        self.assertAlmostEqual(bounding_box.zmin, 10.0, places=3)
        self.assertAlmostEqual(bounding_box.zlen, 60.0, places=3)


class ShotGlassGeometryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.holder = build()
        cls.shape = cls.holder.val()

    def test_holder_preserves_two_by_two_four_unit_envelope(self) -> None:
        bounding_box = self.shape.BoundingBox()

        self.assertAlmostEqual(bounding_box.xlen, 83.5, places=3)
        self.assertAlmostEqual(bounding_box.ylen, 83.5, places=3)
        self.assertAlmostEqual(bounding_box.zlen, 31.8, places=3)
        self.assertEqual(len(self.holder.solids().vals()), 1)

    def test_centered_socket_has_an_exact_eighteen_mm_floor(self) -> None:
        import cadquery as cq

        self.assertTrue(self.shape.isInside(cq.Vector(0.0, 0.0, 9.5), 1e-6))
        self.assertFalse(self.shape.isInside(cq.Vector(0.0, 0.0, 10.5), 1e-6))

    def test_socket_opening_matches_the_taper_and_radial_clearance(self) -> None:
        import cadquery as cq

        deck_z = 27.9
        self.assertFalse(self.shape.isInside(cq.Vector(21.5, 0.0, deck_z), 1e-6))
        self.assertTrue(self.shape.isInside(cq.Vector(22.5, 0.0, deck_z), 1e-6))

    def test_rejects_a_pocket_that_leaves_an_unsafe_floor(self) -> None:
        with self.assertRaisesRegex(ValueError, "preserving a 2 mm cavity floor"):
            build(pocket_depth_mm=20.0)

    def test_rejects_a_footprint_without_a_safe_deck_ring(self) -> None:
        with self.assertRaisesRegex(ValueError, "does not leave a 2 mm deck ring"):
            build(unit_width=1)

    def test_rejects_a_non_tapered_profile(self) -> None:
        with self.assertRaisesRegex(
            ValueError, "top_diameter_mm must be greater than bottom_diameter_mm"
        ):
            build(top_diameter_mm=38.0)

    def test_rejects_a_pocket_deeper_than_the_glass(self) -> None:
        with self.assertRaisesRegex(ValueError, "must not exceed glass_height_mm"):
            build(pocket_depth_mm=61.0, unit_height=10)


if __name__ == "__main__":
    unittest.main()
