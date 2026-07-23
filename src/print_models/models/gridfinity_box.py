"""Parametric Gridfinity box with fractional divider placement."""

from __future__ import annotations

import math
from collections.abc import Iterable, Sequence
from dataclasses import dataclass

from print_models.dovetail import trapezoidal_panel

NAME = "gridfinity_box"
DESCRIPTION = (
    "Gridfinity storage box with a stacking lip or optional matching dovetail lid, solid "
    "no-hole bottom, fractional dividers, and reinforced print-bed-aware splitting."
)
PARAMETERS = {
    "unit_width": 5,
    "unit_depth": 5,
    "unit_height": 8,
    "horizontal_dividers": "",
    "vertical_dividers": "",
    "split_width_u": "",
    "split_depth": "",
    "auto_split": True,
    "max_print_width": 240.0,
    "max_print_depth": 210.0,
    "allow_rotation": True,
    "raised_floors": "",
    "scoops": False,
    "wall_thickness_mm": 1.0,
    "divider_thickness_mm": 1.2,
    "lid_style": "none",
}
PRINT_NOTES = (
    "Divider lists are comma-separated Gridfinity unit specs. Use either position for a "
    "full divider or position@span_start-span_end for a partial divider. Horizontal "
    "dividers run left-to-right and are positioned from the inside front edge along "
    "depth; their optional span is along width. Vertical dividers run front-to-back and "
    "are positioned from the inside left edge along width; their optional span is along "
    "depth. Positions and spans may be decimal units. Boxes are automatically split on "
    "Gridfinity unit boundaries when they exceed the default 240 x 210 mm safe print area "
    "for a Prusa CORE One+. Set auto_split=false to disable this, or provide explicit "
    "split positions to control either axis. Split boxes up to 5U high omit breakaway "
    "supports. Split boxes 6U and taller receive removable brace lattices unless that side "
    "has a full-span parallel divider within 2U of the split. All supports use 0.8 mm "
    "thickness, 2.4 mm upright width, and six 2.4 mm crossbars ending below the stacking "
    "lip or dovetail channels. Divider intersections partition each lattice so no brace "
    "overlaps a divider. Raised floor specs use x_start-x_end@y_start-y_end:height_mm. Set "
    "lid_style=ziplock or lid_style=wrap to use the hole-free reference body with a 2.4 mm "
    "minimum wall, 7.4 mm floor, low-coordinate profiled stop, and high-coordinate open "
    "end. Wrap adds an asymmetric semicircular trough and raised shelf. The lid withdraws "
    "through the high end along the longest footprint axis (depth on ties). Short dovetail "
    "boxes retain at least 1.2 mm of usable cavity height. Raised floors must remain below "
    "the lid ceiling and add visible material rather than being buried in the wrap shelf. "
    "Wrap dividers must cross the open trough rather than lie entirely within that shelf. "
    "Oversized lids use the box split planes and seam "
    "bars; breakaway braces are box-only."
)


@dataclass(frozen=True)
class DividerSpec:
    """One divider centerline with an optional span along the opposite axis."""

    position_u: float
    span_start_u: float
    span_end_u: float


@dataclass(frozen=True)
class RaisedFloorSpec:
    """One raised floor region expressed in Gridfinity units and millimeters."""

    x_start_u: float
    x_end_u: float
    y_start_u: float
    y_end_u: float
    height_mm: float


@dataclass(frozen=True)
class SegmentBreakawayBraces:
    """Whether a split segment needs a brace on either synthetic boundary."""

    minimum_side: bool
    maximum_side: bool


@dataclass(frozen=True)
class BreakawayBraceProfile:
    """Shared printable dimensions for a split-face support lattice."""

    thickness_mm: float
    crossbar_height_mm: float
    support_width_mm: float
    crossbar_height_ratios: tuple[float, ...]


@dataclass(frozen=True)
class DovetailLayout:
    """Resolved dimensions and orientation for a matching box and sliding lid."""

    slide_axis: str
    cross_extent: float
    slide_extent: float
    center_x: float
    center_y: float
    box_top_z: float
    lid_bottom_width: float
    lid_length: float
    lid_slide_center: float
    channel_floor_z: float
    interior_floor_z: float
    interior_ceiling_z: float
    wall_thickness_mm: float


GRID_UNIT_MM = 42.0
POSITION_TOLERANCE_MM = 1e-6
BREAKAWAY_DIVIDER_DISTANCE_U = 2.0
BREAKAWAY_MAX_UNBRACED_HEIGHT_U = 5
BREAKAWAY_BRACE_THICKNESS_MM = 0.8
BREAKAWAY_CROSSBAR_HEIGHT_MM = 2.4
BREAKAWAY_SUPPORT_WIDTH_MM = 2.4
BREAKAWAY_MAX_BRIDGE_MM = 15.0
BREAKAWAY_CROSSBAR_COUNT = 6
BREAKAWAY_LIP_CLEARANCE_MM = 1.0
DOVETAIL_LID_STYLES = ("none", "ziplock", "wrap")
DOVETAIL_LID_THICKNESS_MM = 2.4
DOVETAIL_SIDE_INSET_MM = 3.2
DOVETAIL_THROAT_MM = 0.634315
DOVETAIL_LID_BOTTOM_INSET_MM = 0.634312
GRIDFINITY_BODY_FOOTPRINT_REDUCTION_MM = 0.5
DOVETAIL_REFERENCE_ENVELOPE_REDUCTION_MM = 0.8
DOVETAIL_MODELED_CLEARANCE_MM = (
    DOVETAIL_REFERENCE_ENVELOPE_REDUCTION_MM - GRIDFINITY_BODY_FOOTPRINT_REDUCTION_MM
) / 2.0
DOVETAIL_MINIMUM_WALL_MM = 2.4
DOVETAIL_BODY_HEIGHT_PER_UNIT_MM = 7.0
DOVETAIL_UPSTREAM_FLOOR_Z = 7.0
DOVETAIL_INTERIOR_FLOOR_Z = 7.4
DOVETAIL_FLOOR_FILLET_RUN_MM = 2.4
DOVETAIL_SIDE_SHOULDER_DROP_MM = 2.6
DOVETAIL_FRONT_SHOULDER_DROP_MM = 2.8
DOVETAIL_INTERIOR_CEILING_DROP_MM = 2.434315
DOVETAIL_MINIMUM_USABLE_CAVITY_MM = 1.2
DOVETAIL_VISIBLE_VOLUME_TOLERANCE_MM3 = 1e-6
DOVETAIL_MINIMUM_BODY_HEIGHT_MM = (
    DOVETAIL_INTERIOR_FLOOR_Z
    + DOVETAIL_INTERIOR_CEILING_DROP_MM
    + DOVETAIL_MINIMUM_USABLE_CAVITY_MM
)
DOVETAIL_CHANNEL_SLOPE_RUN_MM = 1.8
DOVETAIL_BOOLEAN_OVERLAP_MM = 0.05
DOVETAIL_WRAP_REFERENCE_INNER_SPAN_MM = 78.4
DOVETAIL_WRAP_LEFT_LEDGE_MM = 1.2
DOVETAIL_WRAP_RADIUS_MM = 26.6
DOVETAIL_LID_SPLIT_BAR_MM = 4.0
DOVETAIL_OPENING_END_MARGIN_MM = 6.0
DOVETAIL_OPENING_SIDE_MARGIN_MM = 4.0
DOVETAIL_REFERENCE_OPENING_OFFSET_MM = 11.8
DOVETAIL_REFERENCE_NARROW_OPENING_MM = 25.0
DOVETAIL_REFERENCE_ZIPLOCK_BULGE_MM = 23.7314


class FractionalDividerGridfinityBox:
    """GridfinityBox wrapper that renders dividers at explicit centerline positions."""

    def __init__(
        self,
        *,
        unit_width: int,
        unit_depth: int,
        unit_height: int,
        horizontal_specs: tuple[DividerSpec, ...],
        vertical_specs: tuple[DividerSpec, ...],
        wall_thickness_mm: float,
        divider_thickness_mm: float,
        scoops: bool,
        lip_enabled: bool,
    ) -> None:
        from cqgridfinity import GridfinityBox

        class CustomGridfinityBox(GridfinityBox):
            def __init__(self, *args, **kwargs):
                self.custom_horizontal_specs = horizontal_specs
                self.custom_vertical_specs = vertical_specs
                self.custom_divider_thickness_mm = divider_thickness_mm
                super().__init__(*args, **kwargs)

            @property
            def has_dividers(self):
                return bool(self.custom_horizontal_specs or self.custom_vertical_specs)

            def render_dividers(self):
                import cadquery as cq

                result = None

                for divider_spec in self.custom_vertical_specs:
                    y_center, y_length = self.divider_span_center_and_length(
                        span_start_u=divider_spec.span_start_u,
                        span_end_u=divider_spec.span_end_u,
                        axis_unit_count=self.width_u,
                        outer_axis_size=self.outer_w,
                        half_axis=self.half_w,
                    )
                    wall = (
                        cq.Workplane("XY")
                        .rect(self.custom_divider_thickness_mm, y_length)
                        .extrude(self.max_height)
                        .translate(
                            (
                                divider_spec.position_u * GRID_UNIT_MM - self.half_in,
                                y_center,
                                self.floor_h,
                            )
                        )
                    )
                    result = wall if result is None else result.union(wall)

                for divider_spec in self.custom_horizontal_specs:
                    x_center, x_length = self.divider_span_center_and_length(
                        span_start_u=divider_spec.span_start_u,
                        span_end_u=divider_spec.span_end_u,
                        axis_unit_count=self.length_u,
                        outer_axis_size=self.outer_l,
                        half_axis=self.half_l,
                    )
                    wall = (
                        cq.Workplane("XY")
                        .rect(x_length, self.custom_divider_thickness_mm)
                        .extrude(self.max_height)
                        .translate(
                            (
                                x_center,
                                divider_spec.position_u * GRID_UNIT_MM - self.half_in,
                                self.floor_h,
                            )
                        )
                    )
                    result = wall if result is None else result.union(wall)

                return result

            def divider_span_center_and_length(
                self,
                *,
                span_start_u,
                span_end_u,
                axis_unit_count,
                outer_axis_size,
                half_axis,
            ):
                if span_start_u == 0:
                    span_start = half_axis - outer_axis_size / 2.0
                else:
                    span_start = span_start_u * GRID_UNIT_MM - self.half_in

                if span_end_u == axis_unit_count:
                    span_end = half_axis + outer_axis_size / 2.0
                else:
                    span_end = span_end_u * GRID_UNIT_MM - self.half_in

                return span_start + (span_end - span_start) / 2.0, span_end - span_start

        self.box = CustomGridfinityBox(
            unit_width,
            unit_depth,
            unit_height,
            holes=False,
            scoops=scoops,
            labels=False,
            no_lip=not lip_enabled,
            fillet_interior=not _has_partial_dividers(
                horizontal_specs=horizontal_specs,
                vertical_specs=vertical_specs,
                unit_width=unit_width,
                unit_depth=unit_depth,
            ),
            wall_th=wall_thickness_mm,
        )

    def render(self):
        return self.box.render()


