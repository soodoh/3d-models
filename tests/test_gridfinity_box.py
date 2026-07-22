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
            with self.subTest(unit_height=unit_height), patch.object(
                gridfinity_box,
                "_add_breakaway_brace_lattice",
                side_effect=keep_part,
            ) as add_brace:
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


if __name__ == "__main__":
    unittest.main()
