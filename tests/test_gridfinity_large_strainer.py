"""Tests for the 3x5x4U circular large-strainer Gridfinity holder."""

from __future__ import annotations

import unittest

import cadquery as cq

from print_models.catalog import load_models
from print_models.models.gridfinity_large_strainer import (
    PARAMETERS,
    _build_strainer_cavity,
    _radius_at_height,
    build,
)


class LargeStrainerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.holder = build()
        cls.shape = cls.holder.val()

    def test_catalog_exposes_three_by_five_defaults(self) -> None:
        models = load_models()

        self.assertIn("gridfinity_large_strainer", models)
        self.assertEqual(PARAMETERS["unit_width"], 3)
        self.assertEqual(PARAMETERS["unit_depth"], 5)
        self.assertEqual(PARAMETERS["unit_height"], 4)
        self.assertEqual(PARAMETERS["pocket_depth_mm"], 18.0)
        self.assertEqual(PARAMETERS["strainer_rotation_degrees"], 0.0)
        self.assertEqual(PARAMETERS["divider_position_u"], 2.6)

    def test_default_holder_has_three_by_five_four_u_envelope(self) -> None:
        bounding_box = self.shape.BoundingBox()

        self.assertAlmostEqual(bounding_box.xlen, 125.5, places=3)
        self.assertAlmostEqual(bounding_box.ylen, 209.5, places=3)
        self.assertAlmostEqual(bounding_box.zlen, 31.8, places=3)
        self.assertEqual(len(self.holder.solids().vals()), 1)

    def test_top_compartment_is_filled_and_bottom_compartment_is_open(self) -> None:
        self.assertFalse(self.shape.isInside(cq.Vector(0.0, -80.0, 8.0), 1e-6))
        self.assertFalse(self.shape.isInside(cq.Vector(0.0, -80.0, 20.0), 1e-6))
        self.assertTrue(self.shape.isInside(cq.Vector(50.0, 90.0, 8.0), 1e-6))
        self.assertTrue(self.shape.isInside(cq.Vector(50.0, 90.0, 20.0), 1e-6))

    def test_bottom_compartment_has_no_vertical_side_divider(self) -> None:
        for x_position in (-50.0, 0.0, 50.0):
            self.assertFalse(self.shape.isInside(cq.Vector(x_position, -80.0, 20.0), 1e-6))

    def test_horizontal_divider_spans_the_three_u_width_below_the_bowl(self) -> None:
        divider_center_y = PARAMETERS["divider_position_u"] * 42.0 - 103.75

        self.assertAlmostEqual(divider_center_y, 5.45, places=2)
        for x_position in (-50.0, 0.0, 50.0):
            self.assertTrue(
                self.shape.isInside(cq.Vector(x_position, divider_center_y, 20.0), 1e-6)
            )
        self.assertFalse(self.shape.isInside(cq.Vector(0.0, 0.0, 20.0), 1e-6))

    def test_profile_uses_measured_transition_and_lip_diameters(self) -> None:
        profile_parameters = {
            "top_lip_diameter_mm": 95.5,
            "under_lip_diameter_mm": 87.0,
            "bottom_curve_diameter_mm": 82.0,
            "flat_bottom_diameter_mm": 68.0,
            "strainer_height_mm": 48.2,
            "curve_height": 6.2,
            "under_lip_height": 45.2,
        }

        self.assertAlmostEqual(_radius_at_height(0.0, **profile_parameters), 34.0, places=6)
        self.assertAlmostEqual(_radius_at_height(6.2, **profile_parameters), 41.0, places=6)
        self.assertAlmostEqual(_radius_at_height(45.2, **profile_parameters), 43.5, places=6)
        self.assertAlmostEqual(_radius_at_height(48.2, **profile_parameters), 47.75, places=6)

    def test_socket_bottom_is_flush_with_the_eighteen_mm_cutout_floor(self) -> None:
        cavity = _build_strainer_cavity(
            item_bottom_z=10.0,
            pocket_depth_mm=18.0,
            top_lip_diameter_mm=95.5,
            under_lip_diameter_mm=87.0,
            bottom_curve_diameter_mm=82.0,
            flat_bottom_diameter_mm=68.0,
            strainer_height_mm=48.2,
            bottom_curve_start_from_top_mm=42.0,
            lip_thickness_mm=3.0,
            fit_clearance_mm=1.0,
            center_x=0.0,
        )
        bounding_box = cavity.val().BoundingBox()

        self.assertAlmostEqual(bounding_box.xlen, 85.5, delta=0.1)
        self.assertAlmostEqual(bounding_box.ylen, 85.5, delta=0.1)
        self.assertAlmostEqual(bounding_box.zmin, 10.0, places=3)
        self.assertAlmostEqual(bounding_box.zmax, 28.2, places=3)

    def test_bowl_socket_is_centered_in_the_upper_section(self) -> None:
        bowl_center = cq.Vector(0.0, 55.0, 0.0)

        self.assertTrue(self.shape.isInside(bowl_center + cq.Vector(0.0, 0.0, 9.8), 1e-6))
        self.assertFalse(self.shape.isInside(bowl_center + cq.Vector(0.0, 0.0, 10.1), 1e-6))

    def test_rejects_footprint_narrower_than_three_units(self) -> None:
        with self.assertRaisesRegex(ValueError, "at least a 3x5x4U"):
            build(unit_width=2)

    def test_rejects_footprint_shorter_than_five_units(self) -> None:
        with self.assertRaisesRegex(ValueError, "at least a 3x5x4U"):
            build(unit_depth=4)

    def test_rejects_height_shorter_than_four_units(self) -> None:
        with self.assertRaisesRegex(ValueError, "at least a 3x5x4U"):
            build(unit_height=3)


if __name__ == "__main__":
    unittest.main()