def build(
    unit_width: int = 5,
    unit_depth: int = 5,
    unit_height: int = 8,
    horizontal_dividers: str | Sequence[float] = "",
    vertical_dividers: str | Sequence[float] = "",
    split_width_u: str | Sequence[float] = "",
    split_depth: str | Sequence[float] = "",
    auto_split: bool = True,
    max_print_width: float = 240.0,
    max_print_depth: float = 210.0,
    allow_rotation: bool = True,
    raised_floors: str | Sequence[RaisedFloorSpec] = "",
    scoops: bool = False,
    wall_thickness_mm: float = 1.0,
    divider_thickness_mm: float = 1.2,
    lid_style: str = "none",
):
    """Build a Gridfinity storage box with optional custom dividers."""
    _validate_unit_count("unit_width", unit_width)
    _validate_unit_count("unit_depth", unit_depth)
    _validate_unit_count("unit_height", unit_height)
    _validate_positive("max_print_width", max_print_width)
    _validate_positive("max_print_depth", max_print_depth)
    _validate_positive("wall_thickness_mm", wall_thickness_mm)
    _validate_positive("divider_thickness_mm", divider_thickness_mm)
    normalized_lid_style = _resolve_lid_style(lid_style)
    effective_wall_thickness_mm = (
        wall_thickness_mm
        if normalized_lid_style == "none"
        else max(wall_thickness_mm, DOVETAIL_MINIMUM_WALL_MM)
    )
    render_unit_height = (
        unit_height if normalized_lid_style == "none" else max(unit_height, 2)
    )

    horizontal_specs = _resolve_divider_specs(
        axis_name="horizontal",
        position_axis_size_mm=_inner_size(unit_depth, effective_wall_thickness_mm),
        span_axis_units=unit_width,
        divider_thickness_mm=divider_thickness_mm,
        raw_specs=horizontal_dividers,
    )
    vertical_specs = _resolve_divider_specs(
        axis_name="vertical",
        position_axis_size_mm=_inner_size(unit_width, effective_wall_thickness_mm),
        span_axis_units=unit_depth,
        divider_thickness_mm=divider_thickness_mm,
        raw_specs=vertical_dividers,
    )

    split_width_positions_u = _resolve_split_positions(
        axis_name="width",
        unit_count=unit_width,
        unit_positions=split_width_u,
    )
    split_depth_positions_u = _resolve_split_positions(
        axis_name="depth",
        unit_count=unit_depth,
        unit_positions=split_depth,
    )
    raised_floor_specs = _resolve_raised_floor_specs(
        raw_specs=raised_floors,
        unit_width=unit_width,
        unit_depth=unit_depth,
    )

    box = FractionalDividerGridfinityBox(
        unit_width=unit_width,
        unit_depth=unit_depth,
        unit_height=render_unit_height,
        horizontal_specs=horizontal_specs,
        vertical_specs=vertical_specs,
        wall_thickness_mm=effective_wall_thickness_mm,
        divider_thickness_mm=divider_thickness_mm,
        scoops=scoops,
        lip_enabled=normalized_lid_style == "none",
    )
    rendered_box = box.render()
    rendered_lid = None
    if normalized_lid_style == "none":
        layout = None
        breakaway_brace_top_z = _resolve_breakaway_brace_top_z(
            box_top_z=rendered_box.val().BoundingBox().zmax,
            lip_enabled=True,
        )
        rendered_box = _apply_raised_floors(
            rendered_box,
            raised_floor_specs=raised_floor_specs,
            wall_thickness_mm=effective_wall_thickness_mm,
        )
    else:
        rendered_box = _trim_dovetail_body_height(rendered_box, unit_height=unit_height)
        layout = _resolve_dovetail_layout(
            rendered_box,
            unit_width=unit_width,
            unit_depth=unit_depth,
            wall_thickness_mm=effective_wall_thickness_mm,
        )
        _validate_dovetail_raised_floors(
            raised_floor_specs=raised_floor_specs,
            layout=layout,
        )
        rendered_box = _raise_dovetail_floor(rendered_box, layout=layout)
        if normalized_lid_style == "wrap":
            _validate_wrap_divider_visibility(
                rendered_box,
                layout=layout,
                horizontal_specs=horizontal_specs,
                vertical_specs=vertical_specs,
                divider_thickness_mm=divider_thickness_mm,
            )
            rendered_box = _add_wrap_interior(rendered_box, layout=layout)
            _validate_wrap_raised_floor_visibility(
                rendered_box,
                raised_floor_specs=raised_floor_specs,
                wall_thickness_mm=effective_wall_thickness_mm,
                floor_top_z=layout.interior_floor_z,
            )
        rendered_box = _apply_raised_floors(
            rendered_box,
            raised_floor_specs=raised_floor_specs,
            wall_thickness_mm=effective_wall_thickness_mm,
            floor_top_z=layout.interior_floor_z,
        )
        rendered_box = _clear_dovetail_interior_headspace(rendered_box, layout=layout)
        rendered_box = _add_dovetail_channels(rendered_box, layout)
        rendered_lid = _build_dovetail_lid(layout, normalized_lid_style)
        breakaway_brace_top_z = layout.channel_floor_z - BREAKAWAY_LIP_CLEARANCE_MM

    split_width_positions_u, split_depth_positions_u = _resolve_print_bed_splits(
        rendered_box,
        split_width_positions_u=split_width_positions_u,
        split_depth_positions_u=split_depth_positions_u,
        unit_width=unit_width,
        unit_depth=unit_depth,
        auto_split=auto_split,
        max_print_width=max_print_width,
        max_print_depth=max_print_depth,
        allow_rotation=allow_rotation,
        companion_rendered=rendered_lid,
    )
    box_bounding_box = rendered_box.val().BoundingBox()
    box_parts = _split_rendered_box(
        rendered_box,
        split_width_positions_u=split_width_positions_u,
        split_depth_positions_u=split_depth_positions_u,
        unit_width=unit_width,
        unit_depth=unit_depth,
        unit_height=unit_height,
        horizontal_specs=horizontal_specs,
        vertical_specs=vertical_specs,
        wall_thickness_mm=effective_wall_thickness_mm,
        divider_thickness_mm=divider_thickness_mm,
        breakaway_brace_top_z=breakaway_brace_top_z,
    )
    naming_parameters = {
        "unit_width": unit_width,
        "unit_depth": unit_depth,
        "unit_height": unit_height,
        "horizontal_specs": horizontal_specs,
        "vertical_specs": vertical_specs,
        "split_width_positions_u": split_width_positions_u,
        "split_depth_positions_u": split_depth_positions_u,
        "raised_floor_specs": raised_floor_specs,
        "scoops": scoops,
    }
    if rendered_lid is None:
        return _named_export_parts(box_parts, **naming_parameters)

    rendered_lid = _add_dovetail_lid_split_bars(
        rendered_lid,
        layout=layout,
        reference_bounding_box=box_bounding_box,
        split_width_positions_u=split_width_positions_u,
        split_depth_positions_u=split_depth_positions_u,
        unit_width=unit_width,
        unit_depth=unit_depth,
    )
    lid_parts = _split_rendered_lid(
        rendered_lid,
        reference_bounding_box=box_bounding_box,
        split_width_positions_u=split_width_positions_u,
        split_depth_positions_u=split_depth_positions_u,
        unit_width=unit_width,
        unit_depth=unit_depth,
    )
    return _named_dovetail_export_parts(
        box_parts,
        lid_parts,
        lid_style=normalized_lid_style,
        **naming_parameters,
    )


def _resolve_breakaway_brace_top_z(*, box_top_z: float, lip_enabled: bool) -> float:
    if not lip_enabled:
        return box_top_z - BREAKAWAY_LIP_CLEARANCE_MM

    from cqgridfinity import GR_LIP_H

    return box_top_z - GR_LIP_H - BREAKAWAY_LIP_CLEARANCE_MM


def _resolve_lid_style(lid_style: str) -> str:
    if not isinstance(lid_style, str):
        raise ValueError("lid_style must be one of: none, ziplock, wrap")

    normalized = lid_style.strip().lower()
    if normalized not in DOVETAIL_LID_STYLES:
        choices = ", ".join(DOVETAIL_LID_STYLES)
        raise ValueError(f"lid_style must be one of: {choices}")
    return normalized


def _trim_dovetail_body_height(rendered_box, *, unit_height: int):
    import cadquery as cq

    bounding_box = rendered_box.val().BoundingBox()
    target_top_z = max(
        unit_height * DOVETAIL_BODY_HEIGHT_PER_UNIT_MM,
        DOVETAIL_MINIMUM_BODY_HEIGHT_MM,
    )
    crop = (
        cq.Workplane("XY")
        .box(bounding_box.xlen + 2.0, bounding_box.ylen + 2.0, target_top_z + 1.0)
        .translate(
            (
                bounding_box.xmin + bounding_box.xlen / 2.0,
                bounding_box.ymin + bounding_box.ylen / 2.0,
                (target_top_z - 1.0) / 2.0,
            )
        )
    )
    return rendered_box.intersect(crop).clean()


