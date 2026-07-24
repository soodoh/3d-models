"""Focused policy tests for Gridfinity split-face breakaway braces."""

from __future__ import annotations

import unittest
from unittest.mock import patch

import print_models.models.gridfinity_box as gridfinity_box
from print_models.models.gridfinity_box import (
    DividerSpec,
    SegmentBreakawayBraces,
    _resolve_segment_breakaway_braces,
)


class SegmentBreakawayBraceTests(unittest.TestCase):
    def resolve(
        self,
        *,
        split_positions_u: tuple[float, ...] = (4.0,),
        divider_specs: tuple[DividerSpec, ...] = (),
        unit_count: int = 7,
        full_span_axis_units: int = 2,
    ) -> tuple[SegmentBreakawayBraces, ...]:
        return _resolve_segment_breakaway_braces(
            unit_count=unit_count,
            split_positions_u=split_positions_u,
            parallel_divider_specs=divider_specs,
            divider_full_span_axis_units=full_span_axis_units,
        )

    def test_adds_braces_to_both_faces_of_every_unsupported_split(self) -> None:
        self.assertEqual(
            self.resolve(split_positions_u=(2.0, 5.0)),
            (
                SegmentBreakawayBraces(minimum_side=False, maximum_side=True),
                SegmentBreakawayBraces(minimum_side=True, maximum_side=True),
                SegmentBreakawayBraces(minimum_side=True, maximum_side=False),
            ),
        )

    def test_divider_before_split_suppresses_only_that_side(self) -> None:
        divider = DividerSpec(position_u=3.0, span_start_u=0.0, span_end_u=2.0)

        self.assertEqual(
            self.resolve(divider_specs=(divider,)),
            (
                SegmentBreakawayBraces(minimum_side=False, maximum_side=False),
                SegmentBreakawayBraces(minimum_side=True, maximum_side=False),
            ),
        )

    def test_divider_after_split_suppresses_only_that_side(self) -> None:
        divider = DividerSpec(position_u=5.0, span_start_u=0.0, span_end_u=2.0)

        self.assertEqual(
            self.resolve(divider_specs=(divider,)),
            (
                SegmentBreakawayBraces(minimum_side=False, maximum_side=True),
                SegmentBreakawayBraces(minimum_side=False, maximum_side=False),
            ),
        )

    def test_divider_exactly_two_units_away_suppresses_brace(self) -> None:
        divider = DividerSpec(position_u=2.0, span_start_u=0.0, span_end_u=2.0)

        self.assertFalse(self.resolve(divider_specs=(divider,))[0].maximum_side)

    def test_divider_more_than_two_units_away_does_not_suppress_brace(self) -> None:
        divider = DividerSpec(position_u=1.99, span_start_u=0.0, span_end_u=2.0)

        self.assertTrue(self.resolve(divider_specs=(divider,))[0].maximum_side)

    def test_divider_outside_adjacent_segment_does_not_suppress_brace(self) -> None:
        divider = DividerSpec(position_u=2.5, span_start_u=0.0, span_end_u=2.0)

        braces = self.resolve(
            split_positions_u=(3.0, 4.0),
            divider_specs=(divider,),
        )

        self.assertTrue(braces[1].maximum_side)

    def test_partial_divider_does_not_suppress_brace(self) -> None:
        divider = DividerSpec(position_u=3.0, span_start_u=0.0, span_end_u=1.0)

        self.assertTrue(self.resolve(divider_specs=(divider,))[0].maximum_side)

    def test_divider_on_split_suppresses_both_faces(self) -> None:
        divider = DividerSpec(position_u=4.0, span_start_u=0.0, span_end_u=2.0)

        self.assertEqual(
            self.resolve(divider_specs=(divider,)),
            (
                SegmentBreakawayBraces(minimum_side=False, maximum_side=False),
                SegmentBreakawayBraces(minimum_side=False, maximum_side=False),
            ),
        )


class BreakawayBraceProfileTests(unittest.TestCase):
    def test_all_supported_heights_use_the_shared_strength(self) -> None:
        profile = gridfinity_box._breakaway_brace_profile()

        self.assertAlmostEqual(profile.thickness_mm, 0.8)
        self.assertAlmostEqual(profile.crossbar_height_mm, 2.4)
        self.assertAlmostEqual(profile.support_width_mm, 2.4)
        self.assertEqual(len(profile.crossbar_height_ratios), 6)
        for actual_ratio, expected_ratio in zip(
            profile.crossbar_height_ratios,
            (1 / 6, 2 / 6, 3 / 6, 4 / 6, 5 / 6, 1.0),
            strict=True,
        ):
            self.assertAlmostEqual(actual_ratio, expected_ratio)

    def test_lipped_box_support_ends_below_the_lip(self) -> None:
        from cqgridfinity import GR_LIP_H

        box_top_z = 45.8
        brace_top_z = gridfinity_box._resolve_breakaway_brace_top_z(
            box_top_z=box_top_z,
            lip_enabled=True,
        )

        self.assertAlmostEqual(
            brace_top_z,
            box_top_z - GR_LIP_H - gridfinity_box.BREAKAWAY_LIP_CLEARANCE_MM,
        )
        self.assertAlmostEqual(
            gridfinity_box._resolve_breakaway_brace_top_z(
                box_top_z=box_top_z,
                lip_enabled=False,
            ),
            box_top_z - gridfinity_box.BREAKAWAY_LIP_CLEARANCE_MM,
        )


