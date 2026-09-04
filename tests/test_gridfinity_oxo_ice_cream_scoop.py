"""Tests for the measured OXO Classic Swipe ice cream scoop holder."""

from __future__ import annotations

import unittest

from print_models.catalog import load_models
from print_models.models.gridfinity_oxo_ice_cream_scoop import (
    PARAMETERS,
    _build_scoop_envelope,
    _orient_scoop_envelope,
    build,
)

_MEASURED_KEYS = (
    "overall_length_mm",
    "guard_face_from_handle_tip_mm",
    "bowl_near_edge_from_handle_tip_mm",
    "handle_width_mm",
    "handle_depth_mm",
    "guard_width_mm",
    "guard_depth_mm",
    "guard_upper_reach_mm",
    "bowl_diameter_mm",
    "bowl_depth_mm",
    "mechanism_span_mm",
    "mechanism_depth_mm",
)


def _default_scoop_envelope(*, clearance_mm: float = 1.0):
    return _build_scoop_envelope(
        **{parameter: PARAMETERS[parameter] for parameter in _MEASURED_KEYS},
        clearance_mm=clearance_mm,
    )


class OxoIceCreamScoopGeometryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.parts = build()
        cls.shapes = {name: part.val() for name, part in cls.parts.items()}

    def test_catalog_exposes_owner_measured_dimensions(self) -> None:
        models = load_models()

        self.assertIn("gridfinity_oxo_ice_cream_scoop", models)
        self.assertEqual(PARAMETERS["unit_width"], 2)
        self.assertEqual(PARAMETERS["unit_depth"], 6)
        self.assertEqual(PARAMETERS["unit_height"], 6)
        self.assertEqual(PARAMETERS["overall_length_mm"], 224.4)
        self.assertEqual(PARAMETERS["guard_face_from_handle_tip_mm"], 120.6)
        self.assertEqual(PARAMETERS["bowl_near_edge_from_handle_tip_mm"], 163.6)
        self.assertEqual(PARAMETERS["handle_width_mm"], 33.5)
        self.assertEqual(PARAMETERS["handle_depth_mm"], 25.7)
        self.assertEqual(PARAMETERS["guard_width_mm"], 54.4)
        self.assertEqual(PARAMETERS["guard_depth_mm"], 35.0)
        self.assertEqual(PARAMETERS["bowl_diameter_mm"], 58.2)
        self.assertEqual(PARAMETERS["bowl_depth_mm"], 36.0)
        self.assertEqual(PARAMETERS["mechanism_span_mm"], 85.8)
        self.assertEqual(PARAMETERS["mechanism_depth_mm"], 22.5)
        self.assertEqual(PARAMETERS["roll_angle_degrees"], 47.0)

    def test_nominal_envelope_matches_caliper_measurements(self) -> None:
        scoop = _default_scoop_envelope(clearance_mm=0.0)
        bounds = scoop.val().BoundingBox()

        self.assertEqual(len(scoop.solids().vals()), 1)
        self.assertTrue(scoop.val().isValid())
        self.assertAlmostEqual(bounds.xmin, -45.4, places=3)
        self.assertAlmostEqual(bounds.xmax, 40.4, places=3)
        self.assertAlmostEqual(bounds.ylen, 224.4, places=3)
        self.assertAlmostEqual(bounds.zmin, 0.0, places=3)
        self.assertAlmostEqual(bounds.zmax, 36.0, places=3)

    def test_clearance_envelope_adds_one_millimeter_per_outer_surface(self) -> None:
        bounds = _default_scoop_envelope().val().BoundingBox()

        self.assertAlmostEqual(bounds.xmin, -46.4, places=3)
        self.assertAlmostEqual(bounds.xmax, 41.4, places=3)
        self.assertAlmostEqual(bounds.ylen, 226.4, places=3)
        self.assertAlmostEqual(bounds.zmin, -1.0, places=3)
        self.assertAlmostEqual(bounds.zmax, 37.0, places=3)

    def test_default_roll_centers_cutter_and_fits_shortest_reported_drawer(self) -> None:
        cutter = _orient_scoop_envelope(
            scoop=_default_scoop_envelope(),
            roll_angle_degrees=PARAMETERS["roll_angle_degrees"],
            cavity_bottom_z=9.0,
        )
        bounds = cutter.val().BoundingBox()

        self.assertAlmostEqual(bounds.xmin, -bounds.xmax, places=3)
        self.assertLess(bounds.xlen, 77.5)
        self.assertAlmostEqual(bounds.ylen, 226.4, places=3)
        self.assertAlmostEqual(bounds.zmin, 9.0, places=3)
        self.assertLess(bounds.zmax, 71.0)

    def test_build_returns_two_valid_printable_2x3_halves(self) -> None:
        self.assertEqual(set(self.parts), {"scoop_holder_front", "scoop_holder_back"})
        for name, shape in self.shapes.items():
            with self.subTest(name=name):
                bounds = shape.BoundingBox()
                self.assertTrue(shape.isValid())
                self.assertEqual(len(shape.Solids()), 1)
                self.assertEqual(len(shape.Shells()), 1)
                self.assertAlmostEqual(bounds.xlen, 83.5, places=3)
                self.assertAlmostEqual(bounds.ylen, 125.75, places=3)
                self.assertAlmostEqual(bounds.zlen, 45.8, places=3)

    def test_cavity_crosses_both_halves_and_preserves_floor_and_deck(self) -> None:
        import cadquery as cq

        sample_locations = (
            ("scoop_holder_front", -70.0, 10.0),
            ("scoop_holder_back", 80.0, 10.0),
        )
        for part_name, sample_y, cavity_x in sample_locations:
            shape = self.shapes[part_name]
            with self.subTest(part_name=part_name):
                self.assertFalse(shape.isInside(cq.Vector(cavity_x, sample_y, 35.0), 1e-6))
                self.assertTrue(shape.isInside(cq.Vector(cavity_x, sample_y, 8.5), 1e-6))
                self.assertTrue(shape.isInside(cq.Vector(35.0, sample_y, 30.0), 1e-6))

    def test_trigger_guard_has_vertical_release_without_cutting_the_wall(self) -> None:
        import cadquery as cq

        for part_name, sample_y in (
            ("scoop_holder_front", -0.1),
            ("scoop_holder_back", 0.1),
        ):
            shape = self.shapes[part_name]
            with self.subTest(part_name=part_name):
                self.assertFalse(shape.isInside(cq.Vector(38.0, sample_y, 40.0), 1e-6))
                self.assertTrue(shape.isInside(cq.Vector(38.5, sample_y, 40.0), 1e-6))

    def test_invalid_fit_parameters_are_rejected(self) -> None:
        invalid_dimensions = {parameter: PARAMETERS[parameter] for parameter in _MEASURED_KEYS}
        invalid_dimensions["overall_length_mm"] = 220.0
        with self.assertRaisesRegex(ValueError, "bowl extends beyond"):
            _build_scoop_envelope(**invalid_dimensions, clearance_mm=1.0)
        with self.assertRaisesRegex(ValueError, "between 0 and 90"):
            _orient_scoop_envelope(
                scoop=_default_scoop_envelope(),
                roll_angle_degrees=0.0,
                cavity_bottom_z=9.0,
            )
        with self.assertRaisesRegex(ValueError, "preserve at least 2 mm"):
            build(cavity_depth_mm=34.0)


if __name__ == "__main__":
    unittest.main()
