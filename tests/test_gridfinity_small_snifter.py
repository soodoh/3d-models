"""Tests for the side-laid Gridfinity small-snifter cradle."""

from __future__ import annotations

import unittest

from print_models.catalog import load_models
from print_models.models.gridfinity_small_snifter import (
    PARAMETERS,
    _build_small_snifter_cutter,
    _monotone_profile_tangents,
    _small_snifter_profile_points,
    build,
)


class SmallSnifterProfileTests(unittest.TestCase):
    def setUp(self) -> None:
        self.parameters = {
            "glass_length_mm": 85.0,
            "base_diameter_mm": 38.0,
            "base_height_mm": 11.0,
            "neck_diameter_mm": 30.0,
            "neck_height_mm": 25.0,
            "widest_diameter_mm": 49.0,
            "widest_height_from_top_mm": 26.0,
            "top_diameter_mm": 43.0,
        }
        self.profile_points = _small_snifter_profile_points(**self.parameters)
        self.profile_tangents = _monotone_profile_tangents(self.profile_points)

    def test_catalog_exposes_requested_small_snifter_dimensions(self) -> None:
        models = load_models()

        self.assertIn("gridfinity_small_snifter", models)
        self.assertEqual(PARAMETERS["glass_length_mm"], 85.0)
        self.assertEqual(PARAMETERS["base_diameter_mm"], 38.0)
        self.assertEqual(PARAMETERS["base_height_mm"], 11.0)
        self.assertEqual(PARAMETERS["neck_diameter_mm"], 30.0)
        self.assertEqual(PARAMETERS["neck_height_mm"], 25.0)
        self.assertEqual(PARAMETERS["widest_diameter_mm"], 49.0)
        self.assertEqual(PARAMETERS["widest_height_from_top_mm"], 26.0)
        self.assertEqual(PARAMETERS["top_diameter_mm"], 43.0)

    def test_profile_matches_measured_extrema_and_photo_informed_heights(self) -> None:
        bottom = self.profile_points[0]
        base_widest = self.profile_points[2]
        neck_start = self.profile_points[6]
        neck_end = self.profile_points[7]
        bowl_widest = self.profile_points[12]
        top = self.profile_points[-1]

        self.assertEqual(bottom, (-42.5, 18.0))
        self.assertEqual(base_widest, (-38.5, 19.0))
        self.assertEqual(neck_start, (-24.5, 15.0))
        self.assertEqual(neck_end, (-17.5, 15.0))
        self.assertEqual(bowl_widest, (16.5, 24.5))
        self.assertEqual(top, (42.5, 21.5))

    def test_base_rounds_outward_then_smoothly_narrows_to_the_neck(self) -> None:
        profile_diameters = tuple(radius * 2.0 for _, radius in self.profile_points[:8])

        self.assertEqual(
            profile_diameters,
            (36.0, 37.6, 38.0, 37.2, 35.0, 31.0, 30.0, 30.0),
        )
        self.assertEqual(self.profile_tangents[0], (1.0, 0.0))

    def test_profile_tangents_flatten_smoothly_at_measured_extrema(self) -> None:
        for point_index in (0, 2, 6, 7, 12):
            self.assertEqual(self.profile_tangents[point_index], (1.0, 0.0))

        for (_, start_radius), (_, end_radius), (_, tangent_slope) in zip(
            self.profile_points,
            self.profile_points[1:],
            self.profile_tangents,
            strict=False,
        ):
            radius_change = end_radius - start_radius
            self.assertGreaterEqual(radius_change * tangent_slope, 0.0)

    def test_top_taper_continues_to_the_rim_without_a_flare(self) -> None:
        previous_tangent = self.profile_tangents[-2][1]
        rim_tangent = self.profile_tangents[-1][1]

        self.assertLess(rim_tangent, 0.0)
        self.assertAlmostEqual(previous_tangent, -1.0 / 6.0)
        self.assertAlmostEqual(rim_tangent, previous_tangent)

    def test_single_smooth_profile_does_not_overshoot_anchor_diameters(self) -> None:
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
        sample_parameters = tuple(index / 1000 for index in range(1001))
        sampled_radii = tuple(point.z for point in profile_edge.positions(sample_parameters))

        self.assertAlmostEqual(min(sampled_radii), 15.0, places=6)
        self.assertAlmostEqual(max(sampled_radii), 24.5, places=5)

    def test_cutter_preserves_length_and_maximum_diameter_with_clearance(self) -> None:
        cutter = _build_small_snifter_cutter(
            axis_z=36.0,
            fit_clearance_mm=1.0,
            **self.parameters,
        )
        bounding_box = cutter.val().BoundingBox()

        self.assertAlmostEqual(bounding_box.xlen, 87.0, places=3)
        self.assertAlmostEqual(bounding_box.ylen, 51.0, places=3)
        self.assertAlmostEqual(bounding_box.zlen, 51.0, places=3)


class SmallSnifterGeometryTests(unittest.TestCase):
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

        self.assertTrue(self.shape.isInside(cq.Vector(16.5, 0.0, 9.5), 1e-6))
        self.assertFalse(self.shape.isInside(cq.Vector(16.5, 0.0, 10.5), 1e-6))

    def test_cutout_follows_widest_and_neck_sections(self) -> None:
        import cadquery as cq

        deck_z = 27.9
        self.assertFalse(self.shape.isInside(cq.Vector(16.5, 24.0, deck_z), 1e-6))
        self.assertTrue(self.shape.isInside(cq.Vector(16.5, 26.0, deck_z), 1e-6))
        self.assertFalse(self.shape.isInside(cq.Vector(-20.0, 14.0, deck_z), 1e-6))
        self.assertTrue(self.shape.isInside(cq.Vector(-20.0, 16.0, deck_z), 1e-6))

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
            build(pocket_depth_mm=9.0)

    def test_rejects_a_widest_section_below_the_neck(self) -> None:
        with self.assertRaisesRegex(ValueError, "above neck_height_mm"):
            build(widest_height_from_top_mm=62.0)


if __name__ == "__main__":
    unittest.main()
