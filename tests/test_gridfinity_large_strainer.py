"""Tests for the 4x3x4U dual-strainer Gridfinity holder."""

from __future__ import annotations

import unittest

import cadquery as cq

from print_models.catalog import load_models
from print_models.models.gridfinity_large_strainer import (
    PARAMETERS,
    _build_strainer_cavity,
    _calculate_cutout_centers,
    _radius_at_height,
    build,
)


class LargeStrainerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.holder = build()
        cls.shape = cls.holder.val()
        cls.medium_scale = 79.3 / 95.5
        cls.large_radius = 85.53846153846153 / 2.0
        cls.medium_radius = 71.76335078534032 / 2.0
        large_center, medium_center = _calculate_cutout_centers(
            inner_x_min=-82.75,
            inner_x_max=82.75,
            inner_y_min=-61.75,
            inner_y_max=61.75,
            large_radius_mm=cls.large_radius,
            medium_radius_mm=cls.medium_radius,
            support_ring_width_mm=4.0,
        )
        cls.large_center = cq.Vector(*large_center)
        cls.medium_center = cq.Vector(*medium_center)

    def test_catalog_exposes_four_by_three_defaults(self) -> None:
        models = load_models()

        self.assertIn("gridfinity_large_strainer", models)
        self.assertEqual(PARAMETERS["unit_width"], 4)
        self.assertEqual(PARAMETERS["unit_depth"], 3)
        self.assertEqual(PARAMETERS["unit_height"], 4)
        self.assertEqual(PARAMETERS["pocket_depth_mm"], 18.0)
        self.assertEqual(PARAMETERS["large_top_lip_diameter_mm"], 95.5)
        self.assertEqual(PARAMETERS["large_bottom_diameter_mm"], 68.0)
        self.assertEqual(PARAMETERS["medium_top_lip_diameter_mm"], 79.3)

    def test_default_holder_has_four_by_three_four_u_envelope(self) -> None:
        bounding_box = self.shape.BoundingBox()

        self.assertAlmostEqual(bounding_box.xlen, 167.5, places=3)
        self.assertAlmostEqual(bounding_box.ylen, 125.5, places=3)
        self.assertAlmostEqual(bounding_box.zlen, 31.8, places=3)
        self.assertEqual(len(self.holder.solids().vals()), 1)

    def test_large_profile_preserves_previous_measured_dimensions(self) -> None:
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

    def test_large_cavity_matches_previous_eighteen_mm_cutout(self) -> None:
        cavity = self._build_large_cavity()
        bounding_box = cavity.val().BoundingBox()

        self.assertAlmostEqual(bounding_box.xlen, 85.53846153846153, places=6)
        self.assertAlmostEqual(bounding_box.ylen, 85.53846153846153, places=6)
        self.assertAlmostEqual(bounding_box.zmin, 10.0, places=6)
        self.assertAlmostEqual(bounding_box.zmax, 28.2, places=6)
        self.assertAlmostEqual(cavity.val().Volume(), 98140.72700096162, places=3)

    def test_medium_cavity_scales_every_strainer_dimension(self) -> None:
        scale = self.medium_scale
        profile_parameters = {
            "top_lip_diameter_mm": 95.5 * scale,
            "under_lip_diameter_mm": 87.0 * scale,
            "bottom_curve_diameter_mm": 82.0 * scale,
            "flat_bottom_diameter_mm": 68.0 * scale,
            "strainer_height_mm": 48.2 * scale,
            "curve_height": 6.2 * scale,
            "under_lip_height": 45.2 * scale,
        }

        self.assertAlmostEqual(68.0 * scale, 56.46492146596859, places=6)
        self.assertAlmostEqual(
            _radius_at_height(6.2 * scale, **profile_parameters), 41.0 * scale, places=6
        )

        cavity = self._build_medium_cavity()
        bounding_box = cavity.val().BoundingBox()
        self.assertAlmostEqual(bounding_box.xlen, 71.76335078534032, places=6)
        self.assertAlmostEqual(bounding_box.ylen, 71.76335078534032, places=6)
        self.assertAlmostEqual(bounding_box.zmin, 10.0, places=6)
        self.assertAlmostEqual(bounding_box.zmax, 28.2, places=6)

    def test_contoured_cavities_are_staggered_across_the_holder(self) -> None:
        self.assertLess(self.large_center.x, self.medium_center.x)
        self.assertLess(self.large_center.y, self.medium_center.y)

        for center in (self.large_center, self.medium_center):
            self.assertFalse(self.shape.isInside(center + cq.Vector(0.0, 0.0, 20.0), 1e-6))

        self.assertTrue(self.shape.isInside(cq.Vector(0.0, -50.0, 20.0), 1e-6))

    def test_blind_cavities_leave_a_floor_at_eighteen_mm_depth(self) -> None:
        for center in (self.large_center, self.medium_center):
            self.assertTrue(self.shape.isInside(center + cq.Vector(0.0, 0.0, 9.8), 1e-6))
            self.assertFalse(self.shape.isInside(center + cq.Vector(0.0, 0.0, 10.1), 1e-6))

    def test_center_layout_preserves_edge_and_inter_cavity_material(self) -> None:
        self.assertAlmostEqual(self.large_center.x, -35.98076923076923, places=6)
        self.assertAlmostEqual(self.large_center.y, -14.980769230769234, places=6)
        self.assertAlmostEqual(self.medium_center.x, 42.86832460732984, places=6)
        self.assertAlmostEqual(self.medium_center.y, 21.86832460732984, places=6)

        center_distance = self.large_center.sub(self.medium_center).Length
        cavity_gap = center_distance - self.large_radius - self.medium_radius
        self.assertGreaterEqual(cavity_gap, 8.0)
        self.assertAlmostEqual(cavity_gap, 8.383772649354434, places=6)

    def test_rejects_footprint_narrower_than_four_units(self) -> None:
        with self.assertRaisesRegex(ValueError, "at least a 4x3x4U"):
            build(unit_width=3)

    def test_rejects_footprint_shorter_than_three_units(self) -> None:
        with self.assertRaisesRegex(ValueError, "at least a 4x3x4U"):
            build(unit_depth=2)

    def test_rejects_height_shorter_than_four_units(self) -> None:
        with self.assertRaisesRegex(ValueError, "at least a 4x3x4U"):
            build(unit_height=3)

    def test_rejects_cavities_that_do_not_fit(self) -> None:
        with self.assertRaisesRegex(ValueError, "do not fit"):
            build(support_ring_width_mm=30.0)

    def test_rejects_medium_larger_than_large(self) -> None:
        with self.assertRaisesRegex(ValueError, "must be smaller"):
            build(medium_top_lip_diameter_mm=95.5)

    @staticmethod
    def _build_large_cavity():
        return _build_strainer_cavity(
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
        )

    @classmethod
    def _build_medium_cavity(cls):
        scale = cls.medium_scale
        return _build_strainer_cavity(
            item_bottom_z=10.0,
            pocket_depth_mm=18.0,
            top_lip_diameter_mm=95.5 * scale,
            under_lip_diameter_mm=87.0 * scale,
            bottom_curve_diameter_mm=82.0 * scale,
            flat_bottom_diameter_mm=68.0 * scale,
            strainer_height_mm=48.2 * scale,
            bottom_curve_start_from_top_mm=42.0 * scale,
            lip_thickness_mm=3.0 * scale,
            fit_clearance_mm=1.0,
        )


if __name__ == "__main__":
    unittest.main()
