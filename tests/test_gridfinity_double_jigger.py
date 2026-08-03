"""Tests for the side-laid Gridfinity double-jigger cradle."""

from __future__ import annotations

import unittest

from print_models.catalog import load_models
from print_models.models._side_laid_profile import monotone_profile_tangents
from print_models.models.gridfinity_double_jigger import (
    PARAMETERS,
    _build_double_jigger_cutter,
    _double_jigger_profile_points,
    build,
)


class DoubleJiggerProfileTests(unittest.TestCase):
    def setUp(self) -> None:
        self.parameters = {
            "jigger_length_mm": 77.6,
            "one_ounce_rim_diameter_mm": 47.0,
            "one_ounce_cup_height_mm": 18.3,
            "one_ounce_grip_diameter_mm": 33.8,
            "waist_diameter_mm": 23.8,
            "waist_position_mm": 36.0,
            "one_and_half_ounce_grip_diameter_mm": 39.8,
            "one_and_half_ounce_cup_height_mm": 21.4,
            "one_and_half_ounce_rim_diameter_mm": 57.8,
        }
        self.profile_points = _double_jigger_profile_points(**self.parameters)

    def test_catalog_exposes_measured_jigger_dimensions(self) -> None:
        models = load_models()

        self.assertIn("gridfinity_double_jigger", models)
        self.assertEqual(PARAMETERS["jigger_length_mm"], 77.6)
        self.assertEqual(PARAMETERS["one_ounce_rim_diameter_mm"], 47.0)
        self.assertEqual(PARAMETERS["waist_diameter_mm"], 23.8)
        self.assertEqual(PARAMETERS["one_and_half_ounce_rim_diameter_mm"], 57.8)

    def test_profile_matches_measured_and_photo_traced_features(self) -> None:
        one_ounce_rim = self.profile_points[0]
        one_ounce_grip = self.profile_points[2]
        waist = self.profile_points[6]
        one_and_half_ounce_grip = self.profile_points[10]
        one_and_half_ounce_rim = self.profile_points[-1]

        self.assertEqual(one_ounce_rim, (-38.8, 23.5))
        self.assertAlmostEqual(one_ounce_grip[0], -20.5)
        self.assertEqual(one_ounce_grip[1], 16.9)
        self.assertAlmostEqual(waist[0], -2.8)
        self.assertEqual(waist[1], 11.9)
        self.assertAlmostEqual(one_and_half_ounce_grip[0], 17.4)
        self.assertEqual(one_and_half_ounce_grip[1], 19.9)
        self.assertEqual(one_and_half_ounce_rim, (38.8, 28.9))

    def test_grip_narrows_then_widens_monotonically(self) -> None:
        upper_grip_radii = tuple(radius for _, radius in self.profile_points[2:7])
        lower_grip_radii = tuple(radius for _, radius in self.profile_points[6:11])

        self.assertEqual(upper_grip_radii, tuple(sorted(upper_grip_radii, reverse=True)))
        self.assertEqual(lower_grip_radii, tuple(sorted(lower_grip_radii)))

    def test_smooth_profile_preserves_measured_extrema(self) -> None:
        import cadquery as cq

        tangents = monotone_profile_tangents(self.profile_points)
        parameters = tuple(position for position, _ in self.profile_points)
        edge = (
            cq.Workplane("XZ")
            .moveTo(*self.profile_points[0])
            .spline(
                self.profile_points[1:],
                tangents=tangents,
                parameters=parameters,
                scale=False,
                includeCurrent=True,
            )
            .val()
        )
        sampled_radii = tuple(
            point.z for point in edge.positions(index / 1000 for index in range(1001))
        )

        self.assertAlmostEqual(min(sampled_radii), 11.9, places=4)
        self.assertAlmostEqual(max(sampled_radii), 28.9, places=4)

    def test_cutter_preserves_length_and_maximum_diameter_with_clearance(self) -> None:
        cutter = _build_double_jigger_cutter(
            axis_z=40.0,
            fit_clearance_mm=1.0,
            **self.parameters,
        )
        bounding_box = cutter.val().BoundingBox()

        self.assertAlmostEqual(bounding_box.xlen, 79.6, places=3)
        self.assertAlmostEqual(bounding_box.ylen, 59.8, places=3)
        self.assertAlmostEqual(bounding_box.zlen, 59.8, places=3)


class DoubleJiggerGeometryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.cradle = build()
        cls.shape = cls.cradle.val()

    def test_cradle_preserves_three_by_two_four_unit_envelope(self) -> None:
        bounding_box = self.shape.BoundingBox()

        self.assertAlmostEqual(bounding_box.xlen, 125.5, places=3)
        self.assertAlmostEqual(bounding_box.ylen, 83.5, places=3)
        self.assertAlmostEqual(bounding_box.zlen, 31.8, places=3)
        self.assertEqual(len(self.cradle.solids().vals()), 1)

    def test_cutout_keeps_material_below_its_floor(self) -> None:
        import cadquery as cq

        self.assertTrue(self.shape.isInside(cq.Vector(38.8, 0.0, 9.5), 1e-6))
        self.assertFalse(self.shape.isInside(cq.Vector(38.8, 0.0, 10.5), 1e-6))

    def test_cutout_follows_both_rims_and_the_waist(self) -> None:
        import cadquery as cq

        deck_z = 27.9
        self.assertFalse(self.shape.isInside(cq.Vector(-38.8, 20.0, deck_z), 1e-6))
        self.assertTrue(self.shape.isInside(cq.Vector(-38.8, 22.0, deck_z), 1e-6))
        self.assertFalse(self.shape.isInside(cq.Vector(-2.8, 4.0, deck_z), 1e-6))
        self.assertTrue(self.shape.isInside(cq.Vector(-2.8, 6.0, deck_z), 1e-6))
        self.assertFalse(self.shape.isInside(cq.Vector(38.8, 27.0, deck_z), 1e-6))
        self.assertTrue(self.shape.isInside(cq.Vector(38.8, 28.0, deck_z), 1e-6))

    def test_cutout_keeps_material_at_both_ends(self) -> None:
        import cadquery as cq

        deck_z = 27.9
        self.assertTrue(self.shape.isInside(cq.Vector(-42.0, 0.0, deck_z), 1e-6))
        self.assertTrue(self.shape.isInside(cq.Vector(42.0, 0.0, deck_z), 1e-6))

    def test_rejects_compact_footprint_without_safe_end_ring(self) -> None:
        with self.assertRaisesRegex(ValueError, "deck ring"):
            build(unit_width=2)

    def test_rejects_a_pocket_that_leaves_an_unsafe_floor(self) -> None:
        with self.assertRaisesRegex(ValueError, "preserving a 2 mm cavity floor"):
            build(pocket_depth_mm=20.0)

    def test_rejects_an_inaccessible_shallow_profile(self) -> None:
        with self.assertRaisesRegex(ValueError, "too shallow"):
            build(pocket_depth_mm=10.0)

    def test_rejects_a_waist_outside_the_grip(self) -> None:
        with self.assertRaisesRegex(ValueError, "between the two cup-to-grip transitions"):
            build(waist_position_mm=60.0)


if __name__ == "__main__":
    unittest.main()
