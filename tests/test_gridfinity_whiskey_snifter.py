"""Tests for the side-laid Gridfinity whiskey-snifter cradle."""

from __future__ import annotations

import unittest

from print_models.models.gridfinity_whiskey_snifter import (
    _build_snifter_cutter,
    _scaled_snifter_profile_groups,
    build,
)


class SnifterProfileTests(unittest.TestCase):
    def setUp(self) -> None:
        self.parameters = {
            "base_diameter_mm": 46.0,
            "waist_diameter_mm": 32.0,
            "widest_diameter_mm": 67.0,
            "top_diameter_mm": 47.0,
        }
        self.groups = _scaled_snifter_profile_groups(
            glass_length_mm=115.0,
            **self.parameters,
        )
        self.feature_points = (self.groups[0][0][0],) + tuple(
            group[-1][-1] for group in self.groups
        )

    def test_profile_matches_verified_dimensions(self) -> None:
        _, bottom_radius = self.feature_points[0]
        base_x, base_radius = self.feature_points[1]
        waist_x, waist_radius = self.feature_points[2]
        widest_x, widest_radius = self.feature_points[3]
        top_x, top_radius = self.feature_points[4]

        self.assertAlmostEqual(bottom_radius, 23.0)
        self.assertAlmostEqual(base_x + 57.5, 4.0)
        self.assertAlmostEqual(base_radius, 23.0)
        self.assertAlmostEqual(waist_x + 57.5, 20.0)
        self.assertAlmostEqual(waist_radius, 16.0)
        self.assertAlmostEqual(widest_x + 57.5, 52.3919, places=4)
        self.assertAlmostEqual(widest_radius, 33.5)
        self.assertAlmostEqual(top_x + 57.5, 115.0)
        self.assertAlmostEqual(top_radius, 23.5)

    def test_profile_has_horizontal_tangents_at_scaled_extrema(self) -> None:
        for previous_group, next_group in zip(self.groups, self.groups[1:], strict=False):
            previous_segment = previous_group[-1]
            next_segment = next_group[0]
            feature_radius = previous_segment[-1][1]

            self.assertAlmostEqual(previous_segment[-2][1], feature_radius)
            self.assertAlmostEqual(next_segment[1][1], feature_radius)

    def test_bezier_cutter_preserves_exact_scaled_extrema(self) -> None:
        cutter = _build_snifter_cutter(
            axis_z=44.5,
            glass_length_mm=115.0,
            fit_clearance_mm=1.0,
            **self.parameters,
        )
        bounding_box = cutter.val().BoundingBox()

        self.assertAlmostEqual(bounding_box.xlen, 117.0, places=3)
        self.assertAlmostEqual(bounding_box.ylen, 69.0, places=2)
        self.assertAlmostEqual(bounding_box.zlen, 69.0, places=2)


class WhiskeySnifterGeometryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.cradle = build()
        cls.shape = cls.cradle.val()
        profile_groups = _scaled_snifter_profile_groups(
            glass_length_mm=115.0,
            base_diameter_mm=46.0,
            waist_diameter_mm=32.0,
            widest_diameter_mm=67.0,
            top_diameter_mm=47.0,
        )
        cls.waist_section_x = profile_groups[1][-1][-1][0]
        cls.widest_section_x = profile_groups[2][-1][-1][0]

    def test_cradle_preserves_three_by_two_four_unit_envelope(self) -> None:
        bounding_box = self.shape.BoundingBox()

        self.assertAlmostEqual(bounding_box.xlen, 125.5, places=3)
        self.assertAlmostEqual(bounding_box.ylen, 83.5, places=3)
        self.assertAlmostEqual(bounding_box.zlen, 31.8, places=3)
        self.assertEqual(len(self.cradle.solids().vals()), 1)

    def test_cutout_keeps_material_below_its_floor(self) -> None:
        import cadquery as cq

        self.assertTrue(self.shape.isInside(cq.Vector(self.widest_section_x, 0.0, 9.5), 1e-6))
        self.assertFalse(self.shape.isInside(cq.Vector(self.widest_section_x, 0.0, 10.5), 1e-6))

    def test_cutout_follows_the_horizontal_snifter_profile(self) -> None:
        import cadquery as cq

        deck_z = 27.9
        self.assertFalse(self.shape.isInside(cq.Vector(self.widest_section_x, 30.0, deck_z), 1e-6))
        self.assertTrue(self.shape.isInside(cq.Vector(self.widest_section_x, 32.0, deck_z), 1e-6))
        self.assertFalse(self.shape.isInside(cq.Vector(self.waist_section_x, 0.0, deck_z), 1e-6))
        self.assertTrue(self.shape.isInside(cq.Vector(self.waist_section_x, 6.0, deck_z), 1e-6))

    def test_compact_cutout_keeps_material_at_both_ends(self) -> None:
        import cadquery as cq

        self.assertFalse(self.shape.isInside(cq.Vector(-58.0, 0.0, 27.9), 1e-6))
        self.assertTrue(self.shape.isInside(cq.Vector(-60.0, 0.0, 27.9), 1e-6))
        self.assertFalse(self.shape.isInside(cq.Vector(58.0, 0.0, 27.9), 1e-6))
        self.assertTrue(self.shape.isInside(cq.Vector(60.0, 0.0, 27.9), 1e-6))

    def test_rejects_a_pocket_that_leaves_an_unsafe_floor(self) -> None:
        with self.assertRaisesRegex(ValueError, "preserving a 2 mm cavity floor"):
            build(pocket_depth_mm=20.0)

    def test_rejects_an_inaccessible_shallow_profile(self) -> None:
        with self.assertRaisesRegex(ValueError, "too shallow"):
            build(pocket_depth_mm=16.0)


if __name__ == "__main__":
    unittest.main()