def _resolve_dovetail_layout(
    rendered_box,
    *,
    unit_width: int,
    unit_depth: int,
    wall_thickness_mm: float = DOVETAIL_MINIMUM_WALL_MM,
) -> DovetailLayout:
    bounding_box = rendered_box.val().BoundingBox()
    slide_axis = "depth" if unit_depth >= unit_width else "width"
    cross_extent = bounding_box.xlen if slide_axis == "depth" else bounding_box.ylen
    slide_extent = bounding_box.ylen if slide_axis == "depth" else bounding_box.xlen
    cross_units = unit_width if slide_axis == "depth" else unit_depth
    slide_units = unit_depth if slide_axis == "depth" else unit_width
    nominal_cross_extent = (
        cross_units * GRID_UNIT_MM - DOVETAIL_REFERENCE_ENVELOPE_REDUCTION_MM
    )
    nominal_slide_extent = (
        slide_units * GRID_UNIT_MM - DOVETAIL_REFERENCE_ENVELOPE_REDUCTION_MM
    )
    lid_bottom_width = nominal_cross_extent - 2.0 * DOVETAIL_LID_BOTTOM_INSET_MM
    lid_length = nominal_slide_extent - DOVETAIL_THROAT_MM
    top_width = lid_bottom_width - 2.0 * DOVETAIL_SIDE_INSET_MM
    if top_width <= 2.0 * DOVETAIL_OPENING_SIDE_MARGIN_MM or lid_length <= 0:
        raise ValueError("Gridfinity footprint is too small for a printable dovetail lid.")

    center_x = bounding_box.xmin + bounding_box.xlen / 2.0
    center_y = bounding_box.ymin + bounding_box.ylen / 2.0
    slide_center = center_y if slide_axis == "depth" else center_x
    return DovetailLayout(
        slide_axis=slide_axis,
        cross_extent=cross_extent,
        slide_extent=slide_extent,
        center_x=center_x,
        center_y=center_y,
        box_top_z=bounding_box.zmax,
        lid_bottom_width=lid_bottom_width,
        lid_length=lid_length,
        lid_slide_center=slide_center + DOVETAIL_THROAT_MM / 2.0,
        channel_floor_z=bounding_box.zmax - DOVETAIL_SIDE_SHOULDER_DROP_MM,
        interior_floor_z=DOVETAIL_INTERIOR_FLOOR_Z,
        interior_ceiling_z=bounding_box.zmax - DOVETAIL_INTERIOR_CEILING_DROP_MM,
        wall_thickness_mm=wall_thickness_mm,
    )


def _raise_dovetail_floor(rendered_box, *, layout: DovetailLayout):
    import cadquery as cq

    bounding_box = rendered_box.val().BoundingBox()
    inset = layout.wall_thickness_mm + DOVETAIL_FLOOR_FILLET_RUN_MM
    width = bounding_box.xlen - 2.0 * inset
    depth = bounding_box.ylen - 2.0 * inset
    height = layout.interior_floor_z - DOVETAIL_UPSTREAM_FLOOR_Z
    if width <= 0 or depth <= 0 or height <= 0:
        return rendered_box
    floor = (
        cq.Workplane("XY")
        .rect(width, depth)
        .extrude(height)
        .translate((layout.center_x, layout.center_y, DOVETAIL_UPSTREAM_FLOOR_Z))
    )
    return rendered_box.union(floor).clean()


def _resolve_wrap_profile_bounds(rendered_box, *, layout: DovetailLayout):
    bounding_box = rendered_box.val().BoundingBox()
    if layout.slide_axis == "depth":
        cross_minimum = bounding_box.xmin + layout.wall_thickness_mm
        cross_maximum = bounding_box.xmax - layout.wall_thickness_mm
        slide_minimum = bounding_box.ymin + layout.wall_thickness_mm
        slide_maximum = bounding_box.ymax - layout.wall_thickness_mm
    else:
        cross_minimum = bounding_box.ymin + layout.wall_thickness_mm
        cross_maximum = bounding_box.ymax - layout.wall_thickness_mm
        slide_minimum = bounding_box.xmin + layout.wall_thickness_mm
        slide_maximum = bounding_box.xmax - layout.wall_thickness_mm

    inner_cross_span = cross_maximum - cross_minimum
    cross_scale = min(1.0, inner_cross_span / DOVETAIL_WRAP_REFERENCE_INNER_SPAN_MM)
    radius = min(
        DOVETAIL_WRAP_RADIUS_MM * cross_scale,
        layout.interior_ceiling_z - layout.interior_floor_z,
    )
    left_spring = cross_minimum + DOVETAIL_WRAP_LEFT_LEDGE_MM * cross_scale
    return (
        cross_minimum,
        cross_maximum,
        slide_minimum,
        slide_maximum,
        radius,
        left_spring,
        left_spring + 2.0 * radius,
    )


def _add_wrap_interior(rendered_box, *, layout: DovetailLayout):
    import cadquery as cq

    (
        cross_minimum,
        cross_maximum,
        slide_minimum,
        slide_maximum,
        radius,
        left_spring,
        right_spring,
    ) = _resolve_wrap_profile_bounds(rendered_box, layout=layout)
    if radius <= POSITION_TOLERANCE_MM:
        return rendered_box

    inner_cross_span = cross_maximum - cross_minimum
    center_cross = left_spring + radius
    center_z = layout.interior_floor_z + radius
    filler_bottom_z = DOVETAIL_UPSTREAM_FLOOR_Z
    filler_height = layout.interior_ceiling_z - filler_bottom_z
    slide_span = slide_maximum - slide_minimum

    if layout.slide_axis == "depth":
        filler = (
            cq.Workplane("XY")
            .box(inner_cross_span, slide_span, filler_height)
            .translate(
                (
                    (cross_minimum + cross_maximum) / 2.0,
                    (slide_minimum + slide_maximum) / 2.0,
                    filler_bottom_z + filler_height / 2.0,
                )
            )
        )
        trough_profile = (
            cq.Workplane("XZ")
            .moveTo(left_spring, layout.interior_ceiling_z + 1.0)
            .lineTo(left_spring, center_z)
            .threePointArc(
                (center_cross, layout.interior_floor_z),
                (right_spring, center_z),
            )
            .lineTo(right_spring, layout.interior_ceiling_z + 1.0)
            .close()
        )
        trough = trough_profile.extrude(slide_span / 2.0 + 1.0, both=True).translate(
            (0.0, (slide_minimum + slide_maximum) / 2.0, 0.0)
        )
    else:
        filler = (
            cq.Workplane("XY")
            .box(slide_span, inner_cross_span, filler_height)
            .translate(
                (
                    (slide_minimum + slide_maximum) / 2.0,
                    (cross_minimum + cross_maximum) / 2.0,
                    filler_bottom_z + filler_height / 2.0,
                )
            )
        )
        trough_profile = (
            cq.Workplane("YZ")
            .moveTo(left_spring, layout.interior_ceiling_z + 1.0)
            .lineTo(left_spring, center_z)
            .threePointArc(
                (center_cross, layout.interior_floor_z),
                (right_spring, center_z),
            )
            .lineTo(right_spring, layout.interior_ceiling_z + 1.0)
            .close()
        )
        trough = trough_profile.extrude(slide_span / 2.0 + 1.0, both=True).translate(
            ((slide_minimum + slide_maximum) / 2.0, 0.0, 0.0)
        )

    wrap_insert = filler.cut(trough)
    return rendered_box.union(wrap_insert).clean()


def _divider_cross_span(
    divider_spec: DividerSpec,
    *,
    position_divider: bool,
    axis_minimum: float,
    axis_maximum: float,
    wall_thickness_mm: float,
    divider_thickness_mm: float,
) -> tuple[float, float]:
    if position_divider:
        center = axis_minimum + wall_thickness_mm + divider_spec.position_u * GRID_UNIT_MM
        return center - divider_thickness_mm / 2.0, center + divider_thickness_mm / 2.0
    return _inner_unit_span_to_coordinates(
        span_start_u=divider_spec.span_start_u,
        span_end_u=divider_spec.span_end_u,
        minimum=axis_minimum,
        maximum=axis_maximum,
        wall_thickness_mm=wall_thickness_mm,
    )


def _validate_wrap_divider_visibility(
    rendered_box,
    *,
    layout: DovetailLayout,
    horizontal_specs: tuple[DividerSpec, ...],
    vertical_specs: tuple[DividerSpec, ...],
    divider_thickness_mm: float,
) -> None:
    bounding_box = rendered_box.val().BoundingBox()
    *_, radius, opening_minimum, opening_maximum = _resolve_wrap_profile_bounds(
        rendered_box,
        layout=layout,
    )
    if radius <= POSITION_TOLERANCE_MM:
        return

    if layout.slide_axis == "depth":
        axis_minimum, axis_maximum = bounding_box.xmin, bounding_box.xmax
        divider_groups = (
            ("horizontal", horizontal_specs, False),
            ("vertical", vertical_specs, True),
        )
    else:
        axis_minimum, axis_maximum = bounding_box.ymin, bounding_box.ymax
        divider_groups = (
            ("horizontal", horizontal_specs, True),
            ("vertical", vertical_specs, False),
        )

    for axis_name, divider_specs, position_divider in divider_groups:
        for divider_spec in divider_specs:
            span_minimum, span_maximum = _divider_cross_span(
                divider_spec,
                position_divider=position_divider,
                axis_minimum=axis_minimum,
                axis_maximum=axis_maximum,
                wall_thickness_mm=layout.wall_thickness_mm,
                divider_thickness_mm=divider_thickness_mm,
            )
            visible_overlap = min(span_maximum, opening_maximum) - max(
                span_minimum, opening_minimum
            )
            if visible_overlap <= POSITION_TOLERANCE_MM:
                raise ValueError(
                    f"wrap {axis_name} divider at {divider_spec.position_u:g}U is fully "
                    "embedded in the raised shelf and would add no visible material."
                )


def _validate_wrap_raised_floor_visibility(
    rendered_box,
    *,
    raised_floor_specs: tuple[RaisedFloorSpec, ...],
    wall_thickness_mm: float,
    floor_top_z: float,
) -> None:
    baseline_volume = rendered_box.val().Volume()
    for raised_floor_spec in raised_floor_specs:
        candidate = _apply_raised_floors(
            rendered_box,
            raised_floor_specs=(raised_floor_spec,),
            wall_thickness_mm=wall_thickness_mm,
            floor_top_z=floor_top_z,
        )
        if candidate.val().Volume() <= baseline_volume + DOVETAIL_VISIBLE_VOLUME_TOLERANCE_MM3:
            formatted_spec = _format_raised_floor_spec(raised_floor_spec)
            raise ValueError(
                f"wrap raised floor {formatted_spec} is fully embedded in the wrap shelf "
                "or interior and would add no visible material."
            )


def _validate_dovetail_raised_floors(
    *,
    raised_floor_specs: tuple[RaisedFloorSpec, ...],
    layout: DovetailLayout,
) -> None:
    maximum_height = layout.interior_ceiling_z - layout.interior_floor_z
    for raised_floor_spec in raised_floor_specs:
        if raised_floor_spec.height_mm > maximum_height + POSITION_TOLERANCE_MM:
            raise ValueError(
                "raised_floors height_mm exceeds the dovetail lid ceiling; "
                f"maximum is {maximum_height:g} mm."
            )