class BreakawayBraceDistributionTests(unittest.TestCase):
    def test_crossing_dividers_are_resolved_in_the_current_segment(self) -> None:
        divider_specs = (
            DividerSpec(position_u=0.5, span_start_u=0.0, span_end_u=3.0),
            DividerSpec(position_u=1.0, span_start_u=3.1, span_end_u=6.0),
            DividerSpec(position_u=1.5, span_start_u=0.0, span_end_u=3.0),
        )

        self.assertEqual(
            gridfinity_box._crossing_divider_coordinates(
                split_position_u=3.0,
                perpendicular_divider_specs=divider_specs,
                position_axis_minimum=-41.75,
                segment_span_minimum=-41.75,
                segment_span_maximum=41.75,
                wall_thickness_mm=1.0,
            ),
            (-19.75, 22.25),
        )

    def test_dividers_partition_crossbar_spans_without_overlap(self) -> None:
        self.assertEqual(
            gridfinity_box._brace_open_spans(
                span_minimum=-20.0,
                span_maximum=20.0,
                divider_center_coordinates=(-10.0, 10.0),
                divider_thickness_mm=1.2,
            ),
            ((-20.0, -10.6), (-9.4, 9.4), (10.6, 20.0)),
        )

    def test_uprights_are_redistributed_between_every_edge(self) -> None:
        self.assertEqual(
            gridfinity_box._distributed_support_centers(((0.0, 20.0), (22.0, 52.0))),
            (10.0, 37.0),
        )


class BreakawayBraceGeometryTests(unittest.TestCase):
    def test_split_axes_use_the_parallel_divider_and_brace_only_the_other_side(self) -> None:
        import cadquery as cq

        def keep_part(part, **_kwargs):
            return part

        horizontal_divider = DividerSpec(
            position_u=3.0,
            span_start_u=0.0,
            span_end_u=2.0,
        )
        depth_box = cq.Workplane("XY").box(83.5, 293.5, 20.0).translate((0.0, 0.0, 10.0))
        with patch.object(
            gridfinity_box,
            "_add_breakaway_brace_lattice",
            side_effect=keep_part,
        ) as add_brace:
            gridfinity_box._split_rendered_box(
                depth_box,
                split_width_positions_u=(),
                split_depth_positions_u=(4.0,),
                unit_width=2,
                unit_depth=7,
                unit_height=8,
                horizontal_specs=(horizontal_divider,),
                vertical_specs=(),
                wall_thickness_mm=1.0,
                divider_thickness_mm=1.2,
                breakaway_brace_top_z=20.0,
            )

        self.assertEqual(add_brace.call_count, 1)
        self.assertEqual(add_brace.call_args.kwargs["split_axis"], "depth")
        self.assertEqual(add_brace.call_args.kwargs["inside_direction"], 1)

        vertical_divider = DividerSpec(
            position_u=3.0,
            span_start_u=0.0,
            span_end_u=2.0,
        )
        width_box = cq.Workplane("XY").box(293.5, 83.5, 20.0).translate((0.0, 0.0, 10.0))
        with patch.object(
            gridfinity_box,
            "_add_breakaway_brace_lattice",
            side_effect=keep_part,
        ) as add_brace:
            gridfinity_box._split_rendered_box(
                width_box,
                split_width_positions_u=(4.0,),
                split_depth_positions_u=(),
                unit_width=7,
                unit_depth=2,
                unit_height=8,
                horizontal_specs=(),
                vertical_specs=(vertical_divider,),
                wall_thickness_mm=1.0,
                divider_thickness_mm=1.2,
                breakaway_brace_top_z=20.0,
            )

        self.assertEqual(add_brace.call_count, 1)
        self.assertEqual(add_brace.call_args.kwargs["split_axis"], "width")
        self.assertEqual(add_brace.call_args.kwargs["inside_direction"], 1)

    def test_perpendicular_dividers_partition_both_split_faces(self) -> None:
        import cadquery as cq

        def keep_part(part, **_kwargs):
            return part

        divider_specs = (
            DividerSpec(position_u=0.5, span_start_u=0.0, span_end_u=4.0),
            DividerSpec(position_u=1.5, span_start_u=0.0, span_end_u=4.0),
        )
        width_box = cq.Workplane("XY").box(293.5, 83.5, 45.8).translate((0.0, 0.0, 22.9))
        with patch.object(
            gridfinity_box,
            "_add_breakaway_brace_lattice",
            side_effect=keep_part,
        ) as add_brace:
            gridfinity_box._split_rendered_box(
                width_box,
                split_width_positions_u=(4.0,),
                split_depth_positions_u=(),
                unit_width=7,
                unit_depth=2,
                unit_height=6,
                horizontal_specs=divider_specs,
                vertical_specs=(),
                wall_thickness_mm=1.0,
                divider_thickness_mm=1.2,
                breakaway_brace_top_z=38.2,
            )

        self.assertEqual(add_brace.call_count, 2)
        for add_brace_call in add_brace.call_args_list:
            self.assertEqual(
                add_brace_call.kwargs["divider_center_coordinates"],
                (-19.75, 22.25),
            )

    def test_braces_start_above_five_units_high(self) -> None:
        import cadquery as cq

        def keep_part(part, **_kwargs):
            return part

        split_box = cq.Workplane("XY").box(293.5, 83.5, 45.8).translate((0.0, 0.0, 22.9))
        for unit_height, expected_brace_count in ((5, 0), (6, 2)):
            with (
                self.subTest(unit_height=unit_height),
                patch.object(
                    gridfinity_box,
                    "_add_breakaway_brace_lattice",
                    side_effect=keep_part,
                ) as add_brace,
            ):
                parts = gridfinity_box._split_rendered_box(
                    split_box,
                    split_width_positions_u=(4.0,),
                    split_depth_positions_u=(),
                    unit_width=7,
                    unit_depth=2,
                    unit_height=unit_height,
                    horizontal_specs=(),
                    vertical_specs=(),
                    wall_thickness_mm=1.0,
                    divider_thickness_mm=1.2,
                    breakaway_brace_top_z=45.8,
                )

            self.assertEqual(len(parts), 2)
            self.assertEqual(add_brace.call_count, expected_brace_count)

    def test_raised_floor_does_not_raise_braces_on_another_segment(self) -> None:
        parts = gridfinity_box.build(
            unit_width=7,
            unit_depth=2,
            unit_height=8,
            split_width_u="4",
            auto_split=False,
            raised_floors="0-1@0-1:100",
        )
        unaffected_part = next(
            part for name, part in parts.items() if name.endswith("width_2_of_2")
        )

        self.assertEqual(len(unaffected_part.solids().vals()), 1)
        self.assertTrue(unaffected_part.val().isValid())
        self.assertAlmostEqual(unaffected_part.val().BoundingBox().zmax, 59.8, places=3)


