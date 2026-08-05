"""Tests for the upright Gridfinity OXO angled-jigger holder."""

from __future__ import annotations

import math
import unittest

from print_models.catalog import load_models
from print_models.models.gridfinity_oxo_angled_jigger import (
    PARAMETERS,
    SCAN_PROFILE_SECTIONS,
    _build_angled_jigger_cutter,
    _opening_dimensions_at_height,
    build,
)


class OxoAngledJiggerProfileTests(unittest.TestCase):
    def test_catalog_exposes_the_measured_jigger(self) -> None:
        models = load_models()

        self.assertIn("gridfinity_oxo_angled_jigger", models)
        self.assertEqual(PARAMETERS["unit_height"], 4)
        self.assertEqual(PARAMETERS["pocket_depth_mm"], 18.0)
        self.assertEqual(PARAMETERS["estimated_bottom_width_mm"], 34.7)
        self.assertEqual(PARAMETERS["bottom_length_mm"], 37.3)
        self.assertEqual(PARAMETERS["top_width_mm"], 61.3)
        self.assertEqual(PARAMETERS["top_length_mm"], 74.0)
        self.assertEqual(PARAMETERS["jigger_height_mm"], 53.0)

    def test_clearance_expanded_cutter_preserves_top_envelope(self) -> None:
        cutter = _build_angled_jigger_cutter(
            cavity_bottom_z=12.0,
            jigger_height_mm=53.0,
            estimated_bottom_width_mm=34.7,
            bottom_length_mm=37.3,
            top_width_mm=61.3,
            top_length_mm=74.0,
            fit_clearance_mm=1.0,
        )
        bounding_box = cutter.val().BoundingBox()

        self.assertAlmostEqual(bounding_box.xlen, 63.3212, places=3)
        self.assertAlmostEqual(bounding_box.ylen, 76.0924, places=3)
        self.assertAlmostEqual(bounding_box.zlen, 53.0, places=3)
        self.assertEqual(len(cutter.solids().vals()), 1)

    def test_opening_matches_the_scan_derived_deck_profile(self) -> None:
        opening_width, opening_length = _opening_dimensions_at_height(
            height_mm=18.0,
            jigger_height_mm=53.0,
            estimated_bottom_width_mm=34.7,
            bottom_length_mm=37.3,
            top_width_mm=61.3,
            top_length_mm=74.0,
            fit_clearance_mm=1.0,
        )

        self.assertAlmostEqual(opening_width, 53.4466, places=3)
        self.assertAlmostEqual(opening_length, 46.0606, places=3)

    def test_length_axis_overtakes_width_above_the_nested_bulge(self) -> None:
        parameters = {
            "jigger_height_mm": 53.0,
            "estimated_bottom_width_mm": 34.7,
            "bottom_length_mm": 37.3,
            "top_width_mm": 61.3,
            "top_length_mm": 74.0,
            "fit_clearance_mm": 0.0,
        }
        deck_width, deck_length = _opening_dimensions_at_height(height_mm=18.0, **parameters)
        rim_width, rim_length = _opening_dimensions_at_height(height_mm=53.0, **parameters)

        self.assertGreater(deck_width, deck_length)
        self.assertGreater(rim_length, rim_width)
        self.assertAlmostEqual(deck_width, 51.48, places=2)
        self.assertAlmostEqual(deck_length, 44.06, places=2)
        self.assertAlmostEqual(rim_width, 61.3, places=2)
        self.assertAlmostEqual(rim_length, 74.0, places=2)

    def test_profile_stations_do_not_reverse_inward(self) -> None:
        previous_radii = None
        for _, profile in SCAN_PROFILE_SECTIONS:
            radii = tuple(math.hypot(x, y) for x, y in profile)
            if previous_radii is not None:
                for previous_radius, radius in zip(previous_radii, radii, strict=True):
                    self.assertGreaterEqual(radius + 0.002, previous_radius)
            previous_radii = radii


class OxoAngledJiggerGeometryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.cradle = build()
        cls.shape = cls.cradle.val()

    def test_cradle_preserves_two_by_two_four_unit_envelope(self) -> None:
        bounding_box = self.shape.BoundingBox()

        self.assertAlmostEqual(bounding_box.xlen, 83.5, places=3)
        self.assertAlmostEqual(bounding_box.ylen, 83.5, places=3)
        self.assertAlmostEqual(bounding_box.zlen, 31.8, places=3)
        self.assertEqual(len(self.cradle.solids().vals()), 1)

    def test_socket_keeps_material_below_its_floor(self) -> None:
        import cadquery as cq

        self.assertTrue(self.shape.isInside(cq.Vector(0.0, 0.0, 9.9), 1e-6))
        self.assertFalse(self.shape.isInside(cq.Vector(0.0, 0.0, 10.1), 1e-6))

    def test_socket_preserves_the_smoothed_offset_profile_at_the_deck(self) -> None:
        import cadquery as cq

        deck_z = 28.0
        self.assertFalse(self.shape.isInside(cq.Vector(-26.0, 0.0, deck_z), 1e-6))
        self.assertFalse(self.shape.isInside(cq.Vector(25.0, 0.0, deck_z), 1e-6))
        self.assertTrue(self.shape.isInside(cq.Vector(-28.0, 0.0, deck_z), 1e-6))
        self.assertTrue(self.shape.isInside(cq.Vector(26.0, 0.0, deck_z), 1e-6))
        self.assertFalse(self.shape.isInside(cq.Vector(0.0, -28.0, deck_z), 1e-6))
        self.assertFalse(self.shape.isInside(cq.Vector(0.0, 17.0, deck_z), 1e-6))
        self.assertTrue(self.shape.isInside(cq.Vector(0.0, 18.0, deck_z), 1e-6))

    def test_rejects_a_short_box_for_the_pocket(self) -> None:
        with self.assertRaisesRegex(ValueError, "preserving a 2 mm cavity floor"):
            build(unit_height=3)

    def test_rejects_a_footprint_that_cannot_fit_the_opening(self) -> None:
        with self.assertRaisesRegex(ValueError, "deck ring"):
            build(unit_width=1)

    def test_rejects_an_invalid_estimated_base_width(self) -> None:
        with self.assertRaisesRegex(ValueError, "top_width_mm"):
            build(estimated_bottom_width_mm=62.0)


if __name__ == "__main__":
    unittest.main()
