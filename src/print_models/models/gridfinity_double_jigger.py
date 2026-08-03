"""Gridfinity cradle with a side-laid cutout for an OXO-style double jigger."""

from __future__ import annotations

import math

from print_models.models._side_laid_profile import Point2D, build_smooth_revolved_cutter
from print_models.models.gridfinity_box import FractionalDividerGridfinityBox

NAME = "gridfinity_double_jigger"
DESCRIPTION = "Side-laid 1 oz/1.5 oz double-jigger cradle for a compact 3x2 Gridfinity footprint."
PARAMETERS = {
    "unit_width": 3,
    "unit_depth": 2,
    "unit_height": 4,
    "jigger_length_mm": 77.6,
    "one_ounce_rim_diameter_mm": 47.0,
    "one_ounce_cup_height_mm": 18.3,
    "one_ounce_grip_diameter_mm": 33.8,
    "waist_diameter_mm": 23.8,
    "waist_position_mm": 36.0,
    "one_and_half_ounce_grip_diameter_mm": 39.8,
    "one_and_half_ounce_cup_height_mm": 21.4,
    "one_and_half_ounce_rim_diameter_mm": 57.8,
    "pocket_depth_mm": 18.0,
    "fit_clearance_mm": 1.0,
    "wall_thickness_mm": 1.0,
}
PRINT_NOTES = (
    "Defaults fit the measured OXO 1 oz/1.5 oz double jigger on its side in a 3x2, 4U "
    "Gridfinity cradle. The 77.6 mm profile is constrained to measured 47 mm and 57.8 mm "
    "rim diameters and a 23.8 mm waist; cup heights and grip transitions are traced from a "
    "calibrated profile photo. The 1 mm fit clearance is applied radially and at both ends."
)

GRIDFINITY_HEIGHT_UNIT_MM = 7.0
MINIMUM_CAVITY_FLOOR_MM = 2.0
MINIMUM_DECK_RING_MM = 2.0
BOOLEAN_OVERLAP_MM = 0.1
RIM_LIP_LENGTH_MM = 1.0