class DovetailLidPolicyTests(unittest.TestCase):
    def test_validates_and_normalizes_lid_style(self) -> None:
        self.assertEqual(gridfinity_box._resolve_lid_style(" ZIPLOCK "), "ziplock")
        self.assertEqual(gridfinity_box._resolve_lid_style("wrap"), "wrap")
        with self.assertRaisesRegex(ValueError, "lid_style must be one of"):
            gridfinity_box._resolve_lid_style("hinged")
        with self.assertRaisesRegex(ValueError, "lid_style must be one of"):
            gridfinity_box._resolve_lid_style(1)

    def test_default_mode_preserves_legacy_geometry_and_name(self) -> None:
        result = gridfinity_box.build(
            unit_width=1,
            unit_depth=1,
            unit_height=3,
            auto_split=False,
        )
        explicit_result = gridfinity_box.build(
            unit_width=1,
            unit_depth=1,
            unit_height=3,
            auto_split=False,
            lid_style="none",
        )

        self.assertEqual(tuple(result), ("1x1x3u",))
        self.assertEqual(tuple(explicit_result), tuple(result))
        for part in (result["1x1x3u"], explicit_result["1x1x3u"]):
            bounding_box = part.val().BoundingBox()
            self.assertEqual(len(part.solids().vals()), 1)
            self.assertAlmostEqual(bounding_box.xlen, 41.5)
            self.assertAlmostEqual(bounding_box.ylen, 41.5)
            self.assertAlmostEqual(bounding_box.zlen, 24.8)
            self.assertAlmostEqual(part.val().Volume(), 14436.019618066, places=6)

    def test_selects_longest_slide_axis_and_depth_on_ties(self) -> None:
        import cadquery as cq

        box = cq.Workplane("XY").box(83.5, 209.5, 20.0).translate((0.0, 0.0, 10.0))
        depth_layout = gridfinity_box._resolve_dovetail_layout(
            box,
            unit_width=2,
            unit_depth=5,
        )
        width_layout = gridfinity_box._resolve_dovetail_layout(
            box,
            unit_width=5,
            unit_depth=2,
        )
        tied_layout = gridfinity_box._resolve_dovetail_layout(
            box,
            unit_width=2,
            unit_depth=2,
        )

        self.assertEqual(depth_layout.slide_axis, "depth")
        self.assertEqual(width_layout.slide_axis, "width")
        self.assertEqual(tied_layout.slide_axis, "depth")


