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
    "horizontal_dividers_mm": "",
    "vertical_dividers_mm": "",
    "horizontal_dividers_u": "",
    "vertical_dividers_u": "",
    "wall_thickness_mm": 1.0,
    "divider_thickness_mm": 1.2,
}
PRINT_NOTES = (
    "Divider lists are comma-separated. Horizontal dividers run left-to-right and are "
    "positioned from the inside front edge along depth. Vertical dividers run "
    "front-to-back and are positioned from the inside left edge along width. Positions "
    "locate divider centerlines. *_u values may be decimal units and are multiplied "
    "by one 42 mm Gridfinity unit."
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
    horizontal_dividers_mm: str | Sequence[float] = "",
    vertical_dividers_mm: str | Sequence[float] = "",
    horizontal_dividers_u: str | Sequence[float] = "",
    vertical_dividers_u: str | Sequence[float] = "",
    wall_thickness_mm: float = 1.0,
    divider_thickness_mm: float = 1.2,
):
    """Build a Gridfinity storage box with optional custom dividers."""
    _validate_unit_count("unit_width", unit_width)
    _validate_unit_count("unit_depth", unit_depth)
    _validate_unit_count("unit_height", unit_height)
    _validate_positive("wall_thickness_mm", wall_thickness_mm)
    _validate_positive("divider_thickness_mm", divider_thickness_mm)

    horizontal_positions_mm = _resolve_positions(
        axis_name="horizontal",
        axis_size_mm=_inner_size(unit_depth, wall_thickness_mm),
        divider_thickness_mm=divider_thickness_mm,
        millimeter_positions=horizontal_dividers_mm,
        unit_positions=horizontal_dividers_u,
    )
    vertical_positions_mm = _resolve_positions(
        axis_name="vertical",
        axis_size_mm=_inner_size(unit_width, wall_thickness_mm),
        divider_thickness_mm=divider_thickness_mm,
        millimeter_positions=vertical_dividers_mm,
        unit_positions=vertical_dividers_u,
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
    return box.render()


def _inner_size(unit_count: int, wall_thickness_mm: float) -> float:
    from cqgridfinity import GR_TOL

    return unit_count * GRID_UNIT_MM - GR_TOL - 2 * wall_thickness_mm


def _resolve_positions(
    *,
    axis_name: str,
    axis_size_mm: float,
    divider_thickness_mm: float,
    millimeter_positions: str | Sequence[float],
    unit_positions: str | Sequence[float],
) -> tuple[float, ...]:
    resolved_positions = [
        *_parse_position_list(f"{axis_name}_dividers_mm", millimeter_positions),
        *(
            unit_position * GRID_UNIT_MM
            for unit_position in _parse_position_list(f"{axis_name}_dividers_u", unit_positions)
        ),
    ]
    sorted_positions = tuple(sorted(resolved_positions))
    _validate_positions(
        axis_name=axis_name,
        axis_size_mm=axis_size_mm,
        divider_thickness_mm=divider_thickness_mm,
        positions_mm=sorted_positions,
    )
    return sorted_positions


def _parse_position_list(parameter_name: str, raw_positions: str | Sequence[float]) -> tuple[float, ...]:
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

    for previous_position, current_position in zip(positions_mm, positions_mm[1:]):
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
