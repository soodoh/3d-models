"""Parametric Gridfinity box with fractional divider placement."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass

NAME = "gridfinity_box"
DESCRIPTION = (
    "Gridfinity storage box with lip, solid no-hole bottom, optional fractional "
    "dividers, and automatic print-bed-aware splitting."
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
    "split positions to control either axis. Raised floor specs use "
    "x_start-x_end@y_start-y_end:height_mm."
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


GRID_UNIT_MM = 42.0
POSITION_TOLERANCE_MM = 1e-6


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
            no_lip=False,
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
):
    """Build a Gridfinity storage box with optional custom dividers."""
    _validate_unit_count("unit_width", unit_width)
    _validate_unit_count("unit_depth", unit_depth)
    _validate_unit_count("unit_height", unit_height)
    _validate_positive("max_print_width", max_print_width)
    _validate_positive("max_print_depth", max_print_depth)
    _validate_positive("wall_thickness_mm", wall_thickness_mm)
    _validate_positive("divider_thickness_mm", divider_thickness_mm)

    horizontal_specs = _resolve_divider_specs(
        axis_name="horizontal",
        position_axis_size_mm=_inner_size(unit_depth, wall_thickness_mm),
        span_axis_units=unit_width,
        divider_thickness_mm=divider_thickness_mm,
        raw_specs=horizontal_dividers,
    )
    vertical_specs = _resolve_divider_specs(
        axis_name="vertical",
        position_axis_size_mm=_inner_size(unit_width, wall_thickness_mm),
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
        unit_height=unit_height,
        horizontal_specs=horizontal_specs,
        vertical_specs=vertical_specs,
        wall_thickness_mm=wall_thickness_mm,
        divider_thickness_mm=divider_thickness_mm,
        scoops=scoops,
    )
    rendered_box = _apply_raised_floors(
        box.render(),
        raised_floor_specs=raised_floor_specs,
        wall_thickness_mm=wall_thickness_mm,
    )
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
    )
    parts = _split_rendered_box(
        rendered_box,
        split_width_positions_u=split_width_positions_u,
        split_depth_positions_u=split_depth_positions_u,
        unit_width=unit_width,
        unit_depth=unit_depth,
    )
    return _named_export_parts(
        parts,
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
):
    if not raised_floor_specs:
        return rendered_box

    import cadquery as cq
    from cqgridfinity import GR_BASE_HEIGHT, GR_FLOOR

    bounding_box = rendered_box.val().BoundingBox()
    floor_top_z = GR_BASE_HEIGHT + GR_FLOOR
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
            if not all(
                _tile_fits(
                    width_maximum - width_minimum,
                    depth_maximum - depth_minimum,
                    max_print_width,
                    max_print_depth,
                    allow_rotation,
                )
                for width_minimum, width_maximum in width_segments
                for depth_minimum, depth_maximum in depth_segments
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

    padding_mm = 2.0
    z_size = bounding_box.zlen + 2 * padding_mm
    z_center = bounding_box.zmin + bounding_box.zlen / 2.0
    parts = {}

    for width_index, width_segment in enumerate(width_segments, start=1):
        width_minimum, width_maximum = width_segment
        for depth_index, depth_segment in enumerate(depth_segments, start=1):
            depth_minimum, depth_maximum = depth_segment
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
            part_name = _split_part_name(
                width_index=width_index,
                width_count=len(width_segments),
                depth_index=depth_index,
                depth_count=len(depth_segments),
            )
            parts[part_name] = rendered_box.intersect(cutter)

    return parts


def _axis_segments(
    *,
    minimum: float,
    maximum: float,
    unit_count: int,
    split_positions_u: tuple[float, ...],
) -> tuple[tuple[float, float], ...]:
    axis_size = maximum - minimum
    split_coordinates = tuple(
        minimum + axis_size * split_position_u / unit_count
        for split_position_u in split_positions_u
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