class DovetailLidGeometryTests(unittest.TestCase):
    def assert_modeled_lid_clearances(self, box, lid, layout) -> None:
        box_bounds = box.val().BoundingBox()
        lid_bounds = lid.val().BoundingBox()
        if layout.slide_axis == "depth":
            lateral_clearances = (
                lid_bounds.xmin - (box_bounds.xmin + gridfinity_box.DOVETAIL_THROAT_MM),
                box_bounds.xmax - gridfinity_box.DOVETAIL_THROAT_MM - lid_bounds.xmax,
            )
            end_clearances = (
                lid_bounds.ymin - (box_bounds.ymin + gridfinity_box.DOVETAIL_THROAT_MM),
                box_bounds.ymax - lid_bounds.ymax,
            )
        else:
            lateral_clearances = (
                lid_bounds.ymin - (box_bounds.ymin + gridfinity_box.DOVETAIL_THROAT_MM),
                box_bounds.ymax - gridfinity_box.DOVETAIL_THROAT_MM - lid_bounds.ymax,
            )
            end_clearances = (
                lid_bounds.xmin - (box_bounds.xmin + gridfinity_box.DOVETAIL_THROAT_MM),
                box_bounds.xmax - lid_bounds.xmax,
            )

        for clearance in (*lateral_clearances, *end_clearances):
            self.assertAlmostEqual(
                clearance,
                gridfinity_box.DOVETAIL_MODELED_CLEARANCE_MM,
                places=5,
            )

    @classmethod
    def setUpClass(cls) -> None:
        cls.ziplock = gridfinity_box.build(
            unit_width=2,
            unit_depth=5,
            unit_height=3,
            auto_split=False,
            lid_style="ziplock",
        )
        cls.wrap = gridfinity_box.build(
            unit_width=2,
            unit_depth=5,
            unit_height=3,
            auto_split=False,
            lid_style="wrap",
        )

    def test_exports_valid_matching_box_and_lid_parts(self) -> None:
        self.assertEqual(
            tuple(self.ziplock),
            (
                "2x5x3u_dovetail_ziplock_box",
                "2x5x3u_dovetail_ziplock_lid",
            ),
        )
        for part in self.ziplock.values():
            self.assertTrue(part.val().isValid())
            self.assertEqual(len(part.solids().vals()), 1)
        lid = self.ziplock["2x5x3u_dovetail_ziplock_lid"]
        lid_box = lid.val().BoundingBox()
        bottom_box = lid.faces("<Z").val().BoundingBox()
        top_box = lid.faces(">Z").val().BoundingBox()
        self.assertAlmostEqual(lid_box.zmin, 0.0, places=6)
        self.assertAlmostEqual(
            lid_box.zlen,
            gridfinity_box.DOVETAIL_LID_THICKNESS_MM,
            places=6,
        )
        self.assertAlmostEqual(
            top_box.ymin - bottom_box.ymin,
            gridfinity_box.DOVETAIL_SIDE_INSET_MM,
        )
        self.assertAlmostEqual(top_box.ymax, bottom_box.ymax)

    def test_ziplock_and_wrap_openings_are_distinct(self) -> None:
        ziplock_lid = self.ziplock["2x5x3u_dovetail_ziplock_lid"]
        wrap_lid = self.wrap["2x5x3u_dovetail_wrap_lid"]

        self.assertLess(ziplock_lid.val().Volume(), wrap_lid.val().Volume())
        self.assertAlmostEqual(
            ziplock_lid.val().BoundingBox().zlen,
            wrap_lid.val().BoundingBox().zlen,
        )

    def test_lid_seats_with_low_stop_and_positive_open_end(self) -> None:
        box = self.ziplock["2x5x3u_dovetail_ziplock_box"]
        lid = self.ziplock["2x5x3u_dovetail_ziplock_lid"]
        layout = gridfinity_box._resolve_dovetail_layout(
            box,
            unit_width=2,
            unit_depth=5,
        )
        self.assert_modeled_lid_clearances(box, lid, layout)
        assembled_lid = lid.translate(
            (0.0, 0.0, layout.box_top_z - gridfinity_box.DOVETAIL_LID_THICKNESS_MM)
        )

        self.assertEqual(len(box.intersect(assembled_lid).solids().vals()), 0)
        withdrawn_lid = assembled_lid.translate((0.0, layout.lid_length * 0.5, 0.0))
        self.assertEqual(len(box.intersect(withdrawn_lid).solids().vals()), 0)
        blocked_lid = assembled_lid.translate((0.0, -0.3, 0.0))
        self.assertGreater(box.intersect(blocked_lid).val().Volume(), 1.0)

    def test_one_unit_footprint_scales_to_valid_distinct_styles(self) -> None:
        results = {
            lid_style: gridfinity_box.build(
                unit_width=1,
                unit_depth=1,
                unit_height=2,
                auto_split=False,
                lid_style=lid_style,
            )
            for lid_style in ("ziplock", "wrap")
        }

        for result in results.values():
            self.assertEqual(len(result), 2)
            for part in result.values():
                self.assertTrue(part.val().isValid())
                self.assertEqual(len(part.solids().vals()), 1)
        ziplock_lid = next(
            part for name, part in results["ziplock"].items() if name.endswith("_lid")
        )
        wrap_lid = next(part for name, part in results["wrap"].items() if name.endswith("_lid"))
        self.assertLess(ziplock_lid.val().Volume(), wrap_lid.val().Volume())

    def test_width_sliding_lid_clears_travel_and_is_retained(self) -> None:
        result = gridfinity_box.build(
            unit_width=5,
            unit_depth=2,
            unit_height=2,
            auto_split=False,
            lid_style="wrap",
        )
        box = next(part for name, part in result.items() if name.endswith("_box"))
        lid = next(part for name, part in result.items() if name.endswith("_lid"))
        layout = gridfinity_box._resolve_dovetail_layout(
            box,
            unit_width=5,
            unit_depth=2,
        )
        self.assertEqual(layout.slide_axis, "width")
        self.assert_modeled_lid_clearances(box, lid, layout)
        seated_lid = lid.translate(
            (0.0, 0.0, layout.box_top_z - gridfinity_box.DOVETAIL_LID_THICKNESS_MM)
        )

        for travel_fraction in (0.0, 0.25, 0.5, 1.05):
            with self.subTest(travel_fraction=travel_fraction):
                traveling_lid = seated_lid.translate(
                    (layout.lid_length * travel_fraction, 0.0, 0.0)
                )
                self.assertEqual(len(box.intersect(traveling_lid).solids().vals()), 0)

        blocked_lid = seated_lid.translate((-0.3, 0.0, 0.0))
        self.assertGreater(box.intersect(blocked_lid).val().Volume(), 1.0)
        lifted_lid = seated_lid.translate(
            (0.0, 0.0, gridfinity_box.DOVETAIL_MODELED_CLEARANCE_MM + 0.15)
        )
        self.assertGreater(box.intersect(lifted_lid).val().Volume(), 1.0)


