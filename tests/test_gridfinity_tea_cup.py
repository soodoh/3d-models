"""Tests for the side-laid Gridfinity tea-cup cradle."""

from __future__ import annotations

import unittest

from print_models.catalog import load_models
from print_models.models._side_laid_profile import monotone_profile_tangents
from print_models.models.gridfinity_tea_cup import (
    PARAMETERS,
    _build_tea_cup_cutter,
    _tea_cup_profile_points,
    build,
)


class TeaCupProfileTests(unittest.TestCase):
    def setUp(self) -> None:
        self.parameters = {
            "cup_height_mm": 85.0,
            "bottom_diameter_mm": 40.0,
            "flare_start_height_mm": 58.0,
            "top_diameter_mm": 54.0,
        }
        self.profile_points = _tea_cup_profile_points(**self.parameters)
        self.profile_tangents = monotone_profile_tangents(self.profile_points)

    def test_catalog_exposes_requested_tea_cup_dimensions(self) -> None:
        models = load_models()

        self.assertIn("gridfinity_tea_cup", models)
        self.assertEqual(PARAMETERS["cup_height_mm"], 85.0)
        self.assertEqual(PARAMETERS["bottom_diameter_mm"], 40.0)
        self.assertEqual(PARAMETERS["top_diameter_mm"], 54.0)
        self.assertEqual(PARAMETERS["fit_clearance_mm"], 1.0)

    def test_profile_matches_measured_extrema_and_photo_informed_flare(self) -> None:
        bottom = self.profile_points[0]
        flare_start = self.profile_points[3]
        upper_flare = self.profile_points[-2]
        top = self.profile_points[-1]

        self.assertEqual(bottom, (-42.5, 20.0))
        self.assertEqual(flare_start, (15.5, 20.0))
        self.assertAlmostEqual(upper_flare[0], 39.8)
        self.assertAlmostEqual(upper_flare[1], 26.58)
        self.assertEqual(top, (42.5, 27.0))

    def test_lower_body_stays_cylindrical_before_flare(self) -> None:
        lower_diameters = tuple(radius * 2.0 for _, radius in self.profile_points[:4])

        self.assertEqual(lower_diameters, (40.0, 40.0, 40.0, 40.0))
        self.assertEqual(self.profile_tangents[3], (1.0, 0.0))

    def test_single_smooth_profile_does_not_overshoot_measured_diameters(self) -> None:
        import cadquery as cq

        profile_parameters = tuple(axial_position for axial_position, _ in self.profile_points)
        profile_edge = (
            cq.Workplane("XZ")
            .moveTo(*self.profile_points[0])
            .spline(
                self.profile_points[1:],
                tangents=self.profile_tangents,
                parameters=profile_parameters,
                scale=False,
                includeCurrent=True,
            )
            .val()
        )
        sampled_radii = tuple(
            point.z for point in profile_edge.positions(index / 1000 for index in range(1001))
        )

        self.assertAlmostEqual(min(sampled_radii), 20.0, places=6)
        self.assertAlmostEqual(max(sampled_radii), 27.0, places=6)

    def test_cutter_preserves_length_and_maximum_diameter_with_clearance(self) -> None:
        cutter = _build_tea_cup_cutter(
            axis_z=38.0,
            fit_clearance_mm=1.0,
            **self.parameters,
        )
        bounding_box = cutter.val().BoundingBox()

        self.assertAlmostEqual(bounding_box.xlen, 87.0, places=3)
        self.assertAlmostEqual(bounding_box.ylen, 56.0, places=3)
        self.assertAlmostEqual(bounding_box.zlen, 56.0, places=3)


class TeaCupGeometryTests(unittest.TestCase):
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

        self.assertTrue(self.shape.isInside(cq.Vector(41.0, 0.0, 9.5), 1e-6))
        self.assertFalse(self.shape.isInside(cq.Vector(41.0, 0.0, 10.5), 1e-6))

    def test_cutout_follows_cylindrical_body_and_flared_rim(self) -> None:
        import cadquery as cq

        deck_z = 27.9
        self.assertFalse(self.shape.isInside(cq.Vector(-30.0, 18.0, deck_z), 1e-6))
        self.assertTrue(self.shape.isInside(cq.Vector(-30.0, 19.0, deck_z), 1e-6))
        self.assertFalse(self.shape.isInside(cq.Vector(41.0, 25.0, deck_z), 1e-6))
        self.assertTrue(self.shape.isInside(cq.Vector(41.0, 27.0, deck_z), 1e-6))

    def test_compact_cutout_keeps_material_at_both_ends(self) -> None:
        import cadquery as cq

        deck_z = 27.9
        self.assertFalse(self.shape.isInside(cq.Vector(-43.0, 0.0, deck_z), 1e-6))
        self.assertTrue(self.shape.isInside(cq.Vector(-46.0, 0.0, deck_z), 1e-6))
        self.assertFalse(self.shape.isInside(cq.Vector(43.0, 0.0, deck_z), 1e-6))
        self.assertTrue(self.shape.isInside(cq.Vector(46.0, 0.0, deck_z), 1e-6))

    def test_rejects_a_pocket_that_leaves_an_unsafe_floor(self) -> None:
        with self.assertRaisesRegex(ValueError, "preserving a 2 mm cavity floor"):
            build(pocket_depth_mm=20.0)

    def test_rejects_an_inaccessible_shallow_profile(self) -> None:
        with self.assertRaisesRegex(ValueError, "too shallow"):
            build(pocket_depth_mm=7.0)

    def test_rejects_a_flare_start_above_the_rim(self) -> None:
        with self.assertRaisesRegex(ValueError, "smaller than cup_height_mm"):
            build(flare_start_height_mm=85.0)


if __name__ == "__main__":
    unittest.main()