def _clear_dovetail_interior_headspace(rendered_box, *, layout: DovetailLayout):
    import cadquery as cq

    bounding_box = rendered_box.val().BoundingBox()
    width = bounding_box.xlen - 2.0 * layout.wall_thickness_mm
    depth = bounding_box.ylen - 2.0 * layout.wall_thickness_mm
    cutter_height = layout.box_top_z - layout.interior_ceiling_z + 1.0
    cutter = (
        cq.Workplane("XY")
        .box(width, depth, cutter_height)
        .translate(
            (
                layout.center_x,
                layout.center_y,
                layout.interior_ceiling_z + cutter_height / 2.0,
            )
        )
    )
    return rendered_box.cut(cutter).clean()


def _dovetail_panel(
    *,
    layout: DovetailLayout,
    length: float,
    bottom_width: float,
    height: float,
    bottom_z: float,
    slide_center: float,
    side_inset: float = DOVETAIL_SIDE_INSET_MM,
    front_inset: float = 0.0,
):
    import cadquery as cq

    panel = trapezoidal_panel(
        cq,
        length=length,
        bottom_width=bottom_width,
        height=height,
        side_inset=side_inset,
        extrusion_axis="y" if layout.slide_axis == "depth" else "x",
        front_inset=front_inset,
    )
    if layout.slide_axis == "depth":
        return panel.translate((layout.center_x, slide_center, bottom_z))
    return panel.translate((slide_center, layout.center_y, bottom_z))


def _add_dovetail_channels(rendered_box, layout: DovetailLayout):
    import cadquery as cq

    bounding_box = rendered_box.val().BoundingBox()
    top_z = layout.box_top_z
    side_shoulder_z = top_z - DOVETAIL_SIDE_SHOULDER_DROP_MM
    throat_top_z = top_z - DOVETAIL_LID_THICKNESS_MM
    front_shoulder_z = top_z - DOVETAIL_FRONT_SHOULDER_DROP_MM
    interior_reach = layout.wall_thickness_mm + 1.0

    if layout.slide_axis == "depth":
        cross_minimum, cross_maximum = bounding_box.xmin, bounding_box.xmax
        slide_minimum, slide_maximum = bounding_box.ymin, bounding_box.ymax
        side_plane = "XZ"
        end_plane = "YZ"
    else:
        cross_minimum, cross_maximum = bounding_box.ymin, bounding_box.ymax
        slide_minimum, slide_maximum = bounding_box.xmin, bounding_box.xmax
        side_plane = "YZ"
        end_plane = "XZ"

    left_boundary = cross_minimum + DOVETAIL_THROAT_MM
    right_boundary = cross_maximum - DOVETAIL_THROAT_MM
    left_points = (
        (left_boundary, side_shoulder_z),
        (left_boundary, throat_top_z),
        (left_boundary + DOVETAIL_CHANNEL_SLOPE_RUN_MM, top_z),
        (cross_minimum + interior_reach, top_z),
        (cross_minimum + interior_reach, side_shoulder_z),
    )
    right_points = (
        (cross_maximum - interior_reach, side_shoulder_z),
        (cross_maximum - interior_reach, top_z),
        (right_boundary - DOVETAIL_CHANNEL_SLOPE_RUN_MM, top_z),
        (right_boundary, throat_top_z),
        (right_boundary, side_shoulder_z),
    )
    slide_center = (slide_minimum + slide_maximum) / 2.0
    side_half_length = (slide_maximum - slide_minimum) / 2.0 + 1.0
    side_cutters = (
        cq.Workplane(side_plane)
        .polyline(left_points)
        .close()
        .extrude(side_half_length, both=True)
    ).union(
        cq.Workplane(side_plane)
        .polyline(right_points)
        .close()
        .extrude(side_half_length, both=True)
    )
    if layout.slide_axis == "depth":
        side_cutters = side_cutters.translate((0.0, slide_center, 0.0))
    else:
        side_cutters = side_cutters.translate((slide_center, 0.0, 0.0))

    front_boundary = slide_minimum + DOVETAIL_THROAT_MM
    front_points = (
        (front_boundary, front_shoulder_z),
        (front_boundary, throat_top_z),
        (front_boundary + DOVETAIL_CHANNEL_SLOPE_RUN_MM, top_z),
        (slide_minimum + interior_reach, top_z),
        (slide_minimum + interior_reach, front_shoulder_z),
    )
    front_half_length = (
        cross_maximum
        - cross_minimum
        - 2.0 * layout.wall_thickness_mm
        + 2.0 * DOVETAIL_BOOLEAN_OVERLAP_MM
    ) / 2.0
    front_cutter = (
        cq.Workplane(end_plane)
        .polyline(front_points)
        .close()
        .extrude(front_half_length, both=True)
    )
    if layout.slide_axis == "depth":
        front_cutter = front_cutter.translate((layout.center_x, 0.0, 0.0))
    else:
        front_cutter = front_cutter.translate((0.0, layout.center_y, 0.0))

    open_end_span = layout.wall_thickness_mm + 1.0
    open_end_height = top_z - side_shoulder_z + 1.0
    if layout.slide_axis == "depth":
        open_end_cutter = (
            cq.Workplane("XY")
            .box(
                cross_maximum - cross_minimum - 2.0 * layout.wall_thickness_mm,
                open_end_span,
                open_end_height,
            )
            .translate(
                (
                    layout.center_x,
                    slide_maximum - layout.wall_thickness_mm + open_end_span / 2.0,
                    side_shoulder_z + open_end_height / 2.0,
                )
            )
        )
    else:
        open_end_cutter = (
            cq.Workplane("XY")
            .box(
                open_end_span,
                cross_maximum - cross_minimum - 2.0 * layout.wall_thickness_mm,
                open_end_height,
            )
            .translate(
                (
                    slide_maximum - layout.wall_thickness_mm + open_end_span / 2.0,
                    layout.center_y,
                    side_shoulder_z + open_end_height / 2.0,
                )
            )
        )

    return rendered_box.cut(side_cutters.union(front_cutter).union(open_end_cutter)).clean()


def _build_dovetail_lid_blank(layout: DovetailLayout):
    return _dovetail_panel(
        layout=layout,
        length=layout.lid_length,
        bottom_width=layout.lid_bottom_width,
        height=DOVETAIL_LID_THICKNESS_MM,
        bottom_z=0.0,
        slide_center=layout.lid_slide_center,
        front_inset=DOVETAIL_SIDE_INSET_MM,
    )


def _build_dovetail_lid(layout: DovetailLayout, lid_style: str):
    lid = _build_dovetail_lid_blank(layout)
    opening = _dovetail_lid_opening(layout, lid_style)
    return lid.cut(opening).clean()


def _add_dovetail_lid_split_bars(
    rendered_lid,
    *,
    layout: DovetailLayout,
    reference_bounding_box,
    split_width_positions_u: tuple[float, ...],
    split_depth_positions_u: tuple[float, ...],
    unit_width: int,
    unit_depth: int,
):
    if not split_width_positions_u and not split_depth_positions_u:
        return rendered_lid

    import cadquery as cq

    lid_blank = _build_dovetail_lid_blank(layout)
    lid_box = lid_blank.val().BoundingBox()
    bands = None
    for split_coordinate in _axis_split_coordinates(
        minimum=reference_bounding_box.xmin,
        maximum=reference_bounding_box.xmax,
        unit_count=unit_width,
        split_positions_u=split_width_positions_u,
    ):
        band = (
            cq.Workplane("XY")
            .box(
                DOVETAIL_LID_SPLIT_BAR_MM,
                lid_box.ylen + 2.0,
                lid_box.zlen + 2.0,
            )
            .translate((split_coordinate, layout.center_y, lid_box.zmin + lid_box.zlen / 2.0))
        )
        bands = band if bands is None else bands.union(band)
    for split_coordinate in _axis_split_coordinates(
        minimum=reference_bounding_box.ymin,
        maximum=reference_bounding_box.ymax,
        unit_count=unit_depth,
        split_positions_u=split_depth_positions_u,
    ):
        band = (
            cq.Workplane("XY")
            .box(
                lid_box.xlen + 2.0,
                DOVETAIL_LID_SPLIT_BAR_MM,
                lid_box.zlen + 2.0,
            )
            .translate((layout.center_x, split_coordinate, lid_box.zmin + lid_box.zlen / 2.0))
        )
        bands = band if bands is None else bands.union(band)

    if bands is None:
        return rendered_lid
    split_bars = lid_blank.intersect(bands)
    return rendered_lid.union(split_bars).clean()


def _dovetail_lid_opening(layout: DovetailLayout, lid_style: str):
    import cadquery as cq

    top_width = layout.lid_bottom_width - 2.0 * DOVETAIL_SIDE_INSET_MM
    cross_left = -top_width / 2.0 + min(
        DOVETAIL_REFERENCE_OPENING_OFFSET_MM,
        max(DOVETAIL_OPENING_SIDE_MARGIN_MM, top_width * 0.156),
    )
    cross_limit = top_width / 2.0 - DOVETAIL_OPENING_SIDE_MARGIN_MM
    available_opening_width = cross_limit - cross_left
    reference_total_width = (
        DOVETAIL_REFERENCE_NARROW_OPENING_MM + DOVETAIL_REFERENCE_ZIPLOCK_BULGE_MM
    )
    opening_scale = min(1.0, available_opening_width / reference_total_width)
    narrow_opening_width = DOVETAIL_REFERENCE_NARROW_OPENING_MM * opening_scale
    ziplock_bulge = DOVETAIL_REFERENCE_ZIPLOCK_BULGE_MM * opening_scale
    cross_right = cross_left + narrow_opening_width
    slide_minimum = -layout.lid_length / 2.0 + DOVETAIL_OPENING_END_MARGIN_MM
    slide_maximum = layout.lid_length / 2.0 - DOVETAIL_OPENING_END_MARGIN_MM
    if narrow_opening_width < 2.0 or slide_maximum - slide_minimum < 2.0:
        raise ValueError("Gridfinity footprint is too small for the selected lid opening.")

    if lid_style == "wrap":
        local_points = (
            (cross_left, slide_minimum),
            (cross_right, slide_minimum),
            (cross_right, slide_maximum),
            (cross_left, slide_maximum),
        )
    else:
        wide_right = min(cross_right + ziplock_bulge, cross_limit)
        slide_middle = (slide_minimum + slide_maximum) / 2.0
        local_points = (
            (cross_left, slide_minimum),
            (cross_right, slide_minimum),
            (wide_right, slide_middle),
            (cross_right, slide_maximum),
            (cross_left, slide_maximum),
        )

    if layout.slide_axis == "depth":
        points = tuple(
            (layout.center_x + cross, layout.lid_slide_center + slide)
            for cross, slide in local_points
        )
    else:
        points = tuple(
            (layout.lid_slide_center + slide, layout.center_y + cross)
            for cross, slide in local_points
        )
    return (
        cq.Workplane("XY")
        .polyline(points)
        .close()
        .extrude(DOVETAIL_LID_THICKNESS_MM + 2.0)
        .translate((0.0, 0.0, -1.0))
    )