class DovetailReferenceGeometryTests(unittest.TestCase):
    @staticmethod
    def is_inside(part, x: float, y: float, z: float) -> bool:
        import cadquery as cq

        return part.val().isInside(cq.Vector(x, y, z), 1e-5)

    @classmethod
    def setUpClass(cls) -> None:
        cls.ziplock_result = gridfinity_box.build(
            unit_width=2,
            unit_depth=5,
            unit_height=9,
            auto_split=False,
            lid_style="ziplock",
        )
        cls.ziplock_box = cls.ziplock_result["2x5x9u_dovetail_ziplock_box"]
        cls.ziplock_lid = cls.ziplock_result["2x5x9u_dovetail_ziplock_lid"]
        cls.wrap_result = gridfinity_box.build(
            unit_width=2,
            unit_depth=8,
            unit_height=9,
            auto_split=False,
            lid_style="wrap",
        )
        cls.wrap_box = cls.wrap_result["2x8x9u_dovetail_wrap_box"]
        cls.feature_plain_box = cls.build_wrap_feature_box()

    def test_ziplock_reference_height_floor_and_lid_envelope(self) -> None:
        box_bounds = self.ziplock_box.val().BoundingBox()
        lid_bounds = self.ziplock_lid.val().BoundingBox()

        self.assertAlmostEqual(box_bounds.zmax, 63.0, places=6)
        self.assertTrue(self.is_inside(self.ziplock_box, 0.0, 0.0, 7.39))
        self.assertFalse(self.is_inside(self.ziplock_box, 0.0, 0.0, 7.41))
        self.assertAlmostEqual(lid_bounds.xlen, 81.931376, places=5)
        self.assertAlmostEqual(lid_bounds.ylen, 208.565685, places=5)
        self.assertAlmostEqual(lid_bounds.zlen, 2.4, places=5)

    def test_depth_channel_has_vertical_wall_throat_slope_and_open_high_end(self) -> None:
        bounds = self.ziplock_box.val().BoundingBox()
        x_minimum = bounds.xmin
        left_corner_boundary_x = (
            x_minimum
            + gridfinity_box.DOVETAIL_MINIMUM_WALL_MM
            + gridfinity_box.DOVETAIL_CHANNEL_INTERIOR_REACH_MM
        )
        right_corner_boundary_x = (
            bounds.xmax
            - gridfinity_box.DOVETAIL_MINIMUM_WALL_MM
            - gridfinity_box.DOVETAIL_CHANNEL_INTERIOR_REACH_MM
        )

        self.assertTrue(
            self.is_inside(
                self.ziplock_box,
                left_corner_boundary_x - gridfinity_box.DOVETAIL_BOOLEAN_OVERLAP_MM,
                bounds.ymin + 1.0,
                60.3,
            )
        )
        self.assertFalse(
            self.is_inside(
                self.ziplock_box,
                left_corner_boundary_x + gridfinity_box.DOVETAIL_BOOLEAN_OVERLAP_MM,
                bounds.ymin + 1.0,
                60.3,
            )
        )
        self.assertTrue(
            self.is_inside(
                self.ziplock_box,
                right_corner_boundary_x + gridfinity_box.DOVETAIL_BOOLEAN_OVERLAP_MM,
                bounds.ymin + 1.0,
                60.3,
            )
        )
        self.assertFalse(
            self.is_inside(
                self.ziplock_box,
                right_corner_boundary_x - gridfinity_box.DOVETAIL_BOOLEAN_OVERLAP_MM,
                bounds.ymin + 1.0,
                60.3,
            )
        )
        self.assertTrue(self.is_inside(self.ziplock_box, x_minimum + 2.3, 0.0, 60.3))
        self.assertFalse(self.is_inside(self.ziplock_box, x_minimum + 2.5, 0.0, 60.3))
        self.assertTrue(self.is_inside(self.ziplock_box, x_minimum + 0.62, 0.0, 60.5))
        self.assertFalse(self.is_inside(self.ziplock_box, x_minimum + 0.65, 0.0, 60.5))
        self.assertTrue(self.is_inside(self.ziplock_box, x_minimum + 1.52, 0.0, 61.8))
        self.assertFalse(self.is_inside(self.ziplock_box, x_minimum + 1.55, 0.0, 61.8))
        self.assertTrue(self.is_inside(self.ziplock_box, 0.0, bounds.ymin + 0.62, 60.4))
        self.assertFalse(self.is_inside(self.ziplock_box, 0.0, bounds.ymin + 0.65, 60.4))
        self.assertTrue(self.is_inside(self.ziplock_box, x_minimum + 2.3, bounds.ymin + 0.5, 60.5))
        self.assertFalse(self.is_inside(self.ziplock_box, x_minimum + 2.3, bounds.ymin + 0.8, 60.5))
        self.assertTrue(self.is_inside(self.ziplock_box, 0.0, bounds.ymax - 1.0, 60.3))
        self.assertFalse(self.is_inside(self.ziplock_box, 0.0, bounds.ymax - 1.0, 60.5))
        self.assertFalse(self.is_inside(self.ziplock_box, x_minimum + 2.3, bounds.ymax - 0.5, 60.5))

    def test_width_sliding_uses_the_same_channel_and_end_profile(self) -> None:
        result = gridfinity_box.build(
            unit_width=5,
            unit_depth=2,
            unit_height=9,
            auto_split=False,
            lid_style="ziplock",
        )
        box = result["5x2x9u_dovetail_ziplock_box"]
        bounds = box.val().BoundingBox()
        lower_corner_boundary_y = (
            bounds.ymin
            + gridfinity_box.DOVETAIL_MINIMUM_WALL_MM
            + gridfinity_box.DOVETAIL_CHANNEL_INTERIOR_REACH_MM
        )
        upper_corner_boundary_y = (
            bounds.ymax
            - gridfinity_box.DOVETAIL_MINIMUM_WALL_MM
            - gridfinity_box.DOVETAIL_CHANNEL_INTERIOR_REACH_MM
        )

        self.assertTrue(
            self.is_inside(
                box,
                bounds.xmin + 1.0,
                lower_corner_boundary_y - gridfinity_box.DOVETAIL_BOOLEAN_OVERLAP_MM,
                60.3,
            )
        )
        self.assertFalse(
            self.is_inside(
                box,
                bounds.xmin + 1.0,
                lower_corner_boundary_y + gridfinity_box.DOVETAIL_BOOLEAN_OVERLAP_MM,
                60.3,
            )
        )
        self.assertTrue(
            self.is_inside(
                box,
                bounds.xmin + 1.0,
                upper_corner_boundary_y + gridfinity_box.DOVETAIL_BOOLEAN_OVERLAP_MM,
                60.3,
            )
        )
        self.assertFalse(
            self.is_inside(
                box,
                bounds.xmin + 1.0,
                upper_corner_boundary_y - gridfinity_box.DOVETAIL_BOOLEAN_OVERLAP_MM,
                60.3,
            )
        )
        self.assertTrue(self.is_inside(box, 0.0, bounds.ymin + 2.3, 60.3))
        self.assertFalse(self.is_inside(box, 0.0, bounds.ymin + 2.5, 60.3))
        self.assertTrue(self.is_inside(box, 0.0, bounds.ymin + 0.62, 60.5))
        self.assertFalse(self.is_inside(box, 0.0, bounds.ymin + 0.65, 60.5))
        self.assertTrue(self.is_inside(box, bounds.xmin + 0.5, bounds.ymin + 2.3, 60.5))
        self.assertFalse(self.is_inside(box, bounds.xmin + 0.8, bounds.ymin + 2.3, 60.5))
        self.assertTrue(self.is_inside(box, bounds.xmax - 1.0, 0.0, 60.3))
        self.assertFalse(self.is_inside(box, bounds.xmax - 1.0, 0.0, 60.5))
        self.assertFalse(self.is_inside(box, bounds.xmax - 0.5, bounds.ymin + 2.3, 60.5))

    def test_wrap_matches_reference_trough_shelf_and_volume(self) -> None:
        bounds = self.wrap_box.val().BoundingBox()
        inner_minimum = bounds.xmin + gridfinity_box.DOVETAIL_MINIMUM_WALL_MM
        left_spring = inner_minimum + gridfinity_box.DOVETAIL_WRAP_LEFT_LEDGE_MM
        center = left_spring + gridfinity_box.DOVETAIL_WRAP_RADIUS_MM
        shelf_x = center + gridfinity_box.DOVETAIL_WRAP_RADIUS_MM + 5.0
        shelf_top = bounds.zmax - gridfinity_box.DOVETAIL_INTERIOR_CEILING_DROP_MM

        self.assertTrue(self.is_inside(self.wrap_box, center, 0.0, 7.39))
        self.assertFalse(self.is_inside(self.wrap_box, center, 0.0, 7.41))
        self.assertTrue(self.is_inside(self.wrap_box, left_spring - 0.1, 0.0, 34.0))
        self.assertFalse(self.is_inside(self.wrap_box, left_spring + 0.1, 0.0, 34.0))
        self.assertTrue(self.is_inside(self.wrap_box, shelf_x, 0.0, shelf_top - 0.01))
        self.assertFalse(self.is_inside(self.wrap_box, shelf_x, 0.0, shelf_top + 0.01))
        self.assertTrue(self.wrap_box.val().isValid())
        self.assertEqual(len(self.wrap_box.solids().vals()), 1)
        self.assertLess(
            abs(self.wrap_box.val().Volume() - 826010.950) / 826010.950,
            0.02,
        )

    def test_wrap_scales_for_narrow_box(self) -> None:
        result = gridfinity_box.build(
            unit_width=5,
            unit_depth=1,
            unit_height=3,
            auto_split=False,
            lid_style="wrap",
        )
        for part in result.values():
            self.assertTrue(part.val().isValid())
            self.assertEqual(len(part.solids().vals()), 1)

    def test_one_unit_wrap_box_has_documented_usable_cavity(self) -> None:
        result = gridfinity_box.build(
            unit_width=1,
            unit_depth=1,
            unit_height=1,
            auto_split=False,
            lid_style="wrap",
        )
        box = next(part for name, part in result.items() if name.endswith("_box"))
        box_bounds = box.val().BoundingBox()
        usable_cavity_height = (
            box_bounds.zmax
            - gridfinity_box.DOVETAIL_INTERIOR_CEILING_DROP_MM
            - gridfinity_box.DOVETAIL_INTERIOR_FLOOR_Z
        )

        self.assertAlmostEqual(
            usable_cavity_height,
            gridfinity_box.DOVETAIL_MINIMUM_USABLE_CAVITY_MM,
            places=6,
        )
        self.assertGreaterEqual(
            usable_cavity_height + gridfinity_box.POSITION_TOLERANCE_MM,
            1.2,
        )
        self.assertTrue(box.val().isValid())
        self.assertEqual(len(box.solids().vals()), 1)

    @staticmethod
    def build_wrap_feature_box(**feature_parameters):
        result = gridfinity_box.build(
            unit_width=2,
            unit_depth=3,
            unit_height=4,
            auto_split=False,
            lid_style="wrap",
            **feature_parameters,
        )
        return next(part for name, part in result.items() if name.endswith("_box"))

    def test_wrap_visible_full_and_partial_dividers_change_geometry(self) -> None:
        divider_parameters = (
            {"horizontal_dividers": "1.5"},
            {"vertical_dividers": "0.5"},
            {"horizontal_dividers": "1.5@0-0.5"},
        )
        for parameters in divider_parameters:
            with self.subTest(parameters=parameters):
                divider_box = self.build_wrap_feature_box(**parameters)
                self.assertNotAlmostEqual(
                    self.feature_plain_box.val().Volume(), divider_box.val().Volume()
                )
                self.assertTrue(divider_box.val().isValid())
                self.assertEqual(len(divider_box.solids().vals()), 1)

    def test_wrap_rejects_full_and_partial_dividers_embedded_in_shelf(self) -> None:
        divider_parameters = (
            {"vertical_dividers": "1"},
            {"horizontal_dividers": "1.5@1-2"},
        )
        for parameters in divider_parameters:
            with self.subTest(parameters=parameters):
                with self.assertRaisesRegex(ValueError, "fully embedded in the raised shelf"):
                    self.build_wrap_feature_box(**parameters)

    def test_width_sliding_wrap_validates_divider_visibility(self) -> None:
        common_parameters = {
            "unit_width": 3,
            "unit_depth": 2,
            "unit_height": 4,
            "auto_split": False,
            "lid_style": "wrap",
        }
        plain_result = gridfinity_box.build(**common_parameters)
        visible_result = gridfinity_box.build(
            **common_parameters,
            vertical_dividers="1.5",
        )
        plain_box = next(part for name, part in plain_result.items() if name.endswith("_box"))
        visible_box = next(part for name, part in visible_result.items() if name.endswith("_box"))
        self.assertNotAlmostEqual(plain_box.val().Volume(), visible_box.val().Volume())
        self.assertTrue(visible_box.val().isValid())
        self.assertEqual(len(visible_box.solids().vals()), 1)

        with self.assertRaisesRegex(ValueError, "fully embedded in the raised shelf"):
            gridfinity_box.build(
                unit_width=3,
                unit_depth=2,
                unit_height=4,
                horizontal_dividers="1.5",
                auto_split=False,
                lid_style="wrap",
            )

    def test_wrap_scoop_only_changes_geometry(self) -> None:
        scoop_box = self.build_wrap_feature_box(scoops=True)

        self.assertNotAlmostEqual(self.feature_plain_box.val().Volume(), scoop_box.val().Volume())
        self.assertTrue(scoop_box.val().isValid())
        self.assertEqual(len(scoop_box.solids().vals()), 1)

    def test_wrap_trough_raised_floor_only_changes_geometry(self) -> None:
        raised_floor_box = self.build_wrap_feature_box(raised_floors="0.5-1.0@0.5-1.0:2")

        self.assertNotAlmostEqual(
            self.feature_plain_box.val().Volume(), raised_floor_box.val().Volume()
        )
        self.assertTrue(raised_floor_box.val().isValid())
        self.assertEqual(len(raised_floor_box.solids().vals()), 1)

    def test_wrap_rejects_raised_floor_fully_embedded_in_shelf(self) -> None:
        with self.assertRaisesRegex(ValueError, "fully embedded in the wrap shelf"):
            self.build_wrap_feature_box(raised_floors="1.5-2@1-2:2")

    def test_wrap_rejects_floor_above_lid_ceiling(self) -> None:
        with self.assertRaisesRegex(ValueError, "dovetail lid ceiling"):
            self.build_wrap_feature_box(raised_floors="0-1@0-1:19")


