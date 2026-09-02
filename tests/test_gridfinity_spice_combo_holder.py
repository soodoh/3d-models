"""Geometry and spacing tests for the Gridfinity spice combo holder."""

from __future__ import annotations

import unittest

import cadquery as cq

from print_models.catalog import load_models
from print_models.models.gridfinity_spice_combo_holder import (
    GRIDFINITY_PITCH_MM,
    PARAMETERS,
    STACKING_LIP_ENABLED,
    TOP_EDGE_CHAMFER_MM,
    _resolve_pocket_layout,
    build,
)


class GridfinitySpiceComboHolderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.holder = build()
        cls.shape = cls.holder.val()
        cls.bounds = cls.shape.BoundingBox()
        cls.jar_pocket_width_mm = PARAMETERS["jar_width_mm"] + 2.0 * PARAMETERS["fit_clearance_mm"]
        cls.jar_pocket_depth_mm = PARAMETERS["jar_depth_mm"] + 2.0 * PARAMETERS["fit_clearance_mm"]
        cls.large_radius_mm = (
            PARAMETERS["large_item_diameter_mm"] / 2.0 + PARAMETERS["fit_clearance_mm"]
        )
        cls.small_radius_mm = (
            PARAMETERS["small_item_diameter_mm"] / 2.0 + PARAMETERS["fit_clearance_mm"]
        )
        cls.layout = _resolve_pocket_layout(
            unit_width=PARAMETERS["unit_width"],
            unit_depth=PARAMETERS["unit_depth"],
            inner_width_mm=cls.bounds.xlen - 2.0 * PARAMETERS["wall_thickness_mm"],
            inner_depth_mm=cls.bounds.ylen - 2.0 * PARAMETERS["wall_thickness_mm"],
            jar_pocket_width_mm=cls.jar_pocket_width_mm,
            jar_pocket_depth_mm=cls.jar_pocket_depth_mm,
            large_pocket_radius_mm=cls.large_radius_mm,
            small_pocket_radius_mm=cls.small_radius_mm,
        )

    def test_catalog_exposes_requested_defaults(self) -> None:
        model = load_models()["gridfinity_spice_combo_holder"]

        self.assertEqual(model.PARAMETERS["unit_width"], 3)
        self.assertEqual(model.PARAMETERS["unit_depth"], 4)
        self.assertEqual(model.PARAMETERS["unit_height"], 4)
        self.assertEqual(model.PARAMETERS["large_item_diameter_mm"], 91.3)
        self.assertEqual(model.PARAMETERS["small_item_diameter_mm"], 57.7)
        self.assertEqual(model.PARAMETERS["pocket_depth_mm"], 19.0)
        self.assertEqual(model.PARAMETERS["fit_clearance_mm"], 0.75)
        self.assertFalse(STACKING_LIP_ENABLED)

    def test_holder_is_one_printable_three_by_four_module(self) -> None:
        self.assertEqual(self.holder.solids().size(), 1)
        self.assertAlmostEqual(self.bounds.xlen, 3.0 * GRIDFINITY_PITCH_MM - 0.5, places=3)
        self.assertAlmostEqual(self.bounds.ylen, 4.0 * GRIDFINITY_PITCH_MM - 0.5, places=3)
        self.assertAlmostEqual(self.bounds.zlen, 28.0, places=3)

    def test_flat_deck_replaces_stacking_lip(self) -> None:
        top_faces = [
            face
            for face in self.shape.Faces()
            if abs(face.BoundingBox().zmin - self.bounds.zmax) < 1e-6
            and abs(face.BoundingBox().zmax - self.bounds.zmax) < 1e-6
        ]
        deck_face = max(top_faces, key=lambda face: face.Area())
        deck_bounds = deck_face.BoundingBox()

        self.assertAlmostEqual(self.bounds.zmax, 4.0 * 7.0, places=3)
        self.assertAlmostEqual(
            deck_bounds.xlen,
            self.bounds.xlen - 2.0 * TOP_EDGE_CHAMFER_MM,
            places=3,
        )
        self.assertAlmostEqual(
            deck_bounds.ylen,
            self.bounds.ylen - 2.0 * TOP_EDGE_CHAMFER_MM,
            places=3,
        )

    def test_spice_socket_continues_adjacent_holder_pitch(self) -> None:
        self.assertEqual(self.layout.jar_center_mm, (-31.5, -42.0))
        left_holder_right_jar_x_mm = -PARAMETERS["unit_width"] * GRIDFINITY_PITCH_MM + 31.5
        self.assertAlmostEqual(
            self.layout.jar_center_mm[0] - left_holder_right_jar_x_mm,
            63.0,
        )

    def test_round_pockets_are_auto_packed_in_remaining_space(self) -> None:
        self.assertAlmostEqual(self.layout.large_center_mm[0], 0.0)
        self.assertAlmostEqual(self.layout.large_center_mm[1], 34.35)
        self.assertAlmostEqual(self.layout.small_center_mm[0], 28.75)
        self.assertAlmostEqual(self.layout.small_center_mm[1], -42.0)

    def test_all_pockets_have_clearance_and_nineteen_mm_depth(self) -> None:
        pocket_checks = (
            (self.layout.large_center_mm, self.large_radius_mm),
            (self.layout.small_center_mm, self.small_radius_mm),
        )
        for (center_x_mm, center_y_mm), radius_mm in pocket_checks:
            self.assertFalse(self.shape.isInside(cq.Vector(center_x_mm, center_y_mm, 27.9), 1e-6))
            self.assertFalse(self.shape.isInside(cq.Vector(center_x_mm, center_y_mm, 9.1), 1e-6))
            self.assertTrue(self.shape.isInside(cq.Vector(center_x_mm, center_y_mm, 8.9), 1e-6))
            self.assertFalse(
                self.shape.isInside(
                    cq.Vector(center_x_mm + radius_mm - 0.1, center_y_mm, 27.9),
                    1e-6,
                )
            )
            self.assertTrue(
                self.shape.isInside(
                    cq.Vector(center_x_mm + radius_mm + 0.1, center_y_mm, 27.9),
                    1e-6,
                )
            )

        jar_x_mm, jar_y_mm = self.layout.jar_center_mm
        self.assertFalse(self.shape.isInside(cq.Vector(jar_x_mm, jar_y_mm, 27.9), 1e-6))
        self.assertFalse(self.shape.isInside(cq.Vector(jar_x_mm, jar_y_mm, 9.1), 1e-6))
        self.assertTrue(self.shape.isInside(cq.Vector(jar_x_mm, jar_y_mm, 8.9), 1e-6))

    def test_layout_preserves_printable_webs(self) -> None:
        jar_right_mm = self.layout.jar_center_mm[0] + self.jar_pocket_width_mm / 2.0
        jar_top_mm = self.layout.jar_center_mm[1] + self.jar_pocket_depth_mm / 2.0
        jar_to_small_web_mm = self.layout.small_center_mm[0] - self.small_radius_mm - jar_right_mm
        jar_to_large_web_mm = self.layout.large_center_mm[1] - self.large_radius_mm - jar_top_mm

        self.assertAlmostEqual(jar_to_small_web_mm, 3.4)
        self.assertAlmostEqual(jar_to_large_web_mm, 2.7)

    def test_rejects_geometry_that_breaks_fit_policy(self) -> None:
        with self.assertRaisesRegex(ValueError, "3x4 Gridfinity footprint"):
            build(unit_depth=3)
        with self.assertRaisesRegex(ValueError, "preserving a 2 mm cavity floor"):
            build(unit_height=2)
        with self.assertRaisesRegex(ValueError, "outer deck ring"):
            build(large_item_diameter_mm=120.0)
        with self.assertRaisesRegex(ValueError, "deck web between openings"):
            build(jar_depth_mm=55.0)
        with self.assertRaisesRegex(ValueError, "less than half"):
            build(jar_corner_radius_mm=26.5)
        with self.assertRaisesRegex(ValueError, "must not be negative"):
            build(fit_clearance_mm=-0.1)


if __name__ == "__main__":
    unittest.main()
