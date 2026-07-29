"""Gridfinity holder with a smooth fitted socket for a rounded cup."""

from __future__ import annotations

import math

from print_models.models.gridfinity_box import FractionalDividerGridfinityBox

NAME = "gridfinity_cup_holder"
DESCRIPTION = (
    "Two-cell Gridfinity holder with a smooth, scan-informed socket for an upright rounded cup."
)
PARAMETERS = {
    "unit_width": 2,
    "unit_depth": 2,
    "unit_height": 4,
    "widest_diameter_mm": 70.0,
    "item_height_mm": 69.0,
    "flat_base_diameter_mm": 40.0,
    "rounded_base_height_mm": 35.0,
    "pocket_depth_mm": 18.0,
    "radial_clearance_mm": 0.6,
    "bottom_clearance_mm": 0.6,
    "wall_thickness_mm": 1.0,
}
PRINT_NOTES = (
    "Defaults fit the measured blue cup upright in a 2x2, 4U Gridfinity holder. The OBJ scan "
    "is used only as a shape reference: the editable cutter is a smooth surface of revolution "
    "with a 40 mm flat base, rounded lower wall, and 70 mm maximum diameter. Print a shallow "
    "fit check before committing to the complete holder if the printer's dimensional accuracy "
    "is unknown."
)

GRIDFINITY_HEIGHT_UNIT_MM = 7.0
MINIMUM_CAVITY_FLOOR_MM = 2.0
MINIMUM_DECK_RING_MM = 2.0
PROFILE_SAMPLE_COUNT = 12
BOOLEAN_OVERLAP_MM = 0.1