class DovetailLidSplitTests(unittest.TestCase):
    def test_automatic_splits_use_matching_box_and_lid_suffixes(self) -> None:
        result = gridfinity_box.build(
            unit_width=2,
            unit_depth=8,
            unit_height=6,
            lid_style="wrap",
        )
        box_names = [name for name in result if "_box_" in name]
        lid_names = [name for name in result if "_lid_" in name]

        self.assertEqual(len(box_names), 2)
        self.assertEqual(len(lid_names), 2)
        self.assertEqual(
            [name.rsplit("_box_", 1)[1] for name in box_names],
            [name.rsplit("_lid_", 1)[1] for name in lid_names],
        )
        for part in result.values():
            bounding_box = part.val().BoundingBox()
            self.assertTrue(part.val().isValid())
            self.assertEqual(len(part.solids().vals()), 1)
            self.assertTrue(
                gridfinity_box._tile_fits(
                    bounding_box.xlen,
                    bounding_box.ylen,
                    240.0,
                    210.0,
                    True,
                )
            )

    def test_forced_split_names_both_part_kinds_stably(self) -> None:
        result = gridfinity_box.build(
            unit_width=2,
            unit_depth=4,
            unit_height=3,
            split_depth="2",
            auto_split=False,
            lid_style="ziplock",
        )

        self.assertEqual(len(result), 4)
        self.assertEqual(
            tuple(result),
            (
                "2x4x3u_split_depth_2u_dovetail_ziplock_box_depth_1_of_2",
                "2x4x3u_split_depth_2u_dovetail_ziplock_box_depth_2_of_2",
                "2x4x3u_split_depth_2u_dovetail_ziplock_lid_depth_1_of_2",
                "2x4x3u_split_depth_2u_dovetail_ziplock_lid_depth_2_of_2",
            ),
        )

    def test_asymmetric_lid_and_box_split_planes_align(self) -> None:
        result = gridfinity_box.build(
            unit_width=2,
            unit_depth=4,
            unit_height=2,
            split_depth="1",
            auto_split=False,
            lid_style="ziplock",
        )
        first_box = next(
            part for name, part in result.items() if name.endswith("_box_depth_1_of_2")
        )
        second_box = next(
            part for name, part in result.items() if name.endswith("_box_depth_2_of_2")
        )
        first_lid = next(
            part for name, part in result.items() if name.endswith("_lid_depth_1_of_2")
        )
        second_lid = next(
            part for name, part in result.items() if name.endswith("_lid_depth_2_of_2")
        )

        self.assertAlmostEqual(
            first_box.val().BoundingBox().ymax,
            first_lid.val().BoundingBox().ymax,
            places=6,
        )
        self.assertAlmostEqual(
            second_box.val().BoundingBox().ymin,
            second_lid.val().BoundingBox().ymin,
            places=6,
        )

    def test_split_bars_keep_three_lid_sections_connected(self) -> None:
        result = gridfinity_box.build(
            unit_width=2,
            unit_depth=9,
            unit_height=2,
            split_depth="3,6",
            auto_split=False,
            lid_style="wrap",
        )
        lid_parts = [part for name, part in result.items() if "_lid_" in name]

        self.assertEqual(len(lid_parts), 3)
        for lid_part in lid_parts:
            self.assertTrue(lid_part.val().isValid())
            self.assertEqual(len(lid_part.solids().vals()), 1)

    def test_split_bars_keep_two_axis_lid_tiles_connected(self) -> None:
        result = gridfinity_box.build(
            unit_width=3,
            unit_depth=3,
            unit_height=2,
            split_width_u="1,2",
            split_depth="1,2",
            auto_split=False,
            lid_style="ziplock",
        )
        lid_parts = [part for name, part in result.items() if "_lid_" in name]

        self.assertEqual(len(lid_parts), 9)
        for lid_part in lid_parts:
            self.assertTrue(lid_part.val().isValid())
            self.assertEqual(len(lid_part.solids().vals()), 1)

    def test_lid_splitter_never_adds_breakaway_braces(self) -> None:
        import cadquery as cq

        lid = cq.Workplane("XY").box(83.0, 167.0, 2.4).translate((0.0, 0.0, 1.2))
        with patch.object(gridfinity_box, "_add_breakaway_brace_lattice") as add_brace:
            parts = gridfinity_box._split_rendered_lid(
                lid,
                reference_bounding_box=lid.val().BoundingBox(),
                split_width_positions_u=(),
                split_depth_positions_u=(2.0,),
                unit_width=2,
                unit_depth=4,
            )

        self.assertEqual(len(parts), 2)
        add_brace.assert_not_called()


if __name__ == "__main__":
    unittest.main()
