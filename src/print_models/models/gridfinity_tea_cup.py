"""Gridfinity cradle with a smooth side-laid cutout for a tapered tea cup."""

from __future__ import annotations

import math

from print_models.models._side_laid_profile import (
    Point2D,
    build_smooth_revolved_cutter,
)
from print_models.models.gridfinity_box import FractionalDividerGridfinityBox

NAME = "gridfinity_tea_cup"
DESCRIPTION = "Side-laid tapered tea-cup cradle for a compact 3x2 Gridfinity footprint."
PARAMETERS = {
    "unit_width": 3,
    "unit_depth": 2,
    "unit_height": 4,
    "cup_height_mm": 85.0,
    "bottom_diameter_mm": 40.0,
    "flare_start_height_mm": 58.0,
    "top_diameter_mm": 54.0,
    "pocket_depth_mm": 18.0,
    "fit_clearance_mm": 1.0,
    "wall_thickness_mm": 1.0,
}
PRINT_NOTES = (
    "Defaults fit the photographed and measured 85 mm tea cup on its side in a compact 3x2, "
    "4U Gridfinity cradle. The photo-informed profile holds a 40 mm lower diameter through most "
    "of its height, then smoothly flares from 58 mm to the 54 mm rim. The 1 mm fit clearance is "
    "applied radially and at both ends."
)

GRIDFINITY_HEIGHT_UNIT_MM = 7.0
MINIMUM_CAVITY_FLOOR_MM = 2.0
MINIMUM_DECK_RING_MM = 2.0
BOOLEAN_OVERLAP_MM = 0.1


def build(
    unit_width: int = 3,
    unit_depth: int = 2,
    unit_height: int = 4,
    cup_height_mm: float = 85.0,
    bottom_diameter_mm: float = 40.0,
    flare_start_height_mm: float = 58.0,
    top_diameter_mm: float = 54.0,
    pocket_depth_mm: float = 18.0,
    fit_clearance_mm: float = 1.0,
    wall_thickness_mm: float = 1.0,
):
    """Build a filled Gridfinity cradle and subtract a horizontal tea-cup socket."""
    import cadquery as cq
    from cqgridfinity import GR_BASE_HEIGHT, GR_FLOOR

    _validate_parameters(
        unit_width=unit_width,
        unit_depth=unit_depth,
        unit_height=unit_height,
        cup_height_mm=cup_height_mm,
        bottom_diameter_mm=bottom_diameter_mm,
        flare_start_height_mm=flare_start_height_mm,
        top_diameter_mm=top_diameter_mm,
        pocket_depth_mm=pocket_depth_mm,
        fit_clearance_mm=fit_clearance_mm,
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
    cavity_bottom_z = deck_top_z - pocket_depth_mm

    if cavity_bottom_z - floor_top_z < MINIMUM_CAVITY_FLOOR_MM:
        raise ValueError(
            "unit_height is too short for pocket_depth_mm while preserving a "
            f"{MINIMUM_CAVITY_FLOOR_MM:g} mm cavity floor."
        )

    inner_width = bounding_box.xlen - 2.0 * wall_thickness_mm
    inner_depth = bounding_box.ylen - 2.0 * wall_thickness_mm
    cutter_length = cup_height_mm + 2.0 * fit_clearance_mm
    if cutter_length + 2.0 * MINIMUM_DECK_RING_MM > inner_width:
        raise ValueError(
            f"The {cutter_length:g} mm cutout length does not leave a "
            f"{MINIMUM_DECK_RING_MM:g} mm deck ring in the selected Gridfinity width."
        )

    maximum_radius = top_diameter_mm / 2.0 + fit_clearance_mm
    minimum_radius = bottom_diameter_mm / 2.0 + fit_clearance_mm
    axis_height_above_deck = maximum_radius - pocket_depth_mm
    if axis_height_above_deck >= minimum_radius:
        raise ValueError(
            "pocket_depth_mm is too shallow for every section of the tea cup to open at the deck."
        )
    if pocket_depth_mm > maximum_radius:
        raise ValueError("pocket_depth_mm must not place the tea-cup axis below the deck.")

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
    cutter = _build_tea_cup_cutter(
        axis_z=deck_top_z + axis_height_above_deck,
        cup_height_mm=cup_height_mm,
        bottom_diameter_mm=bottom_diameter_mm,
        flare_start_height_mm=flare_start_height_mm,
        top_diameter_mm=top_diameter_mm,
        fit_clearance_mm=fit_clearance_mm,
    )
    return box.union(insert_fill).cut(cutter).clean()


def _build_tea_cup_cutter(
    *,
    axis_z: float,
    cup_height_mm: float,
    bottom_diameter_mm: float,
    flare_start_height_mm: float,
    top_diameter_mm: float,
    fit_clearance_mm: float,
):
    profile_points = _tea_cup_profile_points(
        cup_height_mm=cup_height_mm,
        bottom_diameter_mm=bottom_diameter_mm,
        flare_start_height_mm=flare_start_height_mm,
        top_diameter_mm=top_diameter_mm,
    )
    return build_smooth_revolved_cutter(
        axis_z=axis_z,
        profile_points=profile_points,
        fit_clearance_mm=fit_clearance_mm,
    )


def _tea_cup_profile_points(
    *,
    cup_height_mm: float,
    bottom_diameter_mm: float,
    flare_start_height_mm: float,
    top_diameter_mm: float,
) -> tuple[Point2D, ...]:
    """Return calibrated-photo profile anchors from the flat bottom through the flared rim."""
    cup_start_x = -cup_height_mm / 2.0
    bottom_radius = bottom_diameter_mm / 2.0
    top_radius = top_diameter_mm / 2.0
    radius_increase = top_radius - bottom_radius
    flare_span = cup_height_mm - flare_start_height_mm

    def point(height_mm: float, radius: float) -> Point2D:
        return cup_start_x + height_mm, radius

    return (
        point(0.0, bottom_radius),
        point(flare_start_height_mm * 0.15, bottom_radius),
        point(flare_start_height_mm * 0.65, bottom_radius),
        point(flare_start_height_mm, bottom_radius),
        point(flare_start_height_mm + flare_span * 0.25, bottom_radius + radius_increase * 0.14),
        point(flare_start_height_mm + flare_span * 0.45, bottom_radius + radius_increase * 0.38),
        point(flare_start_height_mm + flare_span * 0.70, bottom_radius + radius_increase * 0.68),
        point(flare_start_height_mm + flare_span * 0.90, bottom_radius + radius_increase * 0.94),
        point(cup_height_mm, top_radius),
    )


def _validate_parameters(
    *,
    unit_width: int,
    unit_depth: int,
    unit_height: int,
    cup_height_mm: float,
    bottom_diameter_mm: float,
    flare_start_height_mm: float,
    top_diameter_mm: float,
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
        ("cup_height_mm", cup_height_mm),
        ("bottom_diameter_mm", bottom_diameter_mm),
        ("flare_start_height_mm", flare_start_height_mm),
        ("top_diameter_mm", top_diameter_mm),
        ("pocket_depth_mm", pocket_depth_mm),
        ("wall_thickness_mm", wall_thickness_mm),
    ):
        if value <= 0:
            raise ValueError(f"{name} must be greater than zero.")

    if fit_clearance_mm < 0:
        raise ValueError("fit_clearance_mm must not be negative.")
    if flare_start_height_mm >= cup_height_mm:
        raise ValueError("flare_start_height_mm must be smaller than cup_height_mm.")
    if top_diameter_mm <= bottom_diameter_mm:
        raise ValueError("top_diameter_mm must be greater than bottom_diameter_mm.")