def build(
    unit_width: int = 3,
    unit_depth: int = 2,
    unit_height: int = 4,
    jigger_length_mm: float = 77.6,
    one_ounce_rim_diameter_mm: float = 47.0,
    one_ounce_cup_height_mm: float = 18.3,
    one_ounce_grip_diameter_mm: float = 33.8,
    waist_diameter_mm: float = 23.8,
    waist_position_mm: float = 36.0,
    one_and_half_ounce_grip_diameter_mm: float = 39.8,
    one_and_half_ounce_cup_height_mm: float = 21.4,
    one_and_half_ounce_rim_diameter_mm: float = 57.8,
    pocket_depth_mm: float = 18.0,
    fit_clearance_mm: float = 1.0,
    wall_thickness_mm: float = 1.0,
):
    """Build a filled Gridfinity cradle and subtract a horizontal double-jigger socket."""
    import cadquery as cq
    from cqgridfinity import GR_BASE_HEIGHT, GR_FLOOR

    _validate_parameters(
        unit_width=unit_width,
        unit_depth=unit_depth,
        unit_height=unit_height,
        jigger_length_mm=jigger_length_mm,
        one_ounce_rim_diameter_mm=one_ounce_rim_diameter_mm,
        one_ounce_cup_height_mm=one_ounce_cup_height_mm,
        one_ounce_grip_diameter_mm=one_ounce_grip_diameter_mm,
        waist_diameter_mm=waist_diameter_mm,
        waist_position_mm=waist_position_mm,
        one_and_half_ounce_grip_diameter_mm=one_and_half_ounce_grip_diameter_mm,
        one_and_half_ounce_cup_height_mm=one_and_half_ounce_cup_height_mm,
        one_and_half_ounce_rim_diameter_mm=one_and_half_ounce_rim_diameter_mm,
        pocket_depth_mm=pocket_depth_mm,
        fit_clearance_mm=fit_clearance_mm,
        wall_thickness_mm=wall_thickness_mm,
    )

    profile_points = _double_jigger_profile_points(
        jigger_length_mm=jigger_length_mm,
        one_ounce_rim_diameter_mm=one_ounce_rim_diameter_mm,
        one_ounce_cup_height_mm=one_ounce_cup_height_mm,
        one_ounce_grip_diameter_mm=one_ounce_grip_diameter_mm,
        waist_diameter_mm=waist_diameter_mm,
        waist_position_mm=waist_position_mm,
        one_and_half_ounce_grip_diameter_mm=one_and_half_ounce_grip_diameter_mm,
        one_and_half_ounce_cup_height_mm=one_and_half_ounce_cup_height_mm,
        one_and_half_ounce_rim_diameter_mm=one_and_half_ounce_rim_diameter_mm,
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
    cavity_bottom_z = deck_top_z - pocket_depth_mm

    if cavity_bottom_z - floor_top_z < MINIMUM_CAVITY_FLOOR_MM:
        raise ValueError(
            "unit_height is too short for pocket_depth_mm while preserving a "
            f"{MINIMUM_CAVITY_FLOOR_MM:g} mm cavity floor."
        )

    inner_width = bounding_box.xlen - 2.0 * wall_thickness_mm
    inner_depth = bounding_box.ylen - 2.0 * wall_thickness_mm
    cutter_length = jigger_length_mm + 2.0 * fit_clearance_mm
    if cutter_length + 2.0 * MINIMUM_DECK_RING_MM > inner_width:
        raise ValueError(
            f"The {cutter_length:g} mm cutout length does not leave a "
            f"{MINIMUM_DECK_RING_MM:g} mm deck ring in the selected Gridfinity width."
        )

    profile_radii = tuple(radius for _, radius in profile_points)
    maximum_radius = max(profile_radii) + fit_clearance_mm
    minimum_radius = min(profile_radii) + fit_clearance_mm
    axis_height_above_deck = maximum_radius - pocket_depth_mm
    if axis_height_above_deck >= minimum_radius:
        raise ValueError(
            "pocket_depth_mm is too shallow for every section of the jigger to open at the deck."
        )
    if pocket_depth_mm > maximum_radius:
        raise ValueError("pocket_depth_mm must not place the jigger axis below the deck.")

    opening_half_width = math.sqrt(maximum_radius**2 - axis_height_above_deck**2)
    opening_width = 2.0 * opening_half_width
    if opening_width + 2.0 * MINIMUM_DECK_RING_MM > inner_depth:
        raise ValueError(
            f"The {opening_width:g} mm pocket opening does not leave a "
            f"{MINIMUM_DECK_RING_MM:g} mm deck ring in the selected Gridfinity depth."
        )

    fill_bottom_z = floor_top_z - BOOLEAN_OVERLAP_MM
    fill_height = deck_top_z - fill_bottom_z
    insert_fill = (
        cq.Workplane("XY")
        .box(inner_width, inner_depth, fill_height)
        .translate((0.0, 0.0, fill_bottom_z + fill_height / 2.0))
    )
    cutter = _build_double_jigger_cutter(
        axis_z=deck_top_z + axis_height_above_deck,
        jigger_length_mm=jigger_length_mm,
        one_ounce_rim_diameter_mm=one_ounce_rim_diameter_mm,
        one_ounce_cup_height_mm=one_ounce_cup_height_mm,
        one_ounce_grip_diameter_mm=one_ounce_grip_diameter_mm,
        waist_diameter_mm=waist_diameter_mm,
        waist_position_mm=waist_position_mm,
        one_and_half_ounce_grip_diameter_mm=one_and_half_ounce_grip_diameter_mm,
        one_and_half_ounce_cup_height_mm=one_and_half_ounce_cup_height_mm,
        one_and_half_ounce_rim_diameter_mm=one_and_half_ounce_rim_diameter_mm,
        fit_clearance_mm=fit_clearance_mm,
    )
    return box.union(insert_fill).cut(cutter).clean()


def _build_double_jigger_cutter(
    *,
    axis_z: float,
    jigger_length_mm: float,
    one_ounce_rim_diameter_mm: float,
    one_ounce_cup_height_mm: float,
    one_ounce_grip_diameter_mm: float,
    waist_diameter_mm: float,
    waist_position_mm: float,
    one_and_half_ounce_grip_diameter_mm: float,
    one_and_half_ounce_cup_height_mm: float,
    one_and_half_ounce_rim_diameter_mm: float,
    fit_clearance_mm: float,
):
    profile_points = _double_jigger_profile_points(
        jigger_length_mm=jigger_length_mm,
        one_ounce_rim_diameter_mm=one_ounce_rim_diameter_mm,
        one_ounce_cup_height_mm=one_ounce_cup_height_mm,
        one_ounce_grip_diameter_mm=one_ounce_grip_diameter_mm,
        waist_diameter_mm=waist_diameter_mm,
        waist_position_mm=waist_position_mm,
        one_and_half_ounce_grip_diameter_mm=one_and_half_ounce_grip_diameter_mm,
        one_and_half_ounce_cup_height_mm=one_and_half_ounce_cup_height_mm,
        one_and_half_ounce_rim_diameter_mm=one_and_half_ounce_rim_diameter_mm,
    )
    return build_smooth_revolved_cutter(
        axis_z=axis_z,
        profile_points=profile_points,
        fit_clearance_mm=fit_clearance_mm,
    )


def _double_jigger_profile_points(
    *,
    jigger_length_mm: float,
    one_ounce_rim_diameter_mm: float,
    one_ounce_cup_height_mm: float,
    one_ounce_grip_diameter_mm: float,
    waist_diameter_mm: float,
    waist_position_mm: float,
    one_and_half_ounce_grip_diameter_mm: float,
    one_and_half_ounce_cup_height_mm: float,
    one_and_half_ounce_rim_diameter_mm: float,
) -> tuple[Point2D, ...]:
    """Return measured and calibrated-photo profile anchors from 1 oz to 1.5 oz rim."""
    jigger_start_x = -jigger_length_mm / 2.0
    one_ounce_rim_radius = one_ounce_rim_diameter_mm / 2.0
    one_ounce_grip_radius = one_ounce_grip_diameter_mm / 2.0
    waist_radius = waist_diameter_mm / 2.0
    one_and_half_ounce_grip_radius = one_and_half_ounce_grip_diameter_mm / 2.0
    one_and_half_ounce_rim_radius = one_and_half_ounce_rim_diameter_mm / 2.0
    one_and_half_ounce_grip_position_mm = jigger_length_mm - one_and_half_ounce_cup_height_mm

    def point(position_mm: float, radius: float) -> Point2D:
        return jigger_start_x + position_mm, radius

    upper_grip_span = waist_position_mm - one_ounce_cup_height_mm
    lower_grip_span = one_and_half_ounce_grip_position_mm - waist_position_mm

    def upper_grip_point(position_fraction: float, radius_fraction: float) -> Point2D:
        return point(
            one_ounce_cup_height_mm + upper_grip_span * position_fraction,
            one_ounce_grip_radius + (waist_radius - one_ounce_grip_radius) * radius_fraction,
        )

    def lower_grip_point(position_fraction: float, radius_fraction: float) -> Point2D:
        return point(
            waist_position_mm + lower_grip_span * position_fraction,
            waist_radius + (one_and_half_ounce_grip_radius - waist_radius) * radius_fraction,
        )

    return (
        point(0.0, one_ounce_rim_radius),
        point(min(RIM_LIP_LENGTH_MM, one_ounce_cup_height_mm / 4.0), one_ounce_rim_radius),
        point(one_ounce_cup_height_mm, one_ounce_grip_radius),
        upper_grip_point(0.23, 0.27),
        upper_grip_point(0.56, 0.71),
        upper_grip_point(0.89, 0.99),
        point(waist_position_mm, waist_radius),
        lower_grip_point(0.32, 0.20),
        lower_grip_point(0.60, 0.54),
        lower_grip_point(0.89, 0.89),
        point(one_and_half_ounce_grip_position_mm, one_and_half_ounce_grip_radius),
        point(
            jigger_length_mm - min(RIM_LIP_LENGTH_MM, one_and_half_ounce_cup_height_mm / 4.0),
            one_and_half_ounce_rim_radius,
        ),
        point(jigger_length_mm, one_and_half_ounce_rim_radius),
    )


def _validate_parameters(
    *,
    unit_width: int,
    unit_depth: int,
    unit_height: int,
    jigger_length_mm: float,
    one_ounce_rim_diameter_mm: float,
    one_ounce_cup_height_mm: float,
    one_ounce_grip_diameter_mm: float,
    waist_diameter_mm: float,
    waist_position_mm: float,
    one_and_half_ounce_grip_diameter_mm: float,
    one_and_half_ounce_cup_height_mm: float,
    one_and_half_ounce_rim_diameter_mm: float,
    pocket_depth_mm: float,
    fit_clearance_mm: float,
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
        ("jigger_length_mm", jigger_length_mm),
        ("one_ounce_rim_diameter_mm", one_ounce_rim_diameter_mm),
        ("one_ounce_cup_height_mm", one_ounce_cup_height_mm),
        ("one_ounce_grip_diameter_mm", one_ounce_grip_diameter_mm),
        ("waist_diameter_mm", waist_diameter_mm),
        ("waist_position_mm", waist_position_mm),
        ("one_and_half_ounce_grip_diameter_mm", one_and_half_ounce_grip_diameter_mm),
        ("one_and_half_ounce_cup_height_mm", one_and_half_ounce_cup_height_mm),
        ("one_and_half_ounce_rim_diameter_mm", one_and_half_ounce_rim_diameter_mm),
        ("pocket_depth_mm", pocket_depth_mm),
        ("wall_thickness_mm", wall_thickness_mm),
    ):
        if value <= 0:
            raise ValueError(f"{name} must be greater than zero.")

    if fit_clearance_mm < 0:
        raise ValueError("fit_clearance_mm must not be negative.")
    if one_ounce_cup_height_mm + one_and_half_ounce_cup_height_mm >= jigger_length_mm:
        raise ValueError("The two cup heights must leave space for the central grip.")

    one_and_half_ounce_grip_position_mm = jigger_length_mm - one_and_half_ounce_cup_height_mm
    if not one_ounce_cup_height_mm < waist_position_mm < one_and_half_ounce_grip_position_mm:
        raise ValueError("waist_position_mm must lie between the two cup-to-grip transitions.")
    if one_ounce_grip_diameter_mm >= one_ounce_rim_diameter_mm:
        raise ValueError("one_ounce_grip_diameter_mm must be smaller than its rim diameter.")
    if one_and_half_ounce_grip_diameter_mm >= one_and_half_ounce_rim_diameter_mm:
        raise ValueError(
            "one_and_half_ounce_grip_diameter_mm must be smaller than its rim diameter."
        )
    if waist_diameter_mm >= min(
        one_ounce_grip_diameter_mm,
        one_and_half_ounce_grip_diameter_mm,
    ):
        raise ValueError("waist_diameter_mm must be smaller than both grip transition diameters.")
    if (
        pocket_depth_mm
        > max(
            one_ounce_rim_diameter_mm,
            one_and_half_ounce_rim_diameter_mm,
        )
        / 2.0
        + fit_clearance_mm
    ):
        raise ValueError("pocket_depth_mm must not exceed the cleared maximum profile radius.")
