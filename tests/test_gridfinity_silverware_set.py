"""Tests for the split Cambridge Beacon Gridfinity silverware modules."""

from __future__ import annotations

import unittest

from print_models.catalog import load_models
from print_models.models.gridfinity_silverware_set import (
    PARAMETERS,
    _build_utensil_cutter,
    _fork_width_profile,
    _spoon_width_profile,
    build,
)


class SilverwareSetGeometryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.parts = build()
        cls.shapes = {name: part.val() for name, part in cls.parts.items()}

    def test_catalog_exposes_supplied_silverware_measurements(self) -> None:
        models = load_models()

        self.assertIn("gridfinity_silverware_set", models)
        self.assertEqual(PARAMETERS["unit_height"], 6)
        self.assertEqual(PARAMETERS["spoon_unit_width"], 2)
        self.assertEqual(PARAMETERS["finger_relief_diameter_mm"], 24.0)
        self.assertEqual(PARAMETERS["large_fork_width_mm"], 25.0)
        self.assertEqual(PARAMETERS["large_fork_length_mm"], 208.0)
        self.assertEqual(PARAMETERS["large_fork_stack_height_mm"], 24.0)
        self.assertEqual(PARAMETERS["large_fork_handle_bottom_width_mm"], 10.0)
        self.assertEqual(PARAMETERS["large_fork_handle_narrow_width_mm"], 7.0)
        self.assertEqual(PARAMETERS["small_fork_width_mm"], 23.0)
        self.assertEqual(PARAMETERS["small_fork_length_mm"], 180.0)
        self.assertEqual(PARAMETERS["small_fork_stack_height_mm"], 22.0)
        self.assertEqual(PARAMETERS["small_fork_handle_bottom_width_mm"], 9.0)
        self.assertEqual(PARAMETERS["small_fork_handle_narrow_width_mm"], 7.0)
        self.assertEqual(PARAMETERS["small_spoon_width_mm"], 36.0)
        self.assertEqual(PARAMETERS["small_spoon_length_mm"], 175.0)
        self.assertEqual(PARAMETERS["small_spoon_stack_height_mm"], 23.0)
        self.assertEqual(PARAMETERS["large_spoon_width_mm"], 41.0)
        self.assertEqual(PARAMETERS["large_spoon_length_mm"], 201.0)
        self.assertEqual(PARAMETERS["large_spoon_stack_height_mm"], 24.0)
        self.assertEqual(PARAMETERS["spoon_handle_bottom_width_mm"], 10.0)
        self.assertEqual(PARAMETERS["spoon_handle_narrow_width_mm"], 7.0)
        self.assertEqual(PARAMETERS["knife_count"], 8)
        self.assertEqual(PARAMETERS["knife_length_mm"], 236.0)
        self.assertEqual(PARAMETERS["knife_handle_length_mm"], 125.0)
        self.assertEqual(PARAMETERS["knife_blade_length_mm"], 111.0)
        self.assertEqual(PARAMETERS["knife_handle_lift_angle_degrees"], 3.0)
        self.assertFalse(any(name.startswith("knife_lift_trough_") for name in PARAMETERS))

    def test_build_returns_six_named_printable_halves(self) -> None:
        self.assertEqual(
            set(self.parts),
            {
                "fork_module_front",
                "fork_module_back",
                "spoon_module_front",
                "spoon_module_back",
                "knife_module_front",
                "knife_module_back",
            },
        )
        for part in self.parts.values():
            self.assertEqual(len(part.solids().vals()), 1)

    def test_halves_preserve_gridfinity_envelopes(self) -> None:
        expected_widths = {
            "fork_module": 83.5,
            "spoon_module": 83.5,
            "knife_module": 83.5,
        }
        for module_name, expected_width in expected_widths.items():
            for half_name in ("front", "back"):
                bounds = self.shapes[f"{module_name}_{half_name}"].BoundingBox()
                self.assertAlmostEqual(bounds.xlen, expected_width, places=3)
                self.assertAlmostEqual(bounds.ylen, 125.75, places=3)
                self.assertAlmostEqual(bounds.zlen, 45.8, places=3)

    def test_fork_pockets_use_maximum_depth_with_two_millimeter_floors(self) -> None:
        import cadquery as cq

        front = self.shapes["fork_module_front"]
        for center_x in (-15.5, 14.5):
            with self.subTest(center_x=center_x):
                self.assertFalse(front.isInside(cq.Vector(center_x, -70.0, 9.5), 1e-6))
                self.assertTrue(front.isInside(cq.Vector(center_x, -70.0, 8.5), 1e-6))
        self.assertTrue(front.isInside(cq.Vector(0.0, -70.0, 37.0), 1e-6))

    def test_fork_cutters_use_measured_widths_plus_clearance(self) -> None:
        import cadquery as cq

        fork_measurements = (
            (25.0, 208.0, 10.0, 7.0),
            (23.0, 180.0, 9.0, 7.0),
        )
        for fork_width_mm, fork_length_mm, bottom_width_mm, narrow_width_mm in fork_measurements:
            with self.subTest(fork_width_mm=fork_width_mm):
                width_profile = _fork_width_profile(
                    max_width_mm=fork_width_mm,
                    bottom_handle_width_mm=bottom_width_mm,
                    narrow_handle_width_mm=narrow_width_mm,
                )
                cutter = _build_utensil_cutter(
                    center_x=0.0,
                    center_y=0.0,
                    bottom_z=10.0,
                    top_z=42.2,
                    width_mm=fork_width_mm,
                    length_mm=fork_length_mm,
                    width_profile=width_profile,
                    fit_clearance_mm=1.0,
                    finger_relief_diameter_mm=24.0,
                ).val()
                handle_bottom_y = -fork_length_mm / 2.0
                measured_sections = (
                    (handle_bottom_y, bottom_width_mm),
                    (handle_bottom_y + fork_length_mm * 0.65, narrow_width_mm),
                    (handle_bottom_y + fork_length_mm * 0.75, fork_width_mm),
                )
                for handle_fraction in (0.50, 0.55, 0.60, 0.63, 0.65):
                    handle_y = handle_bottom_y + fork_length_mm * handle_fraction
                    self.assertTrue(cutter.isInside(cq.Vector(4.4, handle_y, 20.0), 1e-6))

                for section_y, measured_width_mm in measured_sections:
                    half_cleared_width_mm = measured_width_mm / 2.0 + 1.0
                    self.assertTrue(
                        cutter.isInside(
                            cq.Vector(half_cleared_width_mm - 0.1, section_y, 20.0), 1e-6
                        )
                    )
                    self.assertFalse(
                        cutter.isInside(
                            cq.Vector(half_cleared_width_mm + 0.1, section_y, 20.0), 1e-6
                        )
                    )

    def test_spoon_pockets_are_staggered_at_maximum_depth(self) -> None:
        import cadquery as cq

        front = self.shapes["spoon_module_front"]
        back = self.shapes["spoon_module_back"]
        small_spoon_center = (-18.0, -20.0)
        large_spoon_center = (17.0, 20.0)

        self.assertFalse(front.isInside(cq.Vector(small_spoon_center[0], -70.0, 9.5), 1e-6))
        self.assertTrue(front.isInside(cq.Vector(small_spoon_center[0], -70.0, 8.5), 1e-6))
        self.assertFalse(back.isInside(cq.Vector(large_spoon_center[0], 70.0, 9.5), 1e-6))
        self.assertTrue(back.isInside(cq.Vector(large_spoon_center[0], 70.0, 8.5), 1e-6))
        self.assertTrue(back.isInside(cq.Vector(0.0, 60.0, 37.0), 1e-6))

    def test_spoon_cutters_use_measured_handle_widths_plus_clearance(self) -> None:
        import cadquery as cq

        for spoon_width_mm, spoon_length_mm in ((36.0, 175.0), (41.0, 201.0)):
            with self.subTest(spoon_width_mm=spoon_width_mm):
                width_profile = _spoon_width_profile(
                    max_width_mm=spoon_width_mm,
                    bottom_handle_width_mm=10.0,
                    narrow_handle_width_mm=7.0,
                )
                cutter = _build_utensil_cutter(
                    center_x=0.0,
                    center_y=0.0,
                    bottom_z=10.0,
                    top_z=35.2,
                    width_mm=spoon_width_mm,
                    length_mm=spoon_length_mm,
                    width_profile=width_profile,
                    fit_clearance_mm=1.0,
                    finger_relief_diameter_mm=24.0,
                ).val()
                handle_bottom_y = -spoon_length_mm / 2.0
                handle_narrow_y = handle_bottom_y + spoon_length_mm * 0.65

                self.assertTrue(cutter.isInside(cq.Vector(5.9, handle_bottom_y, 20.0), 1e-6))
                self.assertFalse(cutter.isInside(cq.Vector(6.1, handle_bottom_y, 20.0), 1e-6))
                for handle_fraction in (0.50, 0.55, 0.60, 0.63, 0.65):
                    handle_y = handle_bottom_y + spoon_length_mm * handle_fraction
                    self.assertTrue(cutter.isInside(cq.Vector(4.4, handle_y, 20.0), 1e-6))
                self.assertFalse(cutter.isInside(cq.Vector(4.6, handle_narrow_y, 20.0), 1e-6))
                bowl_end_y = spoon_length_mm / 2.0
                self.assertTrue(cutter.isInside(cq.Vector(0.9, bowl_end_y, 20.0), 1e-6))
                self.assertFalse(cutter.isInside(cq.Vector(1.1, bowl_end_y, 20.0), 1e-6))
                self.assertTrue(cutter.isInside(cq.Vector(0.5, bowl_end_y + 0.8, 20.0), 1e-6))
                self.assertFalse(cutter.isInside(cq.Vector(0.7, bowl_end_y + 0.8, 20.0), 1e-6))

    def test_utensil_finger_reliefs_use_twenty_four_millimeter_diameter(self) -> None:
        import cadquery as cq

        cutter = _build_utensil_cutter(
            center_x=0.0,
            center_y=0.0,
            bottom_z=10.0,
            top_z=42.2,
            width_mm=23.0,
            length_mm=180.0,
            width_profile=_fork_width_profile(
                max_width_mm=23.0,
                bottom_handle_width_mm=9.0,
                narrow_handle_width_mm=7.0,
            ),
            fit_clearance_mm=1.0,
            finger_relief_diameter_mm=24.0,
        ).val()
        relief_center_y = -90.0 + 28.0

        self.assertTrue(cutter.isInside(cq.Vector(11.9, relief_center_y, 20.0), 1e-6))
        self.assertFalse(cutter.isInside(cq.Vector(12.1, relief_center_y, 20.0), 1e-6))

    def test_knife_module_has_eight_separate_angled_stepped_slots(self) -> None:
        import cadquery as cq

        front = self.shapes["knife_module_front"]
        back = self.shapes["knife_module_back"]
        slot_pitch = 9.7
        slot_centers = tuple(-33.95 + index * slot_pitch for index in range(8))

        for center_x in slot_centers:
            self.assertFalse(front.isInside(cq.Vector(center_x, -90.0, 38.5), 1e-6))
            self.assertTrue(front.isInside(cq.Vector(center_x, -90.0, 37.5), 1e-6))
            self.assertFalse(back.isInside(cq.Vector(center_x, 60.0, 25.5), 1e-6))
            self.assertTrue(back.isInside(cq.Vector(center_x, 60.0, 24.75), 1e-6))
            self.assertFalse(back.isInside(cq.Vector(center_x + 4.1, 7.0, 35.0), 1e-6))
            self.assertTrue(back.isInside(cq.Vector(center_x + 4.4, 7.0, 35.0), 1e-6))
            self.assertFalse(back.isInside(cq.Vector(center_x + 1.4, 8.0, 35.0), 1e-6))
            self.assertTrue(back.isInside(cq.Vector(center_x + 1.6, 8.0, 35.0), 1e-6))

        rib_center_x = (slot_centers[0] + slot_centers[1]) / 2.0
        self.assertTrue(front.isInside(cq.Vector(rib_center_x, -90.0, 25.0), 1e-6))
        self.assertTrue(back.isInside(cq.Vector(slot_centers[0] + 2.0, 60.0, 20.0), 1e-6))

    def test_knife_module_preserves_solid_deck_between_angled_slots(self) -> None:
        import cadquery as cq

        front = self.shapes["knife_module_front"]
        former_trough_center_y = -55.75
        slot_centers = tuple(-33.95 + index * 9.7 for index in range(8))

        for center_x in slot_centers:
            with self.subTest(center_x=center_x):
                self.assertFalse(
                    front.isInside(cq.Vector(center_x, former_trough_center_y, 37.0), 1e-6)
                )
                self.assertTrue(
                    front.isInside(cq.Vector(center_x, former_trough_center_y, 35.0), 1e-6)
                )

        rib_centers = tuple(
            (left_center + right_center) / 2.0
            for left_center, right_center in zip(slot_centers[:-1], slot_centers[1:], strict=True)
        )
        for center_x in rib_centers:
            self.assertTrue(front.isInside(cq.Vector(center_x, former_trough_center_y, 37.0), 1e-6))

    def test_every_export_part_is_one_valid_shell(self) -> None:
        for name, part in self.parts.items():
            with self.subTest(name=name):
                self.assertTrue(part.val().isValid())
                self.assertEqual(len(part.shells().vals()), 1)

    def test_rejects_inconsistent_knife_section_lengths(self) -> None:
        with self.assertRaisesRegex(ValueError, "must add up"):
            build(knife_blade_length_mm=110.0)

    def test_rejects_invalid_knife_handle_lift_angles(self) -> None:
        with self.assertRaisesRegex(ValueError, "must not be negative"):
            build(knife_handle_lift_angle_degrees=-0.1)
        with self.assertRaisesRegex(ValueError, "must be less than 90"):
            build(knife_handle_lift_angle_degrees=90.0)

    def test_rejects_fork_handle_that_does_not_taper(self) -> None:
        with self.assertRaisesRegex(ValueError, "must exceed"):
            build(
                small_fork_handle_bottom_width_mm=7.0,
                small_fork_handle_narrow_width_mm=7.0,
            )

    def test_rejects_spoon_handle_that_does_not_taper(self) -> None:
        with self.assertRaisesRegex(ValueError, "must exceed"):
            build(spoon_handle_bottom_width_mm=7.0, spoon_handle_narrow_width_mm=7.0)


if __name__ == "__main__":
    unittest.main()
