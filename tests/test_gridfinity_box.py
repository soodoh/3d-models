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
    def test_short_walls_keep_single_extrusion_breakaway_lattice(self) -> None:
        for available_height in (3.8, 38.8, 42.0):
            with self.subTest(available_height=available_height):
                profile = gridfinity_box._breakaway_brace_profile(available_height)

                self.assertEqual(profile.strength_scale, 1)
                self.assertAlmostEqual(profile.thickness_mm, 0.4)
                self.assertAlmostEqual(profile.support_width_mm, 1.2)
                self.assertEqual(len(profile.crossbar_height_ratios), 3)

    def test_height_just_above_strength_step_uses_next_profile(self) -> None:
        profile = gridfinity_box._breakaway_brace_profile(42.001)

        self.assertEqual(profile.strength_scale, 2)
        self.assertAlmostEqual(profile.thickness_mm, 0.8)
        self.assertEqual(len(profile.crossbar_height_ratios), 6)

    def test_seven_and_eight_unit_walls_use_double_strength_lattice(self) -> None:
        for available_height in (45.8, 52.8):
            with self.subTest(available_height=available_height):
                profile = gridfinity_box._breakaway_brace_profile(available_height)

                self.assertEqual(profile.strength_scale, 2)
                self.assertAlmostEqual(profile.thickness_mm, 0.8)
                self.assertAlmostEqual(profile.crossbar_height_mm, 2.4)
                self.assertAlmostEqual(profile.support_width_mm, 2.4)
                self.assertEqual(len(profile.crossbar_height_ratios), 6)

    def test_very_tall_walls_cap_at_removable_triple_strength(self) -> None:
        for available_height in (87.8, 500.0):
            with self.subTest(available_height=available_height):
                profile = gridfinity_box._breakaway_brace_profile(available_height)

                self.assertEqual(profile.strength_scale, 3)
                self.assertAlmostEqual(profile.thickness_mm, 1.2)
                self.assertAlmostEqual(profile.support_width_mm, 3.6)
                self.assertEqual(len(profile.crossbar_height_ratios), 9)


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
                horizontal_specs=(horizontal_divider,),
                vertical_specs=(),
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
                horizontal_specs=(),
                vertical_specs=(vertical_divider,),
                breakaway_brace_top_z=20.0,
            )

        self.assertEqual(add_brace.call_count, 1)
        self.assertEqual(add_brace.call_args.kwargs["split_axis"], "width")
        self.assertEqual(add_brace.call_args.kwargs["inside_direction"], 1)

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