def _inner_size(unit_count: int, wall_thickness_mm: float) -> float:
    from cqgridfinity import GR_TOL

    return unit_count * GRID_UNIT_MM - GR_TOL - 2 * wall_thickness_mm


def _resolve_raised_floor_specs(
    *,
    raw_specs: str | Sequence[RaisedFloorSpec],
    unit_width: int,
    unit_depth: int,
) -> tuple[RaisedFloorSpec, ...]:
    if isinstance(raw_specs, str):
        stripped_specs = raw_specs.strip()
        if not stripped_specs:
            return ()

        raised_floor_specs = []
        for raw_spec in stripped_specs.split(","):
            stripped_spec = raw_spec.strip()
            if not stripped_spec:
                raise ValueError("raised_floors contains an empty raised floor spec.")
            raised_floor_specs.append(_parse_raised_floor_spec(stripped_spec))
    elif isinstance(raw_specs, Iterable):
        raised_floor_specs = list(raw_specs)
    else:
        raise ValueError("raised_floors must be a comma-separated string or a sequence.")

    resolved_specs = tuple(raised_floor_specs)
    _validate_raised_floor_specs(
        raised_floor_specs=resolved_specs,
        unit_width=unit_width,
        unit_depth=unit_depth,
    )
    return resolved_specs


def _parse_raised_floor_spec(raw_spec: str) -> RaisedFloorSpec:
    raw_footprint, height_separator, raw_height = raw_spec.partition(":")
    if not height_separator:
        raise ValueError(
            f"raised_floors spec {raw_spec!r} must use x_start-x_end@y_start-y_end:height_mm."
        )

    raw_x_span, footprint_separator, raw_y_span = raw_footprint.partition("@")
    if not footprint_separator:
        raise ValueError(
            f"raised_floors spec {raw_spec!r} must use x_start-x_end@y_start-y_end:height_mm."
        )

    x_start_u, x_end_u = _parse_unit_span("raised_floors x span", raw_x_span)
    y_start_u, y_end_u = _parse_unit_span("raised_floors y span", raw_y_span)
    return RaisedFloorSpec(
        x_start_u=x_start_u,
        x_end_u=x_end_u,
        y_start_u=y_start_u,
        y_end_u=y_end_u,
        height_mm=float(raw_height.strip()),
    )


def _parse_unit_span(parameter_name: str, raw_span: str) -> tuple[float, float]:
    raw_start, span_separator, raw_end = raw_span.partition("-")
    if not span_separator:
        raise ValueError(f"{parameter_name} must use start-end syntax.")

    stripped_start = raw_start.strip()
    stripped_end = raw_end.strip()
    if not stripped_start or not stripped_end:
        raise ValueError(f"{parameter_name} contains an empty span bound.")

    return float(stripped_start), float(stripped_end)


def _validate_raised_floor_specs(
    *,
    raised_floor_specs: tuple[RaisedFloorSpec, ...],
    unit_width: int,
    unit_depth: int,
) -> None:
    for raised_floor_spec in raised_floor_specs:
        if raised_floor_spec.x_start_u < 0 or raised_floor_spec.x_end_u > unit_width:
            raise ValueError(
                f"raised_floors x span {raised_floor_spec.x_start_u:g}-"
                f"{raised_floor_spec.x_end_u:g}U is outside 0-{unit_width:g}U."
            )
        if raised_floor_spec.y_start_u < 0 or raised_floor_spec.y_end_u > unit_depth:
            raise ValueError(
                f"raised_floors y span {raised_floor_spec.y_start_u:g}-"
                f"{raised_floor_spec.y_end_u:g}U is outside 0-{unit_depth:g}U."
            )
        if raised_floor_spec.x_start_u >= raised_floor_spec.x_end_u:
            raise ValueError("raised_floors x span must have a start less than its end.")
        if raised_floor_spec.y_start_u >= raised_floor_spec.y_end_u:
            raise ValueError("raised_floors y span must have a start less than its end.")
        _validate_positive("raised_floors height_mm", raised_floor_spec.height_mm)


def _apply_raised_floors(
    rendered_box,
    *,
    raised_floor_specs: tuple[RaisedFloorSpec, ...],
    wall_thickness_mm: float,
    floor_top_z: float | None = None,
):
    if not raised_floor_specs:
        return rendered_box

    import cadquery as cq

    if floor_top_z is None:
        from cqgridfinity import GR_BASE_HEIGHT, GR_FLOOR

        floor_top_z = GR_BASE_HEIGHT + GR_FLOOR
    bounding_box = rendered_box.val().BoundingBox()
    result = rendered_box

    for raised_floor_spec in raised_floor_specs:
        x_minimum, x_maximum = _inner_unit_span_to_coordinates(
            span_start_u=raised_floor_spec.x_start_u,
            span_end_u=raised_floor_spec.x_end_u,
            minimum=bounding_box.xmin,
            maximum=bounding_box.xmax,
            wall_thickness_mm=wall_thickness_mm,
        )
        y_minimum, y_maximum = _inner_unit_span_to_coordinates(
            span_start_u=raised_floor_spec.y_start_u,
            span_end_u=raised_floor_spec.y_end_u,
            minimum=bounding_box.ymin,
            maximum=bounding_box.ymax,
            wall_thickness_mm=wall_thickness_mm,
        )
        raised_floor = (
            cq.Workplane("XY")
            .rect(x_maximum - x_minimum, y_maximum - y_minimum)
            .extrude(raised_floor_spec.height_mm)
            .translate(
                (
                    x_minimum + (x_maximum - x_minimum) / 2.0,
                    y_minimum + (y_maximum - y_minimum) / 2.0,
                    floor_top_z,
                )
            )
        )
        result = result.union(raised_floor)

    return result


def _inner_unit_span_to_coordinates(
    *,
    span_start_u: float,
    span_end_u: float,
    minimum: float,
    maximum: float,
    wall_thickness_mm: float,
) -> tuple[float, float]:
    inner_minimum = minimum + wall_thickness_mm
    inner_maximum = maximum - wall_thickness_mm
    return (
        inner_minimum + span_start_u * GRID_UNIT_MM,
        min(inner_minimum + span_end_u * GRID_UNIT_MM, inner_maximum),
    )


def _has_partial_dividers(
    *,
    horizontal_specs: tuple[DividerSpec, ...],
    vertical_specs: tuple[DividerSpec, ...],
    unit_width: int,
    unit_depth: int,
) -> bool:
    return any(
        not _is_full_span(divider_spec, unit_width) for divider_spec in horizontal_specs
    ) or any(not _is_full_span(divider_spec, unit_depth) for divider_spec in vertical_specs)


def _is_full_span(divider_spec: DividerSpec, full_span_axis_units: int) -> bool:
    return divider_spec.span_start_u == 0 and divider_spec.span_end_u == full_span_axis_units


def _resolve_divider_specs(
    *,
    axis_name: str,
    position_axis_size_mm: float,
    span_axis_units: int,
    divider_thickness_mm: float,
    raw_specs: str | Sequence[float],
) -> tuple[DividerSpec, ...]:
    parameter_name = f"{axis_name}_dividers"
    divider_specs = tuple(
        sorted(
            _parse_divider_specs(parameter_name, raw_specs, span_axis_units),
            key=lambda spec: (spec.position_u, spec.span_start_u, spec.span_end_u),
        )
    )
    _validate_divider_specs(
        axis_name=axis_name,
        position_axis_size_mm=position_axis_size_mm,
        span_axis_units=span_axis_units,
        divider_thickness_mm=divider_thickness_mm,
        divider_specs=divider_specs,
    )
    return divider_specs


def _parse_divider_specs(
    parameter_name: str,
    raw_specs: str | Sequence[float],
    full_span_axis_units: int,
) -> tuple[DividerSpec, ...]:
    if isinstance(raw_specs, str):
        stripped_specs = raw_specs.strip()
        if not stripped_specs:
            return ()

        divider_specs = []
        for raw_spec in stripped_specs.split(","):
            stripped_spec = raw_spec.strip()
            if not stripped_spec:
                raise ValueError(f"{parameter_name} contains an empty divider spec.")
            divider_specs.append(
                _parse_divider_spec(parameter_name, stripped_spec, full_span_axis_units)
            )
        return tuple(divider_specs)

    if isinstance(raw_specs, Iterable):
        return tuple(
            DividerSpec(
                position_u=float(position_u),
                span_start_u=0.0,
                span_end_u=float(full_span_axis_units),
            )
            for position_u in raw_specs
        )

    raise ValueError(f"{parameter_name} must be a comma-separated string or a sequence.")


def _parse_divider_spec(
    parameter_name: str,
    raw_spec: str,
    full_span_axis_units: int,
) -> DividerSpec:
    raw_position, span_separator, raw_span = raw_spec.partition("@")
    stripped_position = raw_position.strip()
    if not stripped_position:
        raise ValueError(f"{parameter_name} contains a divider spec without a position.")

    if not span_separator:
        return DividerSpec(
            position_u=float(stripped_position),
            span_start_u=0.0,
            span_end_u=float(full_span_axis_units),
        )

    raw_span_start, range_separator, raw_span_end = raw_span.partition("-")
    if not range_separator:
        raise ValueError(
            f"{parameter_name} divider spec {raw_spec!r} must use span_start-span_end "
            "after '@'."
        )

    stripped_span_start = raw_span_start.strip()
    stripped_span_end = raw_span_end.strip()
    if not stripped_span_start or not stripped_span_end:
        raise ValueError(f"{parameter_name} divider spec {raw_spec!r} has an empty span bound.")

    return DividerSpec(
        position_u=float(stripped_position),
        span_start_u=float(stripped_span_start),
        span_end_u=float(stripped_span_end),
    )


def _named_export_parts(
    parts: dict[str, object],
    *,
    unit_width: int,
    unit_depth: int,
    unit_height: int,
    horizontal_specs: tuple[DividerSpec, ...],
    vertical_specs: tuple[DividerSpec, ...],
    split_width_positions_u: tuple[float, ...],
    split_depth_positions_u: tuple[float, ...],
    raised_floor_specs: tuple[RaisedFloorSpec, ...],
    scoops: bool,
) -> dict[str, object]:
    base_name = _export_base_name(
        unit_width=unit_width,
        unit_depth=unit_depth,
        unit_height=unit_height,
        horizontal_specs=horizontal_specs,
        vertical_specs=vertical_specs,
        split_width_positions_u=split_width_positions_u,
        split_depth_positions_u=split_depth_positions_u,
        raised_floor_specs=raised_floor_specs,
        scoops=scoops,
    )

    if set(parts) == {"whole"}:
        return {base_name: parts["whole"]}

    return {f"{base_name}_{part_name}": part for part_name, part in parts.items()}


