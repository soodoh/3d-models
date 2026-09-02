"""Geometry and fit-policy tests for the parametric Gridfinity sloped tray."""

from __future__ import annotations

import math
import unittest

import cadquery as cq

from print_models.catalog import load_models
from print_models.models.gridfinity_sloped_tray import (
    BOOLEAN_OVERLAP_MM,
    FRONT_WALL_TOP_Z_MM,
    PARAMETERS,
    PERIMETER_WALL_THICKNESS_MM,
    _clearance_y_bounds_mm,
    _sloped_item_envelopes_mm,
    build,
)


class GridfinitySlopedTrayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tray = build()
        cls.bounds = cls.tray.val().BoundingBox()
        clearance_y_min, clearance_y_max = _clearance_y_bounds_mm(
            surface_depth_mm=PARAMETERS["surface_depth_mm"],
            item_length_mm=PARAMETERS["item_length_mm"],
            item_height_mm=PARAMETERS["item_height_mm"],
            fit_clearance_mm=PARAMETERS["fit_clearance_mm"],
            angle_degrees=PARAMETERS["angle_degrees"],
        )
        usable_rear_y_mm = cls.bounds.ymax - PERIMETER_WALL_THICKNESS_MM
        target_center_y_mm = (cls.bounds.ymin + usable_rear_y_mm) / 2.0
        cls.tray_offset_y_mm = target_center_y_mm - (clearance_y_min + clearance_y_max) / 2.0

    def test_catalog_exposes_enclosed_fifteen_degree_defaults(self) -> None:
        model = load_models()["gridfinity_sloped_tray"]

        self.assertEqual(model.PARAMETERS["unit_width"], 5)
        self.assertEqual(model.PARAMETERS["unit_depth"], 3)
        self.assertEqual(model.PARAMETERS["surface_depth_mm"], 114.0)
        self.assertEqual(model.PARAMETERS["angle_degrees"], 15.0)
        self.assertEqual(model.PARAMETERS["item_length_mm"], 112.0)
        self.assertEqual(model.PARAMETERS["item_width_mm"], 51.0)
        self.assertEqual(model.PARAMETERS["item_height_mm"], 51.0)
        self.assertEqual(model.PARAMETERS["max_drawer_height_mm"], 91.0)

    def test_clearance_envelope_fits_below_design_limit(self) -> None:
        vertical_mm, front_to_back_mm = _sloped_item_envelopes_mm(
            item_length_mm=PARAMETERS["item_length_mm"],
            item_height_mm=PARAMETERS["item_height_mm"],
            angle_degrees=PARAMETERS["angle_degrees"],
            fit_clearance_mm=PARAMETERS["fit_clearance_mm"],
        )
        overall_height_mm = PARAMETERS["support_front_z_mm"] + vertical_mm

        self.assertAlmostEqual(vertical_mm, 80.6994, places=3)
        self.assertAlmostEqual(front_to_back_mm, 123.8330, places=3)
        self.assertAlmostEqual(overall_height_mm, 88.6994, places=3)
        self.assertLess(overall_height_mm, PARAMETERS["max_drawer_height_mm"])

    def test_default_is_one_printable_five_by_three_module(self) -> None:
        self.assertEqual(self.tray.solids().size(), 1)
        self.assertAlmostEqual(self.bounds.xlen, 5.0 * 42.0 - 0.5, places=3)
        self.assertAlmostEqual(self.bounds.ylen, 3.0 * 42.0 - 0.5, places=3)
        self.assertAlmostEqual(self.bounds.zmax, 37.7619, places=3)

    def test_width_is_parametric(self) -> None:
        narrow_tray = build(unit_width=2)
        narrow_bounds = narrow_tray.val().BoundingBox()

        self.assertEqual(narrow_tray.solids().size(), 1)
        self.assertAlmostEqual(narrow_bounds.xlen, 2.0 * 42.0 - 0.5, places=3)
        self.assertAlmostEqual(narrow_bounds.ylen, self.bounds.ylen, places=3)
        self.assertAlmostEqual(narrow_bounds.zmax, self.bounds.zmax, places=3)

    def test_slope_underside_is_solid_across_tray_width(self) -> None:
        tray_width_mm = self.bounds.xlen - 2.0 * PERIMETER_WALL_THICKNESS_MM
        support_probe = (
            cq.Workplane("XY").box(tray_width_mm - 2.0, 0.4, 0.4).translate((0.0, 0.0, 10.0))
        )

        intersection_volume = self.tray.val().intersect(support_probe.val()).Volume()
        self.assertAlmostEqual(intersection_volume, support_probe.val().Volume(), places=3)

    def test_clearance_envelope_is_centered_between_front_and_back_limits(self) -> None:
        clearance_y_min, clearance_y_max = _clearance_y_bounds_mm(
            surface_depth_mm=PARAMETERS["surface_depth_mm"],
            item_length_mm=PARAMETERS["item_length_mm"],
            item_height_mm=PARAMETERS["item_height_mm"],
            fit_clearance_mm=PARAMETERS["fit_clearance_mm"],
            angle_degrees=PARAMETERS["angle_degrees"],
            tray_offset_y_mm=self.tray_offset_y_mm,
        )
        front_margin_mm = clearance_y_min - self.bounds.ymin
        rear_margin_mm = self.bounds.ymax - PERIMETER_WALL_THICKNESS_MM - clearance_y_max

        self.assertGreater(front_margin_mm, 0.0)
        self.assertAlmostEqual(front_margin_mm, rear_margin_mm, places=6)

    def test_left_right_and_back_walls_are_closed_above_the_base(self) -> None:
        back_probe = (
            cq.Workplane("XY")
            .box(self.bounds.xlen - 2.0, 0.4, 24.0)
            .translate((0.0, self.bounds.ymax - 0.2, 28.0))
        )
        left_probe = (
            cq.Workplane("XY")
            .box(0.4, self.bounds.ylen - 2.0, 16.0)
            .translate((self.bounds.xmin + 0.2, 0.0, 22.0))
        )
        right_probe = left_probe.translate((self.bounds.xlen - 0.4, 0.0, 0.0))

        self.assertGreater(self.tray.val().intersect(back_probe.val()).Volume(), 1500.0)
        self.assertGreater(self.tray.val().intersect(left_probe.val()).Volume(), 100.0)
        self.assertGreater(self.tray.val().intersect(right_probe.val()).Volume(), 100.0)

    def test_perimeter_walls_terminate_on_the_slope_plane(self) -> None:
        angle_radians = math.radians(PARAMETERS["angle_degrees"])
        translation_z_mm = (
            PARAMETERS["support_front_z_mm"]
            + PARAMETERS["surface_depth_mm"] * math.sin(angle_radians) / 2.0
        )

        def slope_z_mm(y_mm: float) -> float:
            return (y_mm - self.tray_offset_y_mm) * math.tan(angle_radians) + translation_z_mm

        low_side_y_mm = self.bounds.ymin + 15.0
        wall_locations = (
            (self.bounds.xmin + 0.2, low_side_y_mm),
            (self.bounds.xmax - 0.2, low_side_y_mm),
            (self.bounds.xmin + 0.2, 0.0),
            (self.bounds.xmax - 0.2, 0.0),
            (0.0, self.bounds.ymax - PERIMETER_WALL_THICKNESS_MM + 0.2),
            (0.0, self.bounds.ymax - 0.2),
        )
        for x_mm, y_mm in wall_locations:
            slope_z = slope_z_mm(y_mm)
            below_probe = (
                cq.Workplane("XY").box(0.2, 0.2, 0.2).translate((x_mm, y_mm, slope_z - 0.1))
            )
            above_probe = below_probe.translate((0.0, 0.0, 0.3))

            self.assertGreater(self.tray.val().intersect(below_probe.val()).Volume(), 0.001)
            self.assertAlmostEqual(
                self.tray.val().intersect(above_probe.val()).Volume(), 0.0, places=6
            )

    def test_front_stop_is_full_width_and_matches_four_u_height(self) -> None:
        probe_y_mm = self.bounds.ymin + 4.2
        below_top_probe = (
            cq.Workplane("XY")
            .box(self.bounds.xlen - 2.0, 0.4, 0.2)
            .translate((0.0, probe_y_mm, FRONT_WALL_TOP_Z_MM - 0.1))
        )
        above_top_probe = below_top_probe.translate((0.0, 0.0, 0.3))

        self.assertGreater(self.tray.val().intersect(below_top_probe.val()).Volume(), 15.0)
        self.assertAlmostEqual(
            self.tray.val().intersect(above_top_probe.val()).Volume(), 0.0, places=6
        )

    def test_four_nominal_square_jars_fit_in_one_row(self) -> None:
        angle_degrees = PARAMETERS["angle_degrees"]
        angle_radians = math.radians(angle_degrees)
        surface_depth_mm = PARAMETERS["surface_depth_mm"]
        translation_z_mm = (
            PARAMETERS["support_front_z_mm"] + surface_depth_mm * math.sin(angle_radians) / 2.0
        )
        jar_front_y_mm = -surface_depth_mm / 2.0 + BOOLEAN_OVERLAP_MM
        jar_center_y_mm = jar_front_y_mm + PARAMETERS["item_length_mm"] / 2.0
        inner_side_x_mm = self.bounds.xmax - PERIMETER_WALL_THICKNESS_MM
        inner_back_y_mm = self.bounds.ymax - PERIMETER_WALL_THICKNESS_MM

        for x_mm in (-76.5, -25.5, 25.5, 76.5):
            jar = (
                cq.Workplane("XY")
                .box(
                    PARAMETERS["item_width_mm"],
                    PARAMETERS["item_length_mm"],
                    PARAMETERS["item_height_mm"],
                )
                .translate(
                    (
                        x_mm,
                        jar_center_y_mm,
                        PARAMETERS["item_height_mm"] / 2.0,
                    )
                )
                .rotate((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), angle_degrees)
                .translate((0.0, self.tray_offset_y_mm, translation_z_mm))
            )
            jar_bounds = jar.val().BoundingBox()

            self.assertGreaterEqual(jar_bounds.xmin, -inner_side_x_mm)
            self.assertLessEqual(jar_bounds.xmax, inner_side_x_mm)
            self.assertGreaterEqual(jar_bounds.ymin, self.bounds.ymin)
            self.assertLessEqual(jar_bounds.ymax, inner_back_y_mm)
            self.assertLess(jar_bounds.zmax, PARAMETERS["max_drawer_height_mm"])
            self.assertAlmostEqual(self.tray.val().intersect(jar.val()).Volume(), 0.0, places=3)

    def test_rejects_geometry_that_breaks_tray_policy(self) -> None:
        with self.assertRaisesRegex(ValueError, "above max_drawer_height_mm"):
            build(max_drawer_height_mm=88.0)
        with self.assertRaisesRegex(ValueError, "3U depth"):
            build(unit_depth=4)
        with self.assertRaisesRegex(ValueError, "item width"):
            build(unit_width=1)
        with self.assertRaisesRegex(ValueError, "surface_depth_mm is too short"):
            build(surface_depth_mm=113.0)


if __name__ == "__main__":
    unittest.main()
