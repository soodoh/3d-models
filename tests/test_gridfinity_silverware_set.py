"""Tests for the split Cambridge Beacon Gridfinity silverware and steak-knife modules."""

from __future__ import annotations

import unittest

from print_models.catalog import load_models
from print_models.models.gridfinity_silverware_set import (
    MINIMUM_DECK_RING_MM,
    PARAMETERS,
    _build_profiled_knife_slot,
    _build_utensil_cutter,
    _extend_steak_knife_profile_middle,
    _fork_width_profile,
    _spoon_width_profile,
    _steak_knife_broadside_spine_offset,
    _steak_knife_section_profile,
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
        self.assertEqual(PARAMETERS["utensil_handle_extension_mm"], 4.0)
        self.assertNotIn("utensil_grab_bay_width_mm", PARAMETERS)
        self.assertEqual(PARAMETERS["utensil_grab_bay_length_mm"], 40.0)
        self.assertEqual(PARAMETERS["utensil_grab_bay_center_y_mm"], -42.0)
        self.assertEqual(PARAMETERS["utensil_lead_in_mm"], 2.0)
        self.assertEqual(PARAMETERS["utensil_lead_in_depth_mm"], 8.0)
        self.assertEqual(PARAMETERS["utensil_handle_lift_mm"], 4.0)
        self.assertNotIn("finger_relief_diameter_mm", PARAMETERS)
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
        self.assertEqual(PARAMETERS["knife_blade_transition_length_mm"], 10.0)
        self.assertEqual(PARAMETERS["knife_blade_transition_extra_width_mm"], 1.0)
        self.assertEqual(PARAMETERS["knife_handle_lift_angle_degrees"], 3.0)
        self.assertFalse(any(name.startswith("knife_lift_trough_") for name in PARAMETERS))
        self.assertEqual(PARAMETERS["steak_knife_unit_width"], 4)
        self.assertEqual(PARAMETERS["steak_knife_count"], 8)
        self.assertEqual(PARAMETERS["steak_knife_length_mm"], 222.0)
        self.assertEqual(PARAMETERS["steak_knife_handle_length_mm"], 106.0)
        self.assertEqual(PARAMETERS["steak_knife_blade_length_mm"], 116.0)
        self.assertEqual(PARAMETERS["steak_knife_blade_width_mm"], 17.6)
        self.assertEqual(PARAMETERS["steak_knife_blade_thickness_mm"], 1.0)
        self.assertEqual(PARAMETERS["steak_knife_handle_top_width_mm"], 24.0)
        self.assertEqual(PARAMETERS["steak_knife_handle_narrow_width_mm"], 16.5)
        self.assertEqual(PARAMETERS["steak_knife_handle_main_width_mm"], 21.0)
        self.assertEqual(PARAMETERS["steak_knife_handle_bottom_width_mm"], 27.5)
        self.assertEqual(PARAMETERS["steak_knife_handle_thickness_mm"], 15.2)
        self.assertEqual(PARAMETERS["steak_knife_handle_neck_thickness_mm"], 11.0)
        self.assertEqual(PARAMETERS["steak_knife_handle_tip_thickness_mm"], 6.0)
        self.assertEqual(PARAMETERS["steak_knife_handle_cap_length_mm"], 11.0)
        self.assertEqual(PARAMETERS["steak_knife_handle_cap_peak_offset_mm"], 5.0)
        self.assertEqual(PARAMETERS["steak_knife_handle_neck_length_mm"], 22.0)
        self.assertEqual(PARAMETERS["steak_knife_handle_edge_bulb_length_mm"], 18.0)
        self.assertEqual(PARAMETERS["steak_knife_handle_edge_bulb_peak_offset_mm"], 9.0)
        self.assertEqual(PARAMETERS["steak_knife_handle_edge_bulb_flat_length_mm"], 12.0)
        self.assertEqual(PARAMETERS["steak_knife_slot_middle_extension_mm"], 4.0)

    def test_build_returns_eight_named_printable_halves(self) -> None:
        self.assertEqual(
            set(self.parts),
            {
                "fork_module_front",
                "fork_module_back",
                "spoon_module_front",
                "spoon_module_back",
                "knife_module_front",
                "knife_module_back",
                "steak_knife_module_front",
                "steak_knife_module_back",
            },
        )
        for part in self.parts.values():
            self.assertEqual(len(part.solids().vals()), 1)

    def test_halves_preserve_gridfinity_envelopes(self) -> None:
        expected_widths = {
            "fork_module": 83.5,
            "spoon_module": 83.5,
            "knife_module": 83.5,
            "steak_knife_module": 167.5,
        }
        for module_name, expected_width in expected_widths.items():
            for half_name in ("front", "back"):
                bounds = self.shapes[f"{module_name}_{half_name}"].BoundingBox()
                self.assertAlmostEqual(bounds.xlen, expected_width, places=3)
                self.assertAlmostEqual(bounds.ylen, 125.75, places=3)
                self.assertAlmostEqual(bounds.zlen, 45.8, places=3)

    def test_fork_heads_keep_maximum_depth_with_two_millimeter_floors(self) -> None:
        import cadquery as cq

        back = self.shapes["fork_module_back"]
        for center_x in (-15.5, 14.5):
            with self.subTest(center_x=center_x):
                self.assertFalse(back.isInside(cq.Vector(center_x, 70.0, 9.5), 1e-6))
                self.assertTrue(back.isInside(cq.Vector(center_x, 70.0, 8.5), 1e-6))
        self.assertTrue(back.isInside(cq.Vector(0.0, 70.0, 37.0), 1e-6))

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

    def test_spoon_heads_are_staggered_at_maximum_depth(self) -> None:
        import cadquery as cq

        back = self.shapes["spoon_module_back"]
        head_locations = ((-18.0, 50.0), (17.0, 90.0))

        for center_x, head_y in head_locations:
            with self.subTest(center_x=center_x, head_y=head_y):
                self.assertFalse(back.isInside(cq.Vector(center_x, head_y, 9.5), 1e-6))
                self.assertTrue(back.isInside(cq.Vector(center_x, head_y, 8.5), 1e-6))
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
                self.assertTrue(cutter.isInside(cq.Vector(5.0, bowl_end_y, 20.0), 1e-6))
                self.assertFalse(cutter.isInside(cq.Vector(6.0, bowl_end_y, 20.0), 1e-6))
                self.assertTrue(cutter.isInside(cq.Vector(2.0, bowl_end_y + 0.8, 20.0), 1e-6))
                self.assertFalse(cutter.isInside(cq.Vector(3.0, bowl_end_y + 0.8, 20.0), 1e-6))

    def test_utensil_cutters_add_requested_access_features(self) -> None:
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
        ).val()

        self.assertTrue(cutter.isInside(cq.Vector(0.0, -94.9, 20.0), 1e-6))
        self.assertFalse(cutter.isInside(cq.Vector(0.0, -95.1, 20.0), 1e-6))
        self.assertFalse(cutter.isInside(cq.Vector(0.0, -90.0, 13.9), 1e-6))
        self.assertTrue(cutter.isInside(cq.Vector(0.0, -90.0, 14.1), 1e-6))
        self.assertFalse(cutter.isInside(cq.Vector(0.0, 70.0, 9.9), 1e-6))
        self.assertTrue(cutter.isInside(cq.Vector(0.0, 70.0, 10.1), 1e-6))

        self.assertFalse(cutter.isInside(cq.Vector(17.9, -18.0, 20.0), 1e-6))

        self.assertFalse(cutter.isInside(cq.Vector(6.0, 18.0, 33.9), 1e-6))
        self.assertTrue(cutter.isInside(cq.Vector(6.0, 18.0, 40.0), 1e-6))

    def test_modules_use_one_wall_to_wall_stadium_grab_bay(self) -> None:
        import cadquery as cq

        for module_name in ("fork_module_front", "spoon_module_front"):
            module = self.shapes[module_name]
            with self.subTest(module_name=module_name):
                for x_position in (-40.7, 0.0, 40.7):
                    self.assertFalse(module.isInside(cq.Vector(x_position, -42.0, 20.0), 1e-6))
                self.assertTrue(module.isInside(cq.Vector(-40.8, -42.0, 20.0), 1e-6))
                self.assertTrue(module.isInside(cq.Vector(40.8, -42.0, 20.0), 1e-6))

                self.assertFalse(module.isInside(cq.Vector(0.0, -61.9, 20.0), 1e-6))
                self.assertFalse(module.isInside(cq.Vector(20.0, -61.9, 20.0), 1e-6))
                self.assertTrue(module.isInside(cq.Vector(25.0, -61.9, 20.0), 1e-6))
                self.assertFalse(module.isInside(cq.Vector(38.0, -50.0, 20.0), 1e-6))
                self.assertTrue(module.isInside(cq.Vector(40.0, -52.0, 20.0), 1e-6))

                self.assertTrue(module.isInside(cq.Vector(0.0, -63.0, 20.0), 1e-6))
                self.assertTrue(module.isInside(cq.Vector(0.0, -21.0, 20.0), 1e-6))
                self.assertTrue(module.isInside(cq.Vector(0.0, -42.0, 12.9), 1e-6))
                self.assertFalse(module.isInside(cq.Vector(0.0, -42.0, 13.1), 1e-6))

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
            self.assertFalse(back.isInside(cq.Vector(center_x + 1.9, 8.0, 35.0), 1e-6))
            self.assertTrue(back.isInside(cq.Vector(center_x + 2.1, 8.0, 35.0), 1e-6))
            self.assertFalse(back.isInside(cq.Vector(center_x + 1.4, 17.0, 35.0), 1e-6))
            self.assertTrue(back.isInside(cq.Vector(center_x + 1.6, 17.0, 35.0), 1e-6))

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

    def test_steak_knife_slots_span_usable_width_evenly(self) -> None:
        import cadquery as cq

        front = self.shapes["steak_knife_module_front"]
        maximum_slot_width = 15.808 + 2.0 * PARAMETERS["knife_slot_clearance_mm"]
        inner_half_width = front.BoundingBox().xlen / 2.0 - PARAMETERS["wall_thickness_mm"]
        outer_center_x = inner_half_width - MINIMUM_DECK_RING_MM - maximum_slot_width / 2.0
        slot_pitch = 2.0 * outer_center_x / (PARAMETERS["steak_knife_count"] - 1)
        slot_centers = tuple(
            -outer_center_x + index * slot_pitch for index in range(PARAMETERS["steak_knife_count"])
        )

        for center_x in slot_centers:
            with self.subTest(center_x=center_x):
                self.assertFalse(front.isInside(cq.Vector(center_x, -90.0, 38.5), 1e-6))

        for left_center, right_center in zip(slot_centers[:-1], slot_centers[1:], strict=True):
            rib_center_x = (left_center + right_center) / 2.0
            self.assertTrue(front.isInside(cq.Vector(rib_center_x, -90.0, 38.5), 1e-6))

    def test_steak_knife_cutter_follows_calibrated_full_profile(self) -> None:
        import cadquery as cq

        profile = _steak_knife_section_profile(
            knife_length_mm=222.0,
            handle_length_mm=106.0,
            blade_length_mm=116.0,
            blade_width_mm=17.6,
            blade_thickness_mm=1.0,
            handle_top_width_mm=24.0,
            handle_narrow_width_mm=16.5,
            handle_main_width_mm=21.0,
            handle_bottom_width_mm=27.5,
            handle_thickness_mm=15.2,
            handle_neck_thickness_mm=11.0,
            handle_tip_thickness_mm=6.0,
            handle_cap_length_mm=11.0,
            handle_cap_peak_offset_mm=5.0,
            handle_neck_length_mm=22.0,
            handle_edge_bulb_length_mm=18.0,
            handle_edge_bulb_peak_offset_mm=9.0,
            handle_edge_bulb_flat_length_mm=12.0,
        )
        self.assertEqual(profile[0], (0.0, 0.2, 0.0))
        self.assertEqual(profile[7], (12.0, 15.2, 27.5))
        self.assertEqual(profile[9], (22.0, 15.2, 21.0))
        self.assertEqual(profile[14], (84.0, 11.0, 16.995))
        self.assertAlmostEqual(profile[15][0], 87.08)
        self.assertAlmostEqual(profile[15][2], 16.5)
        self.assertAlmostEqual(profile[18][0], 91.0)
        self.assertAlmostEqual(profile[18][1], 15.808)
        self.assertAlmostEqual(profile[24][0], 103.0)
        self.assertAlmostEqual(profile[24][1], 15.808)
        self.assertAlmostEqual(profile[24][0] - profile[18][0], 12.0)
        self.assertAlmostEqual(profile[26][0], 105.8)
        self.assertAlmostEqual(profile[26][1], 6.0)
        self.assertAlmostEqual(profile[26][2], 24.0)
        self.assertEqual(
            _steak_knife_broadside_spine_offset(0.0, handle_bottom_width_mm=27.5),
            -13.75,
        )
        self.assertEqual(
            _steak_knife_broadside_spine_offset(12.0, handle_bottom_width_mm=27.5),
            0.0,
        )
        slot_profile = _extend_steak_knife_profile_middle(profile, extension_mm=4.0)
        self.assertEqual(slot_profile[9][0], 22.0)
        self.assertEqual(slot_profile[10][0], 66.0)
        self.assertEqual(slot_profile[-1][0], 226.0)
        cutter = _build_profiled_knife_slot(
            center_x=0.0,
            start_y=0.0,
            deck_top_z=42.0,
            knife_length_mm=222.0,
            section_profile=profile,
            lateral_clearance_mm=0.5,
            vertical_clearance_mm=1.0,
        ).val()
        bounds = cutter.BoundingBox()

        self.assertAlmostEqual(bounds.xlen, 16.808, places=3)
        self.assertAlmostEqual(bounds.ymin, -0.5, places=3)
        self.assertAlmostEqual(bounds.ymax, 222.5, places=3)
        self.assertAlmostEqual(bounds.zmin, 13.5, places=3)
        self.assertAlmostEqual(bounds.zmax, 42.2, places=3)

        self.assertTrue(cutter.isInside(cq.Vector(8.0, 45.0, 20.0), 1e-6))
        self.assertFalse(cutter.isInside(cq.Vector(8.2, 45.0, 20.0), 1e-6))
        self.assertTrue(cutter.isInside(cq.Vector(5.9, 84.0, 30.0), 1e-6))
        self.assertFalse(cutter.isInside(cq.Vector(6.1, 84.0, 30.0), 1e-6))
        self.assertTrue(cutter.isInside(cq.Vector(3.4, 105.8, 30.0), 1e-6))
        self.assertFalse(cutter.isInside(cq.Vector(3.6, 105.8, 30.0), 1e-6))
        self.assertTrue(cutter.isInside(cq.Vector(0.9, 132.0, 30.0), 1e-6))
        self.assertFalse(cutter.isInside(cq.Vector(1.1, 132.0, 30.0), 1e-6))
        self.assertFalse(cutter.isInside(cq.Vector(0.0, 132.0, 23.3), 1e-6))
        self.assertTrue(cutter.isInside(cq.Vector(0.0, 132.0, 23.5), 1e-6))

    def test_every_export_part_is_one_valid_shell(self) -> None:
        for name, part in self.parts.items():
            with self.subTest(name=name):
                self.assertTrue(part.val().isValid())
                self.assertEqual(len(part.shells().vals()), 1)

    def test_rejects_inconsistent_knife_section_lengths(self) -> None:
        with self.assertRaisesRegex(ValueError, "must add up"):
            build(knife_blade_length_mm=110.0)

    def test_rejects_inconsistent_steak_knife_section_lengths(self) -> None:
        with self.assertRaisesRegex(ValueError, "must add up"):
            build(steak_knife_blade_length_mm=115.0)

    def test_rejects_invalid_steak_knife_handle_profile(self) -> None:
        with self.assertRaisesRegex(ValueError, "must descend"):
            build(steak_knife_handle_main_width_mm=16.0)
        with self.assertRaisesRegex(ValueError, "must exceed"):
            build(steak_knife_handle_neck_thickness_mm=15.2)
        with self.assertRaisesRegex(ValueError, "must exceed"):
            build(steak_knife_handle_tip_thickness_mm=15.2)
        with self.assertRaisesRegex(ValueError, "must be less than"):
            build(steak_knife_handle_cap_peak_offset_mm=11.0)
        with self.assertRaisesRegex(ValueError, "fit inside"):
            build(steak_knife_handle_neck_length_mm=95.0)
        with self.assertRaisesRegex(ValueError, "flat must fit"):
            build(steak_knife_handle_edge_bulb_flat_length_mm=18.0)

    def test_rejects_invalid_knife_blade_transition(self) -> None:
        with self.assertRaisesRegex(ValueError, "must not be negative"):
            build(knife_blade_transition_extra_width_mm=-0.1)
        with self.assertRaisesRegex(ValueError, "must not exceed"):
            build(knife_blade_transition_length_mm=112.0)

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