def _named_dovetail_export_parts(
    box_parts: dict[str, object],
    lid_parts: dict[str, object],
    *,
    lid_style: str,
    unit_width: int,
    unit_depth: int,
    unit_height: int,
    horizontal_specs: tuple[DividerSpec, ...],
    vertical_specs: tuple[DividerSpec, ...],
    split_width_positions_u: tuple[float, ...],
    split_depth_positions_u: tuple[float, ...],
    raised_floor_specs: tuple[RaisedFloorSpec, ...],
    scoops: bool,
) -> dict[str, object]:
    base_name = _export_base_name(
        unit_width=unit_width,
        unit_depth=unit_depth,
        unit_height=unit_height,
        horizontal_specs=horizontal_specs,
        vertical_specs=vertical_specs,
        split_width_positions_u=split_width_positions_u,
        split_depth_positions_u=split_depth_positions_u,
        raised_floor_specs=raised_floor_specs,
        scoops=scoops,
    )
    named_parts = {}
    for part_kind, parts in (("box", box_parts), ("lid", lid_parts)):
        part_base_name = f"{base_name}_dovetail_{lid_style}_{part_kind}"
        if set(parts) == {"whole"}:
            named_parts[part_base_name] = parts["whole"]
        else:
            named_parts.update(
                {f"{part_base_name}_{part_name}": part for part_name, part in parts.items()}
            )
    return named_parts


def _export_base_name(
    *,
    unit_width: int,
    unit_depth: int,
    unit_height: int,
    horizontal_specs: tuple[DividerSpec, ...],
    vertical_specs: tuple[DividerSpec, ...],
    split_width_positions_u: tuple[float, ...],
    split_depth_positions_u: tuple[float, ...],
    raised_floor_specs: tuple[RaisedFloorSpec, ...],
    scoops: bool,
) -> str:
    name_parts = [f"{unit_width}x{unit_depth}x{unit_height}u"]

    if horizontal_specs:
        horizontal_label = _format_divider_specs(horizontal_specs, unit_width)
        name_parts.append(f"horizontal_dividers_{horizontal_label}u")
    if vertical_specs:
        vertical_label = _format_divider_specs(vertical_specs, unit_depth)
        name_parts.append(f"vertical_dividers_{vertical_label}u")
    if split_width_positions_u:
        name_parts.append(f"split_width_{_format_positions(split_width_positions_u)}u")
    if split_depth_positions_u:
        name_parts.append(f"split_depth_{_format_positions(split_depth_positions_u)}u")
    if raised_floor_specs:
        name_parts.append(f"raised_floors_{_format_raised_floor_specs(raised_floor_specs)}")
    if scoops:
        name_parts.append("scoops")

    return "_".join(name_parts)


def _format_divider_specs(
    divider_specs: tuple[DividerSpec, ...], full_span_axis_units: int
) -> str:
    return "_".join(
        _format_divider_spec(divider_spec, full_span_axis_units)
        for divider_spec in divider_specs
    )


def _format_divider_spec(divider_spec: DividerSpec, full_span_axis_units: int) -> str:
    position = _format_decimal(divider_spec.position_u)
    if _is_full_span(divider_spec, full_span_axis_units):
        return position

    span_start = _format_decimal(divider_spec.span_start_u)
    span_end = _format_decimal(divider_spec.span_end_u)
    return f"{position}at{span_start}to{span_end}"


def _format_raised_floor_specs(raised_floor_specs: tuple[RaisedFloorSpec, ...]) -> str:
    return "_".join(_format_raised_floor_spec(spec) for spec in raised_floor_specs)


def _format_raised_floor_spec(raised_floor_spec: RaisedFloorSpec) -> str:
    x_start = _format_decimal(raised_floor_spec.x_start_u)
    x_end = _format_decimal(raised_floor_spec.x_end_u)
    y_start = _format_decimal(raised_floor_spec.y_start_u)
    y_end = _format_decimal(raised_floor_spec.y_end_u)
    height = _format_decimal(raised_floor_spec.height_mm)
    return f"x{x_start}to{x_end}_y{y_start}to{y_end}_{height}mm"


def _format_positions(positions: tuple[float, ...]) -> str:
    return "_".join(_format_decimal(position) for position in positions)


def _format_decimal(value: float) -> str:
    return f"{value:g}".replace(".", "p")


def _resolve_split_positions(
    *,
    axis_name: str,
    unit_count: int,
    unit_positions: str | Sequence[float],
) -> tuple[float, ...]:
    parameter_name = "split_width_u" if axis_name == "width" else "split_depth"
    positions = tuple(sorted(_parse_position_list(parameter_name, unit_positions)))
    _validate_split_positions(
        parameter_name=parameter_name,
        unit_count=unit_count,
        positions_u=positions,
    )
    return positions


def _resolve_print_bed_splits(
    rendered_box,
    *,
    split_width_positions_u: tuple[float, ...],
    split_depth_positions_u: tuple[float, ...],
    unit_width: int,
    unit_depth: int,
    auto_split: bool,
    max_print_width: float,
    max_print_depth: float,
    allow_rotation: bool,
    companion_rendered=None,
) -> tuple[tuple[float, ...], tuple[float, ...]]:
    if not auto_split:
        return split_width_positions_u, split_depth_positions_u

    bounding_box = rendered_box.val().BoundingBox()
    width_candidates = (
        (split_width_positions_u,)
        if split_width_positions_u
        else _automatic_split_candidates(unit_width)
    )
    depth_candidates = (
        (split_depth_positions_u,)
        if split_depth_positions_u
        else _automatic_split_candidates(unit_depth)
    )

    best: tuple[tuple[float, ...], tuple[float, ...], tuple[float, ...]] | None = None
    for width_positions in width_candidates:
        width_segments = _axis_segments(
            minimum=bounding_box.xmin,
            maximum=bounding_box.xmax,
            unit_count=unit_width,
            split_positions_u=width_positions,
        )
        for depth_positions in depth_candidates:
            depth_segments = _axis_segments(
                minimum=bounding_box.ymin,
                maximum=bounding_box.ymax,
                unit_count=unit_depth,
                split_positions_u=depth_positions,
            )
            if not _segments_fit_print_bed(
                width_segments=width_segments,
                depth_segments=depth_segments,
                max_print_width=max_print_width,
                max_print_depth=max_print_depth,
                allow_rotation=allow_rotation,
            ):
                continue
            if companion_rendered is not None:
                companion_box = companion_rendered.val().BoundingBox()
                companion_width_segments = _clip_axis_segments(
                    width_segments,
                    minimum=companion_box.xmin,
                    maximum=companion_box.xmax,
                )
                companion_depth_segments = _clip_axis_segments(
                    depth_segments,
                    minimum=companion_box.ymin,
                    maximum=companion_box.ymax,
                )
                if not companion_width_segments or not companion_depth_segments:
                    continue
                if not _segments_fit_print_bed(
                    width_segments=companion_width_segments,
                    depth_segments=companion_depth_segments,
                    max_print_width=max_print_width,
                    max_print_depth=max_print_depth,
                    allow_rotation=allow_rotation,
                ):
                    continue

            width_sizes = tuple(maximum - minimum for minimum, maximum in width_segments)
            depth_sizes = tuple(maximum - minimum for minimum, maximum in depth_segments)
            score = (
                len(width_segments) * len(depth_segments),
                abs(len(width_segments) - len(depth_segments)),
                max(width_sizes) - min(width_sizes) + max(depth_sizes) - min(depth_sizes),
                max(width_sizes) * max(depth_sizes),
            )
            if best is None or score < best[2]:
                best = (width_positions, depth_positions, score)

    if best is None:
        raise ValueError(
            "Could not split the Gridfinity box into parts that fit the print area of "
            f"{max_print_width:g} x {max_print_depth:g} mm."
        )

    return best[0], best[1]


def _segments_fit_print_bed(
    *,
    width_segments: tuple[tuple[float, float], ...],
    depth_segments: tuple[tuple[float, float], ...],
    max_print_width: float,
    max_print_depth: float,
    allow_rotation: bool,
) -> bool:
    return all(
        _tile_fits(
            width_maximum - width_minimum,
            depth_maximum - depth_minimum,
            max_print_width,
            max_print_depth,
            allow_rotation,
        )
        for width_minimum, width_maximum in width_segments
        for depth_minimum, depth_maximum in depth_segments
    )


def _clip_axis_segments(
    segments: tuple[tuple[float, float], ...],
    *,
    minimum: float,
    maximum: float,
) -> tuple[tuple[float, float], ...]:
    clipped_segments = tuple(
        (max(segment_minimum, minimum), min(segment_maximum, maximum))
        for segment_minimum, segment_maximum in segments
    )
    if any(
        segment_maximum - segment_minimum <= POSITION_TOLERANCE_MM
        for segment_minimum, segment_maximum in clipped_segments
    ):
        return ()
    return clipped_segments


def _automatic_split_candidates(unit_count: int) -> tuple[tuple[float, ...], ...]:
    candidates = []
    for part_count in range(1, unit_count + 1):
        cell_count = unit_count // part_count
        extra_cells = unit_count % part_count
        positions = []
        position = 0
        for index in range(part_count - 1):
            position += cell_count + (1 if index < extra_cells else 0)
            positions.append(float(position))
        candidates.append(tuple(positions))
    return tuple(candidates)


def _tile_fits(
    width: float,
    depth: float,
    max_print_width: float,
    max_print_depth: float,
    allow_rotation: bool,
) -> bool:
    fits = width <= max_print_width and depth <= max_print_depth
    rotated_fits = allow_rotation and width <= max_print_depth and depth <= max_print_width
    return fits or rotated_fits


