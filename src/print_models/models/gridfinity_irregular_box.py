"""Split Gridfinity box with a centered arm and one continuous interior."""

from __future__ import annotations

from collections.abc import Mapping

from print_models.models.gridfinity_box import (
    GRID_UNIT_MM,
    GRIDFINITY_BODY_FOOTPRINT_REDUCTION_MM,
    FractionalDividerGridfinityBox,
)

NAME = "gridfinity_irregular_box"
DESCRIPTION = (
    "Irregular 3x3 Gridfinity box with a centered four-cell arm, one continuous cavity, "
    "and a separately printable open-ended 1x2 section."
)
PARAMETERS = {
    "unit_height": 6,
    "wall_thickness_mm": 1.0,
}
PRINT_NOTES = (
    "The fixed top-view footprint is three cells wide for its first three columns and one "
    "centered cell wide for its final four columns. The last 1x2 section of the arm is "
    "exported separately with an open joining face, leaving a flat Gridfinity-boundary seam "
    "for gluing. Print both parts upright and glue the open seam faces together after checking "
    "alignment."
)

MAIN_WIDTH_U = 3
MAIN_DEPTH_U = 3
ARM_LENGTH_U = 4
ARM_DEPTH_U = 1
TOTAL_WIDTH_U = MAIN_WIDTH_U + ARM_LENGTH_U
SECOND_PART_WIDTH_U = 2
BOOLEAN_PADDING_MM = 2.0
VOID_ENVELOPE_INSET_MM = 0.01
MAIN_CENTER_X_MM = -ARM_LENGTH_U * GRID_UNIT_MM / 2.0
PART_SPLIT_X_MM = (TOTAL_WIDTH_U / 2.0 - SECOND_PART_WIDTH_U) * GRID_UNIT_MM


def build(
    unit_height: int = 6,
    wall_thickness_mm: float = 1.0,
) -> Mapping[str, object]:
    """Build the irregular box and split its final 1x2 arm section into a second part."""
    _validate_parameters(
        unit_height=unit_height,
        wall_thickness_mm=wall_thickness_mm,
    )

    whole_box = _build_whole_box(
        unit_height=unit_height,
        wall_thickness_mm=wall_thickness_mm,
    )
    primary, second_part = _split_second_part(whole_box)
    base_name = f"3x3_plus_1x4x{unit_height}u"
    return {
        f"{base_name}_primary": primary,
        f"{base_name}_second_1x2_open": second_part,
    }


def _build_whole_box(*, unit_height: int, wall_thickness_mm: float):
    """Merge overlapping boxes while retaining each one's exact walls and stacking lip."""
    from cqgridfinity import GR_BASE_HEIGHT, GR_FLOOR

    main_box = _render_rectangular_box(
        unit_width=MAIN_WIDTH_U,
        unit_depth=MAIN_DEPTH_U,
        unit_height=unit_height,
        wall_thickness_mm=wall_thickness_mm,
    ).translate((MAIN_CENTER_X_MM, 0.0, 0.0))
    center_row = _render_rectangular_box(
        unit_width=TOTAL_WIDTH_U,
        unit_depth=ARM_DEPTH_U,
        unit_height=unit_height,
        wall_thickness_mm=wall_thickness_mm,
    )
    merged_box = main_box.union(center_row)

    floor_top_z = GR_BASE_HEIGHT + GR_FLOOR
    main_void = _void_above_floor(main_box, floor_top_z=floor_top_z)
    row_void = _void_above_floor(center_row, floor_top_z=floor_top_z)
    row_void = _clip_void_to_connection(
        row_void,
        connection_x=main_box.val().BoundingBox().xmax,
    )
    return merged_box.cut(main_void.union(row_void)).clean()


def _render_rectangular_box(
    *,
    unit_width: int,
    unit_depth: int,
    unit_height: int,
    wall_thickness_mm: float,
):
    return FractionalDividerGridfinityBox(
        unit_width=unit_width,
        unit_depth=unit_depth,
        unit_height=unit_height,
        horizontal_specs=(),
        vertical_specs=(),
        wall_thickness_mm=wall_thickness_mm,
        divider_thickness_mm=1.2,
        scoops=False,
        lip_enabled=True,
    ).render()


def _void_above_floor(part, *, floor_top_z: float):
    """Return a part's exact open volume without touching its exterior perimeter."""
    import cadquery as cq

    bounding_box = part.val().BoundingBox()
    envelope_height = bounding_box.zmax - floor_top_z + BOOLEAN_PADDING_MM
    envelope = (
        cq.Workplane("XY")
        .box(
            bounding_box.xlen - 2.0 * VOID_ENVELOPE_INSET_MM,
            bounding_box.ylen - 2.0 * VOID_ENVELOPE_INSET_MM,
            envelope_height,
        )
        .translate(
            (
                bounding_box.xmin + bounding_box.xlen / 2.0,
                bounding_box.ymin + bounding_box.ylen / 2.0,
                floor_top_z + envelope_height / 2.0,
            )
        )
    )
    return envelope.cut(part)


def _clip_void_to_connection(void, *, connection_x: float):
    """Limit the row void to the internal join so its rounded end cannot cut the far wall."""
    import cadquery as cq

    bounding_box = void.val().BoundingBox()
    cutter = (
        cq.Workplane("XY")
        .box(GRID_UNIT_MM, bounding_box.ylen, bounding_box.zlen)
        .translate(
            (
                connection_x,
                bounding_box.ymin + bounding_box.ylen / 2.0,
                bounding_box.zmin + bounding_box.zlen / 2.0,
            )
        )
    )
    return void.intersect(cutter)


def _inner_span(unit_count: int, wall_thickness_mm: float) -> float:
    return (
        unit_count * GRID_UNIT_MM - GRIDFINITY_BODY_FOOTPRINT_REDUCTION_MM - 2.0 * wall_thickness_mm
    )


def _split_second_part(whole_box):
    """Clip at the exact Gridfinity boundary before the final two arm cells."""
    import cadquery as cq

    bounding_box = whole_box.val().BoundingBox()
    cutter_height = bounding_box.zlen + 2.0 * BOOLEAN_PADDING_MM
    cutter_z = bounding_box.zmin + bounding_box.zlen / 2.0

    primary_width = PART_SPLIT_X_MM - bounding_box.xmin
    primary_cutter = (
        cq.Workplane("XY")
        .box(primary_width, bounding_box.ylen, cutter_height)
        .translate(
            (
                bounding_box.xmin + primary_width / 2.0,
                bounding_box.ymin + bounding_box.ylen / 2.0,
                cutter_z,
            )
        )
    )
    second_part_width = bounding_box.xmax - PART_SPLIT_X_MM
    second_part_cutter = (
        cq.Workplane("XY")
        .box(second_part_width, bounding_box.ylen, cutter_height)
        .translate(
            (
                PART_SPLIT_X_MM + second_part_width / 2.0,
                bounding_box.ymin + bounding_box.ylen / 2.0,
                cutter_z,
            )
        )
    )

    return (
        whole_box.intersect(primary_cutter).clean(),
        whole_box.intersect(second_part_cutter).clean(),
    )


def _validate_parameters(*, unit_height: int, wall_thickness_mm: float) -> None:
    if isinstance(unit_height, bool) or not isinstance(unit_height, int) or unit_height < 1:
        raise ValueError("unit_height must be a positive integer.")
    if wall_thickness_mm <= 0:
        raise ValueError("wall_thickness_mm must be greater than zero.")
    if _inner_span(1, wall_thickness_mm) <= 0:
        raise ValueError("wall_thickness_mm leaves no interior space in the one-cell arm.")
