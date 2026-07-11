"""Parametric Gridfinity box with fractional divider placement."""

from __future__ import annotations

from collections.abc import Iterable, Sequence

NAME = "gridfinity_box"
DESCRIPTION = (
    "Gridfinity storage box with lip, solid no-hole bottom, and optional fractional "
    "horizontal/vertical dividers."
)
PARAMETERS = {
    "unit_width": 5,
    "unit_depth": 5,
    "unit_height": 8,
    "horizontal_dividers": "",
    "vertical_dividers": "",
    "split_width_u": "",
    "split_depth": "",
    "wall_thickness_mm": 1.0,
    "divider_thickness_mm": 1.2,
}
PRINT_NOTES = (
    "Divider lists are comma-separated Gridfinity unit positions. Horizontal dividers "
    "run left-to-right and are positioned from the inside front edge along depth. "
    "Vertical dividers run front-to-back and are positioned from the inside left edge "
    "along width. Positions locate divider centerlines and may be decimal units. Split "
    "positions are comma-separated Gridfinity unit positions along the outer width/depth "
    "footprint and produce separate open-ended parts that can be joined after printing."
)

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
        horizontal_positions_mm: tuple[float, ...],
        vertical_positions_mm: tuple[float, ...],
        wall_thickness_mm: float,
        divider_thickness_mm: float,
    ) -> None:
        from cqgridfinity import GridfinityBox

        class CustomGridfinityBox(GridfinityBox):
            def __init__(self, *args, **kwargs):
                self.custom_horizontal_positions_mm = horizontal_positions_mm
                self.custom_vertical_positions_mm = vertical_positions_mm
                self.custom_divider_thickness_mm = divider_thickness_mm
                super().__init__(*args, **kwargs)

            @property
            def has_dividers(self):
                return bool(
                    self.custom_horizontal_positions_mm or self.custom_vertical_positions_mm
                )

            def render_dividers(self):
                import cadquery as cq

                result = None

                for x_position in self.custom_vertical_positions_mm:
                    wall = (
                        cq.Workplane("XY")
                        .rect(self.custom_divider_thickness_mm, self.outer_w)
                        .extrude(self.max_height)
                        .translate((x_position - self.half_in, self.half_w, self.floor_h))
                    )
                    result = wall if result is None else result.union(wall)

                for y_position in self.custom_horizontal_positions_mm:
                    wall = (
                        cq.Workplane("XY")
                        .rect(self.outer_l, self.custom_divider_thickness_mm)
                        .extrude(self.max_height)
                        .translate((self.half_l, y_position - self.half_in, self.floor_h))
                    )
                    result = wall if result is None else result.union(wall)

                return result

        self.box = CustomGridfinityBox(
            unit_width,
            unit_depth,
            unit_height,
            holes=False,
            scoops=False,
            labels=False,
            no_lip=False,
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
    wall_thickness_mm: float = 1.0,
    divider_thickness_mm: float = 1.2,
):
    """Build a Gridfinity storage box with optional custom dividers."""
    _validate_unit_count("unit_width", unit_width)
    _validate_unit_count("unit_depth", unit_depth)
    _validate_unit_count("unit_height", unit_height)
    _validate_positive("wall_thickness_mm", wall_thickness_mm)
    _validate_positive("divider_thickness_mm", divider_thickness_mm)

    horizontal_positions_u = _resolve_divider_positions(
        axis_name="horizontal",
        axis_size_mm=_inner_size(unit_depth, wall_thickness_mm),
        divider_thickness_mm=divider_thickness_mm,
        unit_positions=horizontal_dividers,
    )
    vertical_positions_u = _resolve_divider_positions(
        axis_name="vertical",
        axis_size_mm=_inner_size(unit_width, wall_thickness_mm),
        divider_thickness_mm=divider_thickness_mm,
        unit_positions=vertical_dividers,
    )
    horizontal_positions_mm = _unit_positions_to_mm(horizontal_positions_u)
    vertical_positions_mm = _unit_positions_to_mm(vertical_positions_u)

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

    box = FractionalDividerGridfinityBox(
        unit_width=unit_width,
        unit_depth=unit_depth,
        unit_height=unit_height,
        horizontal_positions_mm=horizontal_positions_mm,
        vertical_positions_mm=vertical_positions_mm,
        wall_thickness_mm=wall_thickness_mm,
        divider_thickness_mm=divider_thickness_mm,
    )
    rendered_box = box.render()
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
        horizontal_positions_u=horizontal_positions_u,
        vertical_positions_u=vertical_positions_u,
        split_width_positions_u=split_width_positions_u,
        split_depth_positions_u=split_depth_positions_u,
    )