def _split_rendered_box(
    rendered_box,
    *,
    split_width_positions_u: tuple[float, ...],
    split_depth_positions_u: tuple[float, ...],
    unit_width: int,
    unit_depth: int,
    unit_height: int,
    horizontal_specs: tuple[DividerSpec, ...],
    vertical_specs: tuple[DividerSpec, ...],
    wall_thickness_mm: float,
    divider_thickness_mm: float,
    breakaway_brace_top_z: float,
):
    if not split_width_positions_u and not split_depth_positions_u:
        return {"whole": rendered_box}

    import cadquery as cq

    bounding_box = rendered_box.val().BoundingBox()
    width_segments = _axis_segments(
        minimum=bounding_box.xmin,
        maximum=bounding_box.xmax,
        unit_count=unit_width,
        split_positions_u=split_width_positions_u,
    )
    depth_segments = _axis_segments(
        minimum=bounding_box.ymin,
        maximum=bounding_box.ymax,
        unit_count=unit_depth,
        split_positions_u=split_depth_positions_u,
    )
    width_boundaries_u = (0.0, *split_width_positions_u, float(unit_width))
    depth_boundaries_u = (0.0, *split_depth_positions_u, float(unit_depth))
    if unit_height <= BREAKAWAY_MAX_UNBRACED_HEIGHT_U:
        width_braces = _empty_segment_breakaway_braces(split_width_positions_u)
        depth_braces = _empty_segment_breakaway_braces(split_depth_positions_u)
    else:
        width_braces = _resolve_segment_breakaway_braces(
            unit_count=unit_width,
            split_positions_u=split_width_positions_u,
            parallel_divider_specs=vertical_specs,
            divider_full_span_axis_units=unit_depth,
        )
        depth_braces = _resolve_segment_breakaway_braces(
            unit_count=unit_depth,
            split_positions_u=split_depth_positions_u,
            parallel_divider_specs=horizontal_specs,
            divider_full_span_axis_units=unit_width,
        )

    padding_mm = 2.0
    z_size = bounding_box.zlen + 2 * padding_mm
    z_center = bounding_box.zmin + bounding_box.zlen / 2.0
    parts = {}

    for width_index, width_segment in enumerate(width_segments, start=1):
        width_minimum, width_maximum = width_segment
        width_minimum_u = width_boundaries_u[width_index - 1]
        width_maximum_u = width_boundaries_u[width_index]
        width_brace_sides = width_braces[width_index - 1]
        for depth_index, depth_segment in enumerate(depth_segments, start=1):
            depth_minimum, depth_maximum = depth_segment
            depth_minimum_u = depth_boundaries_u[depth_index - 1]
            depth_maximum_u = depth_boundaries_u[depth_index]
            depth_brace_sides = depth_braces[depth_index - 1]
            cutter = (
                cq.Workplane("XY")
                .box(
                    width_maximum - width_minimum,
                    depth_maximum - depth_minimum,
                    z_size,
                )
                .translate(
                    (
                        width_minimum + (width_maximum - width_minimum) / 2.0,
                        depth_minimum + (depth_maximum - depth_minimum) / 2.0,
                        z_center,
                    )
                )
            )
            part = rendered_box.intersect(cutter)
            if width_brace_sides.minimum_side:
                part = _add_breakaway_brace_lattice(
                    part,
                    split_axis="width",
                    split_coordinate=width_minimum,
                    inside_direction=1,
                    span_minimum=depth_minimum,
                    span_maximum=depth_maximum,
                    divider_center_coordinates=_crossing_divider_coordinates(
                        split_position_u=width_minimum_u,
                        perpendicular_divider_specs=horizontal_specs,
                        position_axis_minimum=bounding_box.ymin,
                        segment_span_minimum=depth_minimum,
                        segment_span_maximum=depth_maximum,
                        wall_thickness_mm=wall_thickness_mm,
                    ),
                    divider_thickness_mm=divider_thickness_mm,
                    brace_top_z=breakaway_brace_top_z,
                )
            if width_brace_sides.maximum_side:
                part = _add_breakaway_brace_lattice(
                    part,
                    split_axis="width",
                    split_coordinate=width_maximum,
                    inside_direction=-1,
                    span_minimum=depth_minimum,
                    span_maximum=depth_maximum,
                    divider_center_coordinates=_crossing_divider_coordinates(
                        split_position_u=width_maximum_u,
                        perpendicular_divider_specs=horizontal_specs,
                        position_axis_minimum=bounding_box.ymin,
                        segment_span_minimum=depth_minimum,
                        segment_span_maximum=depth_maximum,
                        wall_thickness_mm=wall_thickness_mm,
                    ),
                    divider_thickness_mm=divider_thickness_mm,
                    brace_top_z=breakaway_brace_top_z,
                )
            if depth_brace_sides.minimum_side:
                part = _add_breakaway_brace_lattice(
                    part,
                    split_axis="depth",
                    split_coordinate=depth_minimum,
                    inside_direction=1,
                    span_minimum=width_minimum,
                    span_maximum=width_maximum,
                    divider_center_coordinates=_crossing_divider_coordinates(
                        split_position_u=depth_minimum_u,
                        perpendicular_divider_specs=vertical_specs,
                        position_axis_minimum=bounding_box.xmin,
                        segment_span_minimum=width_minimum,
                        segment_span_maximum=width_maximum,
                        wall_thickness_mm=wall_thickness_mm,
                    ),
                    divider_thickness_mm=divider_thickness_mm,
                    brace_top_z=breakaway_brace_top_z,
                )
            if depth_brace_sides.maximum_side:
                part = _add_breakaway_brace_lattice(
                    part,
                    split_axis="depth",
                    split_coordinate=depth_maximum,
                    inside_direction=-1,
                    span_minimum=width_minimum,
                    span_maximum=width_maximum,
                    divider_center_coordinates=_crossing_divider_coordinates(
                        split_position_u=depth_maximum_u,
                        perpendicular_divider_specs=vertical_specs,
                        position_axis_minimum=bounding_box.xmin,
                        segment_span_minimum=width_minimum,
                        segment_span_maximum=width_maximum,
                        wall_thickness_mm=wall_thickness_mm,
                    ),
                    divider_thickness_mm=divider_thickness_mm,
                    brace_top_z=breakaway_brace_top_z,
                )

            part_name = _split_part_name(
                width_index=width_index,
                width_count=len(width_segments),
                depth_index=depth_index,
                depth_count=len(depth_segments),
            )
            parts[part_name] = part

    return parts


def _split_rendered_lid(
    rendered_lid,
    *,
    reference_bounding_box,
    split_width_positions_u: tuple[float, ...],
    split_depth_positions_u: tuple[float, ...],
    unit_width: int,
    unit_depth: int,
):
    if not split_width_positions_u and not split_depth_positions_u:
        return {"whole": rendered_lid}

    import cadquery as cq

    bounding_box = rendered_lid.val().BoundingBox()
    width_segments = _axis_segments(
        minimum=reference_bounding_box.xmin,
        maximum=reference_bounding_box.xmax,
        unit_count=unit_width,
        split_positions_u=split_width_positions_u,
    )
    depth_segments = _axis_segments(
        minimum=reference_bounding_box.ymin,
        maximum=reference_bounding_box.ymax,
        unit_count=unit_depth,
        split_positions_u=split_depth_positions_u,
    )
    z_padding = 1.0
    parts = {}
    for width_index, (width_minimum, width_maximum) in enumerate(width_segments, start=1):
        for depth_index, (depth_minimum, depth_maximum) in enumerate(
            depth_segments,
            start=1,
        ):
            cutter = (
                cq.Workplane("XY")
                .box(
                    width_maximum - width_minimum,
                    depth_maximum - depth_minimum,
                    bounding_box.zlen + 2.0 * z_padding,
                )
                .translate(
                    (
                        (width_minimum + width_maximum) / 2.0,
                        (depth_minimum + depth_maximum) / 2.0,
                        bounding_box.zmin + bounding_box.zlen / 2.0,
                    )
                )
            )
            part_name = _split_part_name(
                width_index=width_index,
                width_count=len(width_segments),
                depth_index=depth_index,
                depth_count=len(depth_segments),
            )
            part = rendered_lid.intersect(cutter)
            if not part.solids().vals():
                raise ValueError(
                    f"Gridfinity lid split {part_name} does not intersect the lid. "
                    "Move the split position farther from the footprint edge."
                )
            parts[part_name] = part
    return parts


def _crossing_divider_coordinates(
    *,
    split_position_u: float,
    perpendicular_divider_specs: tuple[DividerSpec, ...],
    position_axis_minimum: float,
    segment_span_minimum: float,
    segment_span_maximum: float,
    wall_thickness_mm: float,
) -> tuple[float, ...]:
    tolerance_u = POSITION_TOLERANCE_MM / GRID_UNIT_MM
    coordinates = {
        position_axis_minimum
        + wall_thickness_mm
        + divider_spec.position_u * GRID_UNIT_MM
        for divider_spec in perpendicular_divider_specs
        if divider_spec.span_start_u - tolerance_u
        <= split_position_u
        <= divider_spec.span_end_u + tolerance_u
    }
    return tuple(
        coordinate
        for coordinate in sorted(coordinates)
        if segment_span_minimum - POSITION_TOLERANCE_MM
        <= coordinate
        <= segment_span_maximum + POSITION_TOLERANCE_MM
    )


def _empty_segment_breakaway_braces(
    split_positions_u: tuple[float, ...],
) -> tuple[SegmentBreakawayBraces, ...]:
    return tuple(
        SegmentBreakawayBraces(minimum_side=False, maximum_side=False)
        for _ in range(len(split_positions_u) + 1)
    )


def _resolve_segment_breakaway_braces(
    *,
    unit_count: int,
    split_positions_u: tuple[float, ...],
    parallel_divider_specs: tuple[DividerSpec, ...],
    divider_full_span_axis_units: int,
) -> tuple[SegmentBreakawayBraces, ...]:
    unit_boundaries = (0.0, *split_positions_u, float(unit_count))
    segment_count = len(unit_boundaries) - 1
    segment_braces = []

    for segment_index, (segment_minimum_u, segment_maximum_u) in enumerate(
        zip(unit_boundaries, unit_boundaries[1:], strict=False)
    ):
        minimum_side = segment_index > 0 and not _has_nearby_supporting_divider(
            split_position_u=segment_minimum_u,
            segment_minimum_u=segment_minimum_u,
            segment_maximum_u=segment_maximum_u,
            parallel_divider_specs=parallel_divider_specs,
            divider_full_span_axis_units=divider_full_span_axis_units,
        )
        maximum_side = segment_index < segment_count - 1 and not _has_nearby_supporting_divider(
            split_position_u=segment_maximum_u,
            segment_minimum_u=segment_minimum_u,
            segment_maximum_u=segment_maximum_u,
            parallel_divider_specs=parallel_divider_specs,
            divider_full_span_axis_units=divider_full_span_axis_units,
        )
        segment_braces.append(
            SegmentBreakawayBraces(
                minimum_side=minimum_side,
                maximum_side=maximum_side,
            )
        )

    return tuple(segment_braces)


