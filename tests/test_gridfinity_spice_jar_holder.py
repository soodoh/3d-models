"""Geometry and modular-spacing tests for the Gridfinity spice-jar holder."""

from __future__ import annotations

import unittest

import cadquery as cq

from print_models.catalog import load_models
from print_models.models.gridfinity_spice_jar_holder import (
    GRIDFINITY_PITCH_MM,
    PARAMETERS,
    STACKING_LIP_ENABLED,
    TOP_EDGE_CHAMFER_MM,
    _jar_center_x_positions_mm,
    build,
)


class GridfinitySpiceJarHolderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.holder = build()
        cls.shape = cls.holder.val()
        cls.bounds = cls.shape.BoundingBox()

    def test_catalog_exposes_requested_defaults(self) -> None:
        model = load_models()["gridfinity_spice_jar_holder"]

        self.assertEqual(model.PARAMETERS["unit_width"], 3)
        self.assertEqual(model.PARAMETERS["unit_depth"], 2)
        self.assertEqual(model.PARAMETERS["unit_height"], 4)
        self.assertEqual(model.PARAMETERS["jar_width_mm"], 53.0)
        self.assertEqual(model.PARAMETERS["jar_depth_mm"], 53.0)
        self.assertEqual(model.PARAMETERS["jar_corner_radius_mm"], 12.0)
        self.assertEqual(model.PARAMETERS["pocket_depth_mm"], 19.0)
        self.assertEqual(model.PARAMETERS["fit_clearance_mm"], 0.75)
        self.assertFalse(STACKING_LIP_ENABLED)

    def test_holder_is_one_printable_three_by_two_module(self) -> None:
        self.assertEqual(self.holder.solids().size(), 1)
        self.assertAlmostEqual(self.bounds.xlen, 3.0 * GRIDFINITY_PITCH_MM - 0.5, places=3)
        self.assertAlmostEqual(self.bounds.ylen, 2.0 * GRIDFINITY_PITCH_MM - 0.5, places=3)
        self.assertAlmostEqual(self.bounds.zlen, 28.0, places=3)

    def test_flat_deck_replaces_raised_bin_walls(self) -> None:
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

    def test_jar_centers_repeat_evenly_across_holder_seam(self) -> None:
        centers = _jar_center_x_positions_mm(unit_width=3, jar_count=2)
        holder_pitch_mm = PARAMETERS["unit_width"] * GRIDFINITY_PITCH_MM
        adjacent_first_center_mm = holder_pitch_mm + centers[0]

        self.assertEqual(centers, (-31.5, 31.5))
        self.assertAlmostEqual(centers[1] - centers[0], 63.0)
        self.assertAlmostEqual(adjacent_first_center_mm - centers[1], 63.0)
        self.assertAlmostEqual(centers[1] - centers[0] - PARAMETERS["jar_width_mm"], 10.0)

    def test_each_socket_has_clearance_and_a_nineteen_mm_depth(self) -> None:
        for center_x_mm in _jar_center_x_positions_mm(unit_width=3, jar_count=2):
            self.assertFalse(self.shape.isInside(cq.Vector(center_x_mm, 0.0, 27.9), 1e-6))
            self.assertFalse(self.shape.isInside(cq.Vector(center_x_mm, 0.0, 9.1), 1e-6))
            self.assertTrue(self.shape.isInside(cq.Vector(center_x_mm, 0.0, 8.9), 1e-6))

            cleared_half_width_mm = (
                PARAMETERS["jar_width_mm"] / 2.0 + PARAMETERS["fit_clearance_mm"]
            )
            self.assertFalse(
                self.shape.isInside(
                    cq.Vector(center_x_mm + cleared_half_width_mm - 0.1, 0.0, 27.9),
                    1e-6,
                )
            )
            self.assertTrue(
                self.shape.isInside(
                    cq.Vector(center_x_mm + cleared_half_width_mm + 0.1, 0.0, 27.9),
                    1e-6,
                )
            )

    def test_rounded_corner_profile_preserves_corner_material(self) -> None:
        center_x_mm = _jar_center_x_positions_mm(unit_width=3, jar_count=2)[0]
        self.assertTrue(self.shape.isInside(cq.Vector(center_x_mm + 27.0, 27.0, 27.9), 1e-6))
        self.assertFalse(self.shape.isInside(cq.Vector(center_x_mm + 20.0, 20.0, 27.9), 1e-6))

    def test_rejects_geometry_that_breaks_fit_policy(self) -> None:
        with self.assertRaisesRegex(ValueError, "3x2 Gridfinity footprint"):
            build(unit_width=4)
        with self.assertRaisesRegex(ValueError, "preserving a 2 mm cavity floor"):
            build(unit_height=2)
        with self.assertRaisesRegex(ValueError, "outer deck ring"):
            build(jar_depth_mm=80.0)
        with self.assertRaisesRegex(ValueError, "deck web between jars"):
            build(jar_width_mm=61.0)
        with self.assertRaisesRegex(ValueError, "less than half"):
            build(jar_corner_radius_mm=26.5)
        with self.assertRaisesRegex(ValueError, "must not be negative"):
            build(fit_clearance_mm=-0.1)


if __name__ == "__main__":
    unittest.main()
