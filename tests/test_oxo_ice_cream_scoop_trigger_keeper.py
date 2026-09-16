"""Geometry-policy tests for the OXO scoop peg-lock clip."""

from __future__ import annotations

import math
import unittest

import cadquery as cq

from print_models.catalog import load_models
from print_models.models import oxo_ice_cream_scoop_trigger_keeper as keeper


class OxoIceCreamScoopTriggerKeeperTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.default_clip = keeper.build()

    def test_model_is_registered(self) -> None:
        self.assertIn(keeper.NAME, load_models())

    def test_builds_one_valid_single_solid_clip(self) -> None:
        self.assertEqual(len(self.default_clip.solids().vals()), 1)
        self.assertTrue(self.default_clip.val().isValid())

    def test_default_envelope_uses_the_former_small_span_and_taller_legs(self) -> None:
        bounds = self.default_clip.val().BoundingBox()
        expected_size = (42.4, 22.2, 3.62)
        for actual, expected in zip(
            (bounds.xlen, bounds.ylen, bounds.zlen), expected_size, strict=True
        ):
            self.assertAlmostEqual(actual, expected, places=5)

    def test_peg_matches_slot_clearance_rotation_and_projection(self) -> None:
        peg_region = (
            cq.Workplane("XY")
            .box(10.0, keeper.DEFAULT_PEG_LENGTH_MM, 10.0)
            .translate(
                (
                    -keeper.DEFAULT_BODY_THICKNESS_MM / 2.0,
                    -keeper.DEFAULT_PEG_DROP_MM - keeper.DEFAULT_PEG_LENGTH_MM / 2.0,
                    keeper.DEFAULT_BODY_WIDTH_MM / 2.0,
                )
            )
        )
        peg = self.default_clip.intersect(peg_region).val().BoundingBox()

        projected_width, projected_height = keeper._capsule_projected_size(
            major_mm=keeper.DEFAULT_PEG_MAJOR_MM,
            minor_mm=keeper.DEFAULT_PEG_MINOR_MM,
            angle_degrees=keeper.DEFAULT_PEG_ANGLE_DEGREES,
        )
        self.assertEqual(keeper.DEFAULT_PEG_ANGLE_DEGREES, 45.0)
        self.assertAlmostEqual(peg.xlen, projected_width, places=5)
        self.assertAlmostEqual(peg.ylen, keeper.DEFAULT_PEG_LENGTH_MM, places=5)
        self.assertAlmostEqual(peg.zlen, projected_height, places=5)
        self.assertLessEqual(projected_width, keeper.DEFAULT_BODY_THICKNESS_MM)
        self.assertLessEqual(projected_height, keeper.DEFAULT_BODY_WIDTH_MM)
        self.assertLess(keeper.DEFAULT_BODY_WIDTH_MM - projected_height, 0.01)
        self.assertLess(keeper.DEFAULT_PEG_MAJOR_MM, 4.6)
        self.assertLess(keeper.DEFAULT_PEG_MINOR_MM, 2.6)

    def test_exports_broadside_down_with_a_stable_printing_face(self) -> None:
        bounds = self.default_clip.val().BoundingBox()
        bottom_area = sum(face.Area() for face in self.default_clip.faces("<Z").vals())
        self.assertAlmostEqual(bounds.zmin, 0.0, places=5)
        self.assertGreater(bottom_area, 250.0)

    def test_enlarged_trigger_lip_meets_terminal_leg_without_a_gap(self) -> None:
        junction_point = cq.Vector(
            keeper.DEFAULT_HANDLE_SPAN_MM - 0.01,
            -keeper.DEFAULT_TRIGGER_LEG_DROP_MM + 0.2,
            keeper.DEFAULT_BODY_WIDTH_MM / 2.0,
        )
        self.assertTrue(self.default_clip.val().isInside(junction_point))

    def test_parameters_resize_the_clip(self) -> None:
        clip = keeper.build(
            handle_span_mm=40.0,
            peg_drop_mm=12.0,
            trigger_leg_drop_mm=16.0,
            body_thickness_mm=4.0,
            body_width_mm=7.0,
            peg_length_mm=4.0,
            peg_major_mm=4.0,
            peg_minor_mm=2.0,
            trigger_lip_mm=1.2,
        )
        bounds = clip.val().BoundingBox()
        self.assertAlmostEqual(bounds.xlen, 48.0, places=5)
        self.assertAlmostEqual(bounds.ylen, 20.0, places=5)
        self.assertAlmostEqual(bounds.zlen, 7.0, places=5)

    def test_rejects_geometry_breaking_parameters(self) -> None:
        invalid_parameters = (
            {"handle_span_mm": 0.0},
            {"handle_span_mm": math.nan},
            {"peg_drop_mm": 0.0},
            {"trigger_leg_drop_mm": 2.5},
            {"body_thickness_mm": 1.19},
            {"body_thickness_mm": 3.0},
            {"body_width_mm": 1.99},
            {"body_width_mm": 2.8},
            {"peg_length_mm": 0.0},
            {"peg_major_mm": 2.0, "peg_minor_mm": 2.0},
            {"peg_minor_mm": 0.0},
            {"peg_angle_degrees": math.inf},
            {"trigger_lip_mm": 0.0},
            {"trigger_lip_mm": 4.2},
        )
        for parameters in invalid_parameters:
            with self.subTest(parameters=parameters), self.assertRaises(ValueError):
                keeper.build(**parameters)


if __name__ == "__main__":
    unittest.main()
