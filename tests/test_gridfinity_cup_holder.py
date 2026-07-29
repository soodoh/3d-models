"""Tests for the smooth fitted Gridfinity cup holder."""

from __future__ import annotations

import unittest

from print_models.models.gridfinity_cup_holder import _cup_radius_at_height, build


class CupProfileTests(unittest.TestCase):
    def test_profile_matches_measured_base_and_widest_radii(self) -> None:
        parameters = {
            "widest_diameter_mm": 70.0,
            "flat_base_diameter_mm": 40.0,
            "rounded_base_height_mm": 35.0,
        }

        self.assertAlmostEqual(_cup_radius_at_height(0.0, **parameters), 20.0)
        self.assertAlmostEqual(_cup_radius_at_height(35.0, **parameters), 35.0)
        self.assertAlmostEqual(_cup_radius_at_height(69.0, **parameters), 35.0)

    def test_profile_uses_scan_informed_rounded_transition(self) -> None:
        radius = _cup_radius_at_height(
            18.0,
            widest_diameter_mm=70.0,
            flat_base_diameter_mm=40.0,
            rounded_base_height_mm=35.0,
        )

        self.assertAlmostEqual(radius, 30.84, places=2)


class CupHolderGeometryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.holder = build()
        cls.shape = cls.holder.val()

    def test_holder_preserves_two_by_two_four_unit_envelope(self) -> None:
        bounding_box = self.shape.BoundingBox()

        self.assertAlmostEqual(bounding_box.xlen, 83.5, places=3)
        self.assertAlmostEqual(bounding_box.ylen, 83.5, places=3)
        self.assertAlmostEqual(bounding_box.zlen, 31.8, places=3)
        self.assertEqual(len(self.holder.solids().vals()), 1)

    def test_socket_keeps_material_below_its_clearance_floor(self) -> None:
        import cadquery as cq

        self.assertTrue(self.shape.isInside(cq.Vector(0.0, 0.0, 9.0), 1e-6))
        self.assertFalse(self.shape.isInside(cq.Vector(0.0, 0.0, 9.8), 1e-6))

    def test_socket_opening_matches_profile_and_clearance(self) -> None:
        import cadquery as cq

        self.assertFalse(self.shape.isInside(cq.Vector(31.0, 0.0, 27.9), 1e-6))
        self.assertTrue(self.shape.isInside(cq.Vector(32.5, 0.0, 27.9), 1e-6))

    def test_rejects_a_pocket_that_leaves_an_unsafe_floor(self) -> None:
        with self.assertRaisesRegex(ValueError, "preserving a 2 mm cavity floor"):
            build(pocket_depth_mm=21.0)


if __name__ == "__main__":
    unittest.main()
