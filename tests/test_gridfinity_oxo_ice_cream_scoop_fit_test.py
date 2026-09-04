"""Tests for the solid split OXO Classic Swipe scoop fit gauge."""

from __future__ import annotations

import unittest

from print_models.catalog import load_models
from print_models.models.gridfinity_oxo_ice_cream_scoop_fit_test import (
    PARAMETERS,
    _measured_fitted_cutter,
    build,
)


class OxoIceCreamScoopFitTestGeometryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.parts = build()
        cls.shapes = {name: part.val() for name, part in cls.parts.items()}

    def test_catalog_exposes_matching_clearance_roll_and_center_split(self) -> None:
        models = load_models()

        self.assertIn("gridfinity_oxo_ice_cream_scoop_fit_test", models)
        self.assertEqual(PARAMETERS["fit_clearance_mm"], 1.0)
        self.assertEqual(PARAMETERS["roll_angle_degrees"], 47.0)
        self.assertEqual(PARAMETERS["cavity_bottom_z_mm"], 9.0)
        self.assertEqual(PARAMETERS["test_height_mm"], 42.0)
        self.assertEqual(PARAMETERS["test_width_mm"], 83.5)
        self.assertEqual(PARAMETERS["split_y_mm"], 0.0)

    def test_fitted_cutter_matches_full_holder_orientation(self) -> None:
        cutter = _measured_fitted_cutter(
            fit_clearance_mm=1.0,
            roll_angle_degrees=47.0,
            cavity_bottom_z_mm=9.0,
        )
        bounds = cutter.val().BoundingBox()

        self.assertAlmostEqual(bounds.xlen, 76.961, places=3)
        self.assertAlmostEqual(bounds.ylen, 226.4, places=3)
        self.assertAlmostEqual(bounds.zmin, 9.0, places=3)
        self.assertAlmostEqual(bounds.zmax, 70.395, places=3)

    def test_build_returns_two_valid_single_shell_halves(self) -> None:
        self.assertEqual(set(self.parts), {"solid_handle_half", "solid_bowl_half"})
        for name, shape in self.shapes.items():
            with self.subTest(name=name):
                self.assertTrue(shape.isValid())
                self.assertEqual(len(shape.Solids()), 1)
                self.assertEqual(len(shape.Shells()), 1)

    def test_halves_cover_full_measured_envelope(self) -> None:
        handle_bounds = self.shapes["solid_handle_half"].BoundingBox()
        bowl_bounds = self.shapes["solid_bowl_half"].BoundingBox()

        for bounds in (handle_bounds, bowl_bounds):
            self.assertAlmostEqual(bounds.xlen, 83.5, places=3)
            self.assertAlmostEqual(bounds.ylen, 113.2, places=3)
            self.assertAlmostEqual(bounds.zlen, 42.0, places=3)
        self.assertAlmostEqual(handle_bounds.ymin, -113.2, places=3)
        self.assertAlmostEqual(handle_bounds.ymax, 0.0, places=3)
        self.assertAlmostEqual(bowl_bounds.ymin, 0.0, places=3)
        self.assertAlmostEqual(bowl_bounds.ymax, 113.2, places=3)
        combined_volume = sum(shape.Volume() for shape in self.shapes.values())
        self.assertGreater(combined_volume, 680_000.0)
        self.assertLess(combined_volume, 690_000.0)

    def test_cavity_preserves_floor_and_outer_walls_in_both_halves(self) -> None:
        import cadquery as cq

        for part_name, sample_y, cavity_x in (
            ("solid_handle_half", -70.0, 10.0),
            ("solid_bowl_half", 80.0, 10.0),
        ):
            shape = self.shapes[part_name]
            with self.subTest(part_name=part_name):
                self.assertTrue(shape.isInside(cq.Vector(cavity_x, sample_y, 8.5), 1e-6))
                self.assertFalse(shape.isInside(cq.Vector(cavity_x, sample_y, 35.0), 1e-6))
                self.assertTrue(shape.isInside(cq.Vector(40.0, sample_y, 30.0), 1e-6))

    def test_invalid_gauge_parameters_are_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "cannot be negative"):
            build(fit_clearance_mm=-0.1)
        with self.assertRaisesRegex(ValueError, "must be positive"):
            build(cavity_bottom_z_mm=0.0)
        with self.assertRaisesRegex(ValueError, "inside the test"):
            build(split_y_mm=120.0)


if __name__ == "__main__":
    unittest.main()
