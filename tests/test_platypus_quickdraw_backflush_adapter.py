"""Tests for the Platypus QuickDraw clean-side backflush adapter."""

from __future__ import annotations

import math
import unittest

from print_models.catalog import load_models
from print_models.models.platypus_quickdraw_backflush_adapter import PARAMETERS, build


class PlatypusQuickDrawBackflushAdapterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.parts = build()
        cls.body = cls.parts["body"].val()
        cls.gasket = cls.parts["bottle_gasket"].val()

    def test_catalog_exposes_adapter_and_nominal_interfaces(self) -> None:
        models = load_models()

        self.assertIn("platypus_quickdraw_backflush_adapter", models)
        self.assertEqual(PARAMETERS["bottle_thread_major_diameter_mm"], 27.6)
        self.assertEqual(PARAMETERS["bottle_thread_pitch_mm"], 3.2)
        self.assertEqual(PARAMETERS["filter_thread_major_diameter_mm"], 33.4)
        self.assertEqual(PARAMETERS["filter_thread_pitch_mm"], 1.5)

    def test_build_returns_rigid_body_and_flexible_gasket(self) -> None:
        self.assertEqual(set(self.parts), {"body", "bottle_gasket"})
        self.assertEqual(len(self.parts["body"].solids().vals()), 1)
        self.assertEqual(len(self.parts["bottle_gasket"].solids().vals()), 1)

    def test_adapter_preserves_reference_envelope(self) -> None:
        bounding_box = self.body.BoundingBox()

        self.assertAlmostEqual(bounding_box.xlen, 38.0, places=3)
        self.assertAlmostEqual(bounding_box.ylen, 38.0, places=3)
        self.assertAlmostEqual(bounding_box.zlen, 26.0, places=3)

    def test_sockets_are_connected_by_a_ten_mm_flow_bore(self) -> None:
        import cadquery as cq

        self.assertFalse(self.body.isInside(cq.Vector(0.0, 0.0, 13.0), 1e-6))
        self.assertFalse(self.body.isInside(cq.Vector(4.9, 0.0, 13.0), 1e-6))
        self.assertTrue(self.body.isInside(cq.Vector(5.1, 0.0, 13.0), 1e-6))

    def test_internal_shoulder_supports_the_bottle_gasket(self) -> None:
        import cadquery as cq

        self.assertTrue(self.body.isInside(cq.Vector(8.0, 0.0, 13.0), 1e-6))
        self.assertFalse(self.body.isInside(cq.Vector(12.0, 0.0, 6.0), 1e-6))
        self.assertFalse(self.body.isInside(cq.Vector(16.0, 0.0, 23.0), 1e-6))

    def test_gasket_fits_bottle_socket_without_restricting_flow(self) -> None:
        bounding_box = self.gasket.BoundingBox()

        self.assertAlmostEqual(bounding_box.xlen, 24.8, places=3)
        self.assertAlmostEqual(bounding_box.ylen, 24.8, places=3)
        self.assertAlmostEqual(bounding_box.zlen, 1.0, places=3)
        expected_volume = math.pi * (12.4**2 - 5.1**2)
        self.assertAlmostEqual(self.gasket.Volume(), expected_volume, places=3)

    def test_rejects_filter_thread_that_leaves_a_thin_wall(self) -> None:
        with self.assertRaisesRegex(ValueError, "at least a 1.5 mm body wall"):
            build(filter_fit_adjustment_mm=2.0)

    def test_rejects_overlapping_thread_sockets(self) -> None:
        with self.assertRaisesRegex(ValueError, "at least a 1 mm sealing shoulder"):
            build(bottle_thread_length_mm=14.0)

    def test_rejects_gasket_that_cannot_enter_bottle_socket(self) -> None:
        with self.assertRaisesRegex(ValueError, "fit through the bottle-thread opening"):
            build(gasket_outer_diameter_mm=26.0)

    def test_rejects_non_finite_fit_adjustment(self) -> None:
        with self.assertRaisesRegex(ValueError, "finite and positive"):
            build(filter_fit_adjustment_mm=math.inf)


if __name__ == "__main__":
    unittest.main()