def _inner_size(unit_count: int, wall_thickness_mm: float) -> float:
    from cqgridfinity import GR_TOL

    return unit_count * GRID_UNIT_MM - GR_TOL - 2 * wall_thickness_mm


def _resolve_divider_positions(
    *,
    axis_name: str,
    axis_size_mm: float,
    divider_thickness_mm: float,
    unit_positions: str | Sequence[float],
) -> tuple[float, ...]:
    sorted_positions_u = tuple(
        sorted(_parse_position_list(f"{axis_name}_dividers", unit_positions))
    )
    _validate_positions(
        axis_name=axis_name,
        axis_size_mm=axis_size_mm,
        divider_thickness_mm=divider_thickness_mm,
        positions_mm=_unit_positions_to_mm(sorted_positions_u),
    )
    return sorted_positions_u


def _unit_positions_to_mm(positions_u: tuple[float, ...]) -> tuple[float, ...]:
    return tuple(position * GRID_UNIT_MM for position in positions_u)


def _named_export_parts(
    parts: dict[str, object],
    *,
    unit_width: int,
    unit_depth: int,
    unit_height: int,
    horizontal_positions_u: tuple[float, ...],
    vertical_positions_u: tuple[float, ...],
    split_width_positions_u: tuple[float, ...],
    split_depth_positions_u: tuple[float, ...],
) -> dict[str, object]:
    base_name = _export_base_name(
        unit_width=unit_width,
        unit_depth=unit_depth,
        unit_height=unit_height,
        horizontal_positions_u=horizontal_positions_u,
        vertical_positions_u=vertical_positions_u,
        split_width_positions_u=split_width_positions_u,
        split_depth_positions_u=split_depth_positions_u,
    )

    if set(parts) == {"whole"}:
        return {base_name: parts["whole"]}

    return {f"{base_name}_{part_name}": part for part_name, part in parts.items()}


def _export_base_name(
    *,
    unit_width: int,
    unit_depth: int,
    unit_height: int,
    horizontal_positions_u: tuple[float, ...],
    vertical_positions_u: tuple[float, ...],
    split_width_positions_u: tuple[float, ...],
    split_depth_positions_u: tuple[float, ...],
) -> str:
    name_parts = [f"{unit_width}x{unit_depth}x{unit_height}u"]

    if horizontal_positions_u:
        horizontal_label = _format_positions(horizontal_positions_u)
        name_parts.append(f"horizontal_dividers_{horizontal_label}u")
    if vertical_positions_u:
        vertical_label = _format_positions(vertical_positions_u)
        name_parts.append(f"vertical_dividers_{vertical_label}u")
    if split_width_positions_u:
        name_parts.append(f"split_width_{_format_positions(split_width_positions_u)}u")
    if split_depth_positions_u:
        name_parts.append(f"split_depth_{_format_positions(split_depth_positions_u)}u")

    return "_".join(name_parts)


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


def _validate_positions(
    *,
    axis_name: str,
    axis_size_mm: float,
    divider_thickness_mm: float,
    positions_mm: tuple[float, ...],
) -> None:
    minimum_center = divider_thickness_mm / 2.0
    maximum_center = axis_size_mm - divider_thickness_mm / 2.0

    for position in positions_mm:
        if position < minimum_center or position > maximum_center:
            raise ValueError(
                f"{axis_name} divider at {position:g} mm is outside the usable cavity. "
                f"Centerline positions must be between {minimum_center:g} mm and "
                f"{maximum_center:g} mm."
            )

    for previous_position, current_position in zip(
        positions_mm, positions_mm[1:], strict=False
    ):
        distance = current_position - previous_position
        if distance <= divider_thickness_mm + POSITION_TOLERANCE_MM:
            raise ValueError(
                f"{axis_name} dividers at {previous_position:g} mm and {current_position:g} mm "
                f"overlap or duplicate each other. Centerlines must be more than "
                f"{divider_thickness_mm:g} mm apart."
            )


def _validate_unit_count(name: str, value: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{name} must be an integer Gridfinity unit count.")
    if value < 1:
        raise ValueError(f"{name} must be at least 1.")


def _validate_positive(name: str, value: float) -> None:
    if value <= 0:
        raise ValueError(f"{name} must be positive.")