def _has_nearby_supporting_divider(
    *,
    split_position_u: float,
    segment_minimum_u: float,
    segment_maximum_u: float,
    parallel_divider_specs: tuple[DividerSpec, ...],
    divider_full_span_axis_units: int,
) -> bool:
    tolerance_u = POSITION_TOLERANCE_MM / GRID_UNIT_MM
    return any(
        _is_full_span(divider_spec, divider_full_span_axis_units)
        and segment_minimum_u - tolerance_u
        <= divider_spec.position_u
        <= segment_maximum_u + tolerance_u
        and abs(divider_spec.position_u - split_position_u)
        <= BREAKAWAY_DIVIDER_DISTANCE_U + tolerance_u
        for divider_spec in parallel_divider_specs
    )


def _breakaway_brace_profile() -> BreakawayBraceProfile:
    return BreakawayBraceProfile(
        thickness_mm=BREAKAWAY_BRACE_THICKNESS_MM,
        crossbar_height_mm=BREAKAWAY_CROSSBAR_HEIGHT_MM,
        support_width_mm=BREAKAWAY_SUPPORT_WIDTH_MM,
        crossbar_height_ratios=tuple(
            index / BREAKAWAY_CROSSBAR_COUNT
            for index in range(1, BREAKAWAY_CROSSBAR_COUNT + 1)
        ),
    )


def _brace_open_spans(
    *,
    span_minimum: float,
    span_maximum: float,
    divider_center_coordinates: tuple[float, ...],
    divider_thickness_mm: float,
) -> tuple[tuple[float, float], ...]:
    divider_half_thickness = divider_thickness_mm / 2.0
    blocked_spans = sorted(
        (
            max(span_minimum, coordinate - divider_half_thickness),
            min(span_maximum, coordinate + divider_half_thickness),
        )
        for coordinate in divider_center_coordinates
        if coordinate + divider_half_thickness > span_minimum
        and coordinate - divider_half_thickness < span_maximum
    )
    open_spans = []
    cursor = span_minimum
    for blocked_minimum, blocked_maximum in blocked_spans:
        if blocked_minimum > cursor + POSITION_TOLERANCE_MM:
            open_spans.append((cursor, blocked_minimum))
        cursor = max(cursor, blocked_maximum)
    if cursor < span_maximum - POSITION_TOLERANCE_MM:
        open_spans.append((cursor, span_maximum))
    return tuple(open_spans)


def _distributed_support_centers(
    open_spans: tuple[tuple[float, float], ...],
) -> tuple[float, ...]:
    centers = []
    for span_minimum, span_maximum in open_spans:
        span_length = span_maximum - span_minimum
        bridge_count = max(1, math.ceil(span_length / BREAKAWAY_MAX_BRIDGE_MM))
        centers.extend(
            span_minimum + span_length * support_index / bridge_count
            for support_index in range(1, bridge_count)
        )
    return tuple(centers)


def _add_breakaway_brace_lattice(
    part,
    *,
    split_axis: str,
    split_coordinate: float,
    inside_direction: int,
    span_minimum: float,
    span_maximum: float,
    divider_center_coordinates: tuple[float, ...],
    divider_thickness_mm: float,
    brace_top_z: float,
):
    import cadquery as cq
    from cqgridfinity import GR_BASE_HEIGHT, GR_FLOOR

    floor_top_z = GR_BASE_HEIGHT + GR_FLOOR
    profile = _breakaway_brace_profile()
    crossbar_center_height = brace_top_z - floor_top_z - profile.crossbar_height_mm / 2.0
    if crossbar_center_height <= 0:
        return part

    crossbar_centers_z = tuple(
        floor_top_z + crossbar_center_height * ratio
        for ratio in profile.crossbar_height_ratios
    )
    open_spans = _brace_open_spans(
        span_minimum=span_minimum,
        span_maximum=span_maximum,
        divider_center_coordinates=divider_center_coordinates,
        divider_thickness_mm=divider_thickness_mm,
    )
    normal_center = split_coordinate + inside_direction * profile.thickness_mm / 2.0
    brace = None

    for crossbar_center_z in crossbar_centers_z:
        for open_span_minimum, open_span_maximum in open_spans:
            span_length = open_span_maximum - open_span_minimum
            span_center = open_span_minimum + span_length / 2.0
            if split_axis == "width":
                crossbar = (
                    cq.Workplane("XY")
                    .box(
                        profile.thickness_mm,
                        span_length,
                        profile.crossbar_height_mm,
                    )
                    .translate((normal_center, span_center, crossbar_center_z))
                )
            else:
                crossbar = (
                    cq.Workplane("XY")
                    .box(
                        span_length,
                        profile.thickness_mm,
                        profile.crossbar_height_mm,
                    )
                    .translate((span_center, normal_center, crossbar_center_z))
                )
            brace = crossbar if brace is None else brace.union(crossbar)

    support_bottom_z = floor_top_z - profile.thickness_mm
    support_height = brace_top_z - support_bottom_z
    for support_span_center in _distributed_support_centers(open_spans):
        if split_axis == "width":
            support = (
                cq.Workplane("XY")
                .box(
                    profile.thickness_mm,
                    profile.support_width_mm,
                    support_height,
                )
                .translate(
                    (
                        normal_center,
                        support_span_center,
                        support_bottom_z + support_height / 2.0,
                    )
                )
            )
        else:
            support = (
                cq.Workplane("XY")
                .box(
                    profile.support_width_mm,
                    profile.thickness_mm,
                    support_height,
                )
                .translate(
                    (
                        support_span_center,
                        normal_center,
                        support_bottom_z + support_height / 2.0,
                    )
                )
            )
        brace = support if brace is None else brace.union(support)

    return part if brace is None else part.union(brace)


def _axis_split_coordinates(
    *,
    minimum: float,
    maximum: float,
    unit_count: int,
    split_positions_u: tuple[float, ...],
) -> tuple[float, ...]:
    axis_size = maximum - minimum
    return tuple(
        minimum + axis_size * split_position_u / unit_count
        for split_position_u in split_positions_u
    )


def _axis_segments(
    *,
    minimum: float,
    maximum: float,
    unit_count: int,
    split_positions_u: tuple[float, ...],
) -> tuple[tuple[float, float], ...]:
    split_coordinates = _axis_split_coordinates(
        minimum=minimum,
        maximum=maximum,
        unit_count=unit_count,
        split_positions_u=split_positions_u,
    )
    coordinates = (minimum, *split_coordinates, maximum)
    return tuple(zip(coordinates, coordinates[1:], strict=False))


def _split_part_name(
    *,
    width_index: int,
    width_count: int,
    depth_index: int,
    depth_count: int,
) -> str:
    name_parts = []
    if width_count > 1:
        name_parts.append(f"width_{width_index}_of_{width_count}")
    if depth_count > 1:
        name_parts.append(f"depth_{depth_index}_of_{depth_count}")
    return "_".join(name_parts) or "whole"


def _validate_split_positions(
    *,
    parameter_name: str,
    unit_count: int,
    positions_u: tuple[float, ...],
) -> None:
    for position in positions_u:
        if position <= 0 or position >= unit_count:
            raise ValueError(
                f"{parameter_name} position {position:g}U is outside the footprint. "
                f"Split positions must be greater than 0U and less than {unit_count:g}U."
            )

    for previous_position, current_position in zip(
        positions_u, positions_u[1:], strict=False
    ):
        if current_position <= previous_position + POSITION_TOLERANCE_MM / GRID_UNIT_MM:
            raise ValueError(
                f"{parameter_name} positions {previous_position:g}U and "
                f"{current_position:g}U overlap or duplicate each other."
            )


def _parse_position_list(
    parameter_name: str, raw_positions: str | Sequence[float]
) -> tuple[float, ...]:
    if isinstance(raw_positions, str):
        stripped_positions = raw_positions.strip()
        if not stripped_positions:
            return ()

        values = []
        for raw_position in stripped_positions.split(","):
            stripped_position = raw_position.strip()
            if not stripped_position:
                raise ValueError(f"{parameter_name} contains an empty position.")
            values.append(float(stripped_position))
        return tuple(values)

    if isinstance(raw_positions, Iterable):
        return tuple(float(position) for position in raw_positions)

    raise ValueError(f"{parameter_name} must be a comma-separated string or a sequence.")


def _validate_divider_specs(
    *,
    axis_name: str,
    position_axis_size_mm: float,
    span_axis_units: int,
    divider_thickness_mm: float,
    divider_specs: tuple[DividerSpec, ...],
) -> None:
    minimum_center = divider_thickness_mm / 2.0
    maximum_center = position_axis_size_mm - divider_thickness_mm / 2.0

    for divider_spec in divider_specs:
        position_mm = divider_spec.position_u * GRID_UNIT_MM
        if position_mm < minimum_center or position_mm > maximum_center:
            raise ValueError(
                f"{axis_name} divider at {divider_spec.position_u:g}U is outside the "
                "usable cavity. Centerline positions must be between "
                f"{minimum_center / GRID_UNIT_MM:g}U and "
                f"{maximum_center / GRID_UNIT_MM:g}U."
            )

        if divider_spec.span_start_u < 0 or divider_spec.span_end_u > span_axis_units:
            raise ValueError(
                f"{axis_name} divider span {divider_spec.span_start_u:g}-"
                f"{divider_spec.span_end_u:g}U is outside the opposite axis. Spans must "
                f"stay between 0U and {span_axis_units:g}U."
            )

        if divider_spec.span_start_u >= divider_spec.span_end_u:
            raise ValueError(
                f"{axis_name} divider span {divider_spec.span_start_u:g}-"
                f"{divider_spec.span_end_u:g}U must have a start less than its end."
            )

    for previous_index, previous_spec in enumerate(divider_specs):
        for current_spec in divider_specs[previous_index + 1 :]:
            distance_mm = abs(current_spec.position_u - previous_spec.position_u) * GRID_UNIT_MM
            if (
                distance_mm <= divider_thickness_mm + POSITION_TOLERANCE_MM
                and _divider_spans_overlap(previous_spec, current_spec)
            ):
                raise ValueError(
                    f"{axis_name} dividers at {previous_spec.position_u:g}U and "
                    f"{current_spec.position_u:g}U overlap or duplicate each other over "
                    "the same span."
                )


def _divider_spans_overlap(first_spec: DividerSpec, second_spec: DividerSpec) -> bool:
    return max(first_spec.span_start_u, second_spec.span_start_u) < min(
        first_spec.span_end_u, second_spec.span_end_u
    )


def _validate_unit_count(name: str, value: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{name} must be an integer Gridfinity unit count.")
    if value < 1:
        raise ValueError(f"{name} must be at least 1.")


def _validate_positive(name: str, value: float) -> None:
    if value <= 0:
        raise ValueError(f"{name} must be positive.")
