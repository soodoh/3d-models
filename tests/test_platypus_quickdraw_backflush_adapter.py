"""Tests for the Platypus QuickDraw clean-side backflush adapter."""

from __future__ import annotations

import math
import unittest

from print_models.catalog import load_models
from print_models.models.platypus_quickdraw_backflush_adapter import PARAMETERS, build


class PlatypusQuickDrawBackflushAdapterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.adapter = build()
        cls.shape = cls.adapter.val()

    def test_catalog_exposes_both_female_interfaces(self) -> None:
        models = load_models()

        self.assertIn("platypus_quickdraw_backflush_adapter", models)
        self.assertEqual(PARAMETERS["bottle_thread_major_diameter_mm"], 27.6)
        self.assertEqual(PARAMETERS["bottle_thread_pitch_mm"], 3.2)
        self.assertEqual(PARAMETERS["filter_thread_major_diameter_mm"], 33.4)
        self.assertEqual(PARAMETERS["filter_thread_pitch_mm"], 1.5)

    def test_build_returns_one_adapter_without_a_separate_gasket(self) -> None:
        self.assertEqual(len(self.adapter.solids().vals()), 1)

    def test_adapter_preserves_reference_envelope(self) -> None:
        bounding_box = self.shape.BoundingBox()

        self.assertAlmostEqual(bounding_box.xlen, 38.0, places=3)
        self.assertAlmostEqual(bounding_box.ylen, 38.0, places=3)
        self.assertAlmostEqual(bounding_box.zlen, 26.0, places=3)

    def test_bottle_end_remains_a_female_twenty_eight_mm_socket(self) -> None:
        import cadquery as cq

        self.assertFalse(self.shape.isInside(cq.Vector(12.0, 0.0, 6.0), 1e-6))
        self.assertTrue(self.shape.isInside(cq.Vector(14.5, 0.0, 6.0), 1e-6))

    def test_filter_end_is_restored_to_a_larger_female_socket(self) -> None:
        import cadquery as cq

        self.assertFalse(self.shape.isInside(cq.Vector(15.5, 0.0, 18.0), 1e-6))
        self.assertFalse(self.shape.isInside(cq.Vector(16.5, 0.0, 18.0), 1e-6))
        self.assertTrue(self.shape.isInside(cq.Vector(17.0, 0.0, 18.0), 1e-6))

    def test_full_width_taper_replaces_internal_divider(self) -> None:
        import cadquery as cq

        self.assertFalse(self.shape.isInside(cq.Vector(12.6, 0.0, 12.0), 1e-6))
        self.assertFalse(self.shape.isInside(cq.Vector(13.5, 0.0, 13.0), 1e-6))
        self.assertTrue(self.shape.isInside(cq.Vector(14.0, 0.0, 13.0), 1e-6))
        self.assertFalse(self.shape.isInside(cq.Vector(15.7, 0.0, 15.1), 1e-6))
        self.assertTrue(self.shape.isInside(cq.Vector(16.0, 0.0, 15.1), 1e-6))

    def test_center_is_open_at_every_stage(self) -> None:
        import cadquery as cq

        for height_mm in (1.0, 12.0, 13.0, 15.1, 20.0, 25.0):
            self.assertFalse(self.shape.isInside(cq.Vector(0.0, 0.0, height_mm), 1e-6))

    def test_rejects_filter_thread_that_leaves_a_thin_wall(self) -> None:
        with self.assertRaisesRegex(ValueError, "at least a 1.5 mm body wall"):
            build(filter_fit_adjustment_mm=2.0)

    def test_rejects_sockets_that_do_not_fit_inside_body(self) -> None:
        with self.assertRaisesRegex(ValueError, "must fit within body_height_mm"):
            build(bottle_thread_length_mm=16.0)

    def test_rejects_non_finite_fit_adjustment(self) -> None:
        with self.assertRaisesRegex(ValueError, "finite and positive"):
            build(filter_fit_adjustment_mm=math.inf)


if __name__ == "__main__":
    unittest.main()