def build(
    unit_width: int = 2,
    unit_depth: int = 2,
    unit_height: int = 4,
    widest_diameter_mm: float = 70.0,
    item_height_mm: float = 69.0,
    flat_base_diameter_mm: float = 40.0,
    rounded_base_height_mm: float = 35.0,
    pocket_depth_mm: float = 18.0,
    radial_clearance_mm: float = 0.6,
    bottom_clearance_mm: float = 0.6,
    wall_thickness_mm: float = 1.0,
):
    """Build a filled Gridfinity holder and subtract an upright cup-shaped socket."""
    import cadquery as cq
    from cqgridfinity import GR_BASE_HEIGHT, GR_FLOOR

    _validate_parameters(
        unit_width=unit_width,
        unit_depth=unit_depth,
        unit_height=unit_height,
        widest_diameter_mm=widest_diameter_mm,
        item_height_mm=item_height_mm,
        flat_base_diameter_mm=flat_base_diameter_mm,
        rounded_base_height_mm=rounded_base_height_mm,
        pocket_depth_mm=pocket_depth_mm,
        radial_clearance_mm=radial_clearance_mm,
        bottom_clearance_mm=bottom_clearance_mm,
        wall_thickness_mm=wall_thickness_mm,
    )

    box = FractionalDividerGridfinityBox(
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
    bounding_box = box.val().BoundingBox()
    floor_top_z = GR_BASE_HEIGHT + GR_FLOOR
    deck_top_z = unit_height * GRIDFINITY_HEIGHT_UNIT_MM
    cavity_bottom_z = deck_top_z - pocket_depth_mm - bottom_clearance_mm

    if cavity_bottom_z - floor_top_z < MINIMUM_CAVITY_FLOOR_MM:
        raise ValueError(
            "unit_height is too short for pocket_depth_mm and bottom_clearance_mm while "
            f"preserving a {MINIMUM_CAVITY_FLOOR_MM:g} mm cavity floor."
        )

    inner_width = bounding_box.xlen - 2.0 * wall_thickness_mm
    inner_depth = bounding_box.ylen - 2.0 * wall_thickness_mm
    opening_diameter = 2.0 * (
        _cup_radius_at_height(
            pocket_depth_mm,
            widest_diameter_mm=widest_diameter_mm,
            flat_base_diameter_mm=flat_base_diameter_mm,
            rounded_base_height_mm=rounded_base_height_mm,
        )
        + radial_clearance_mm
    )
    minimum_inner_span = min(inner_width, inner_depth)
    if opening_diameter + 2.0 * MINIMUM_DECK_RING_MM > minimum_inner_span:
        raise ValueError(
            f"The {opening_diameter:g} mm pocket opening does not leave a "
            f"{MINIMUM_DECK_RING_MM:g} mm deck ring in the selected Gridfinity footprint."
        )

    fill_bottom_z = floor_top_z - BOOLEAN_OVERLAP_MM
    fill_height = deck_top_z - fill_bottom_z
    insert_fill = (
        cq.Workplane("XY")
        .box(inner_width, inner_depth, fill_height)
        .translate((0.0, 0.0, fill_bottom_z + fill_height / 2.0))
    )
    cutter = _build_cup_cutter(
        item_bottom_z=deck_top_z - pocket_depth_mm,
        widest_diameter_mm=widest_diameter_mm,
        item_height_mm=item_height_mm,
        flat_base_diameter_mm=flat_base_diameter_mm,
        rounded_base_height_mm=rounded_base_height_mm,
        radial_clearance_mm=radial_clearance_mm,
        bottom_clearance_mm=bottom_clearance_mm,
    )
    return box.union(insert_fill).cut(cutter).clean()


def _build_cup_cutter(
    *,
    item_bottom_z: float,
    widest_diameter_mm: float,
    item_height_mm: float,
    flat_base_diameter_mm: float,
    rounded_base_height_mm: float,
    radial_clearance_mm: float,
    bottom_clearance_mm: float,
):
    import cadquery as cq

    base_radius = flat_base_diameter_mm / 2.0 + radial_clearance_mm
    maximum_radius = widest_diameter_mm / 2.0 + radial_clearance_mm
    cavity_bottom_z = item_bottom_z - bottom_clearance_mm
    rounded_profile_points = []
    for sample_index in range(1, PROFILE_SAMPLE_COUNT + 1):
        height = rounded_base_height_mm * sample_index / PROFILE_SAMPLE_COUNT
        radius = _cup_radius_at_height(
            height,
            widest_diameter_mm=widest_diameter_mm,
            flat_base_diameter_mm=flat_base_diameter_mm,
            rounded_base_height_mm=rounded_base_height_mm,
        )
        rounded_profile_points.append((radius + radial_clearance_mm, item_bottom_z + height))

    profile = (
        cq.Workplane("XZ")
        .moveTo(0.0, cavity_bottom_z)
        .lineTo(base_radius, cavity_bottom_z)
        .lineTo(base_radius, item_bottom_z)
        .spline(rounded_profile_points, includeCurrent=True)
        .lineTo(maximum_radius, item_bottom_z + item_height_mm)
        .lineTo(0.0, item_bottom_z + item_height_mm)
        .close()
    )
    return profile.revolve(360.0, (0.0, 0.0), (0.0, 1.0))


def _cup_radius_at_height(
    height_mm: float,
    *,
    widest_diameter_mm: float,
    flat_base_diameter_mm: float,
    rounded_base_height_mm: float,
) -> float:
    """Return the smooth scan-informed cup radius above its flat base."""
    base_radius = flat_base_diameter_mm / 2.0
    maximum_radius = widest_diameter_mm / 2.0
    normalized_height = min(max(height_mm / rounded_base_height_mm, 0.0), 1.0)
    blend = math.sin(normalized_height * math.pi / 2.0)
    return base_radius + (maximum_radius - base_radius) * blend


def _validate_parameters(
    *,
    unit_width: int,
    unit_depth: int,
    unit_height: int,
    widest_diameter_mm: float,
    item_height_mm: float,
    flat_base_diameter_mm: float,
    rounded_base_height_mm: float,
    pocket_depth_mm: float,
    radial_clearance_mm: float,
    bottom_clearance_mm: float,
    wall_thickness_mm: float,
) -> None:
    for name, value in (
        ("unit_width", unit_width),
        ("unit_depth", unit_depth),
        ("unit_height", unit_height),
    ):
        if isinstance(value, bool) or not isinstance(value, int) or value < 1:
            raise ValueError(f"{name} must be a positive integer.")

    for name, value in (
        ("widest_diameter_mm", widest_diameter_mm),
        ("item_height_mm", item_height_mm),
        ("flat_base_diameter_mm", flat_base_diameter_mm),
        ("rounded_base_height_mm", rounded_base_height_mm),
        ("pocket_depth_mm", pocket_depth_mm),
        ("wall_thickness_mm", wall_thickness_mm),
    ):
        if value <= 0:
            raise ValueError(f"{name} must be greater than zero.")

    for name, value in (
        ("radial_clearance_mm", radial_clearance_mm),
        ("bottom_clearance_mm", bottom_clearance_mm),
    ):
        if value < 0:
            raise ValueError(f"{name} must not be negative.")

    if flat_base_diameter_mm >= widest_diameter_mm:
        raise ValueError("flat_base_diameter_mm must be smaller than widest_diameter_mm.")
    if rounded_base_height_mm >= item_height_mm:
        raise ValueError("rounded_base_height_mm must be smaller than item_height_mm.")
    if pocket_depth_mm > item_height_mm:
        raise ValueError("pocket_depth_mm must not exceed item_height_mm.")
