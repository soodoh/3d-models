"""Gridfinity cradle with a side-laid cutout for a small snifter-like shot glass."""

from __future__ import annotations

import math

from print_models.models.gridfinity_box import FractionalDividerGridfinityBox

NAME = "gridfinity_small_snifter"
DESCRIPTION = "Side-laid small-snifter shot-glass cradle for a compact 3x2 Gridfinity footprint."
PARAMETERS = {
    "unit_width": 3,
    "unit_depth": 2,
    "unit_height": 4,
    "glass_length_mm": 85.0,
    "base_diameter_mm": 38.0,
    "base_height_mm": 11.0,
    "neck_diameter_mm": 30.0,
    "neck_height_mm": 25.0,
    "widest_diameter_mm": 49.0,
    "widest_height_from_top_mm": 26.0,
    "top_diameter_mm": 43.0,
    "pocket_depth_mm": 18.0,
    "fit_clearance_mm": 1.0,
    "wall_thickness_mm": 1.0,
}
PRINT_NOTES = (
    "Defaults fit the calibrated-photo and caliper-measured 85 mm small snifter on its side "
    "in a compact 3x2, 4U Gridfinity cradle. The profile has a 38 mm base through 11 mm, "
    "a 30 mm neck through 25 mm, a photo-traced cup-shaped bowl reaching 49 mm at 26 mm "
    "below the top, and a 43 mm rim. The 1 mm fit clearance is applied radially and at both ends."
)

GRIDFINITY_HEIGHT_UNIT_MM = 7.0
MINIMUM_CAVITY_FLOOR_MM = 2.0
MINIMUM_DECK_RING_MM = 2.0
BOOLEAN_OVERLAP_MM = 0.1

Point2D = tuple[float, float]


def build(
    unit_width: int = 3,
    unit_depth: int = 2,
    unit_height: int = 4,
    glass_length_mm: float = 85.0,
    base_diameter_mm: float = 38.0,
    base_height_mm: float = 11.0,
    neck_diameter_mm: float = 30.0,
    neck_height_mm: float = 25.0,
    widest_diameter_mm: float = 49.0,
    widest_height_from_top_mm: float = 26.0,
    top_diameter_mm: float = 43.0,
    pocket_depth_mm: float = 18.0,
    fit_clearance_mm: float = 1.0,
    wall_thickness_mm: float = 1.0,
):
    """Build a filled Gridfinity cradle and subtract a horizontal small-snifter socket."""
    import cadquery as cq
    from cqgridfinity import GR_BASE_HEIGHT, GR_FLOOR

    _validate_parameters(
        unit_width=unit_width,
        unit_depth=unit_depth,
        unit_height=unit_height,
        glass_length_mm=glass_length_mm,
        base_diameter_mm=base_diameter_mm,
        base_height_mm=base_height_mm,
        neck_diameter_mm=neck_diameter_mm,
        neck_height_mm=neck_height_mm,
        widest_diameter_mm=widest_diameter_mm,
        widest_height_from_top_mm=widest_height_from_top_mm,
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
    cutter_length = glass_length_mm + 2.0 * fit_clearance_mm
    if cutter_length + 2.0 * MINIMUM_DECK_RING_MM > inner_width:
        raise ValueError(
            f"The {cutter_length:g} mm cutout length does not leave a "
            f"{MINIMUM_DECK_RING_MM:g} mm deck ring in the selected Gridfinity width."
        )

    maximum_radius = widest_diameter_mm / 2.0 + fit_clearance_mm
    minimum_radius = min(base_diameter_mm, neck_diameter_mm, top_diameter_mm) / 2.0
    minimum_radius += fit_clearance_mm
    axis_height_above_deck = maximum_radius - pocket_depth_mm
    if axis_height_above_deck >= minimum_radius:
        raise ValueError(
            "pocket_depth_mm is too shallow for every section of the snifter to open at the deck."
        )
    if pocket_depth_mm > maximum_radius:
        raise ValueError("pocket_depth_mm must not place the snifter axis below the deck.")

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
    cutter = _build_small_snifter_cutter(
        axis_z=deck_top_z + axis_height_above_deck,
        glass_length_mm=glass_length_mm,
        base_diameter_mm=base_diameter_mm,
        base_height_mm=base_height_mm,
        neck_diameter_mm=neck_diameter_mm,
        neck_height_mm=neck_height_mm,
        widest_diameter_mm=widest_diameter_mm,
        widest_height_from_top_mm=widest_height_from_top_mm,
        top_diameter_mm=top_diameter_mm,
        fit_clearance_mm=fit_clearance_mm,
    )
    return box.union(insert_fill).cut(cutter).clean()


def _build_small_snifter_cutter(
    *,
    axis_z: float,
    glass_length_mm: float,
    base_diameter_mm: float,
    base_height_mm: float,
    neck_diameter_mm: float,
    neck_height_mm: float,
    widest_diameter_mm: float,
    widest_height_from_top_mm: float,
    top_diameter_mm: float,
    fit_clearance_mm: float,
):
    import cadquery as cq

    profile_points = _small_snifter_profile_points(
        glass_length_mm=glass_length_mm,
        base_diameter_mm=base_diameter_mm,
        base_height_mm=base_height_mm,
        neck_diameter_mm=neck_diameter_mm,
        neck_height_mm=neck_height_mm,
        widest_diameter_mm=widest_diameter_mm,
        widest_height_from_top_mm=widest_height_from_top_mm,
        top_diameter_mm=top_diameter_mm,
    )
    cutter_profile_points = tuple(
        (axial_position, radius + fit_clearance_mm) for axial_position, radius in profile_points
    )
    profile_tangents = _monotone_profile_tangents(cutter_profile_points)
    profile_parameters = tuple(axial_position for axial_position, _ in cutter_profile_points)
    glass_start_x = cutter_profile_points[0][0]
    glass_end_x = cutter_profile_points[-1][0]
    cutter_start_x = glass_start_x - fit_clearance_mm
    cutter_end_x = glass_end_x + fit_clearance_mm
    bottom_radius = cutter_profile_points[0][1]
    top_radius = cutter_profile_points[-1][1]

    profile = (
        cq.Workplane("XZ")
        .moveTo(cutter_start_x, 0.0)
        .lineTo(cutter_start_x, bottom_radius)
        .lineTo(glass_start_x, bottom_radius)
        .spline(
            cutter_profile_points[1:],
            tangents=profile_tangents,
            parameters=profile_parameters,
            scale=False,
            includeCurrent=True,
        )
        .lineTo(cutter_end_x, top_radius)
        .lineTo(cutter_end_x, 0.0)
        .close()
    )
    return profile.revolve(360.0, (0.0, 0.0), (1.0, 0.0)).translate((0.0, 0.0, axis_z))


def _small_snifter_profile_points(
    *,
    glass_length_mm: float,
    base_diameter_mm: float,
    base_height_mm: float,
    neck_diameter_mm: float,
    neck_height_mm: float,
    widest_diameter_mm: float,
    widest_height_from_top_mm: float,
    top_diameter_mm: float,
) -> tuple[Point2D, ...]:
    """Return photo-informed profile anchors from the rounded base through the bowl."""
    glass_start_x = -glass_length_mm / 2.0
    base_radius = base_diameter_mm / 2.0
    neck_radius = neck_diameter_mm / 2.0
    widest_radius = widest_diameter_mm / 2.0
    top_radius = top_diameter_mm / 2.0
    base_transition_span = neck_height_mm - base_height_mm
    widest_height_mm = glass_length_mm - widest_height_from_top_mm
    lower_bowl_span = widest_height_mm - neck_height_mm
    upper_bowl_span = widest_height_from_top_mm

    def point(height_mm: float, radius: float) -> Point2D:
        return glass_start_x + height_mm, radius

    return (
        point(0.0, neck_radius + (base_radius - neck_radius) * 0.75),
        point(base_height_mm * 2.0 / 11.0, neck_radius + (base_radius - neck_radius) * 0.95),
        point(base_height_mm * 4.0 / 11.0, base_radius),
        point(base_height_mm * 8.0 / 11.0, neck_radius + (base_radius - neck_radius) * 0.90),
        point(base_height_mm, neck_radius + (base_radius - neck_radius) * 0.625),
        point(
            base_height_mm + base_transition_span * 2.0 / 7.0,
            neck_radius + (base_radius - neck_radius) * 0.125,
        ),
        point(base_height_mm + base_transition_span / 2.0, neck_radius),
        point(neck_height_mm, neck_radius),
        point(
            neck_height_mm + lower_bowl_span * 5.0 / 34.0,
            neck_radius + (widest_radius - neck_radius) * 2.0 / 19.0,
        ),
        point(
            neck_height_mm + lower_bowl_span * 11.0 / 34.0,
            neck_radius + (widest_radius - neck_radius) * 9.0 / 19.0,
        ),
        point(
            neck_height_mm + lower_bowl_span * 18.0 / 34.0,
            neck_radius + (widest_radius - neck_radius) * 16.0 / 19.0,
        ),
        point(
            neck_height_mm + lower_bowl_span * 24.0 / 34.0,
            neck_radius + (widest_radius - neck_radius) * 37.0 / 38.0,
        ),
        point(widest_height_mm, widest_radius),
        point(
            widest_height_mm + upper_bowl_span * 11.0 / 26.0,
            top_radius + (widest_radius - top_radius) * 5.0 / 6.0,
        ),
        point(
            widest_height_mm + upper_bowl_span * 20.0 / 26.0,
            top_radius + (widest_radius - top_radius) / 3.0,
        ),
        point(glass_length_mm, top_radius),
    )


def _monotone_profile_tangents(profile_points: tuple[Point2D, ...]) -> tuple[Point2D, ...]:
    """Return spline tangents that preserve profile extrema without introducing visible seams."""
    axial_spans = tuple(
        end[0] - start[0] for start, end in zip(profile_points, profile_points[1:], strict=False)
    )
    secant_slopes = tuple(
        (end[1] - start[1]) / axial_span
        for start, end, axial_span in zip(
            profile_points, profile_points[1:], axial_spans, strict=False
        )
    )
    tangent_slopes = [0.0] * len(profile_points)

    for point_index in range(1, len(profile_points) - 1):
        previous_slope = secant_slopes[point_index - 1]
        next_slope = secant_slopes[point_index]
        if previous_slope * next_slope <= 0.0:
            continue
        previous_span = axial_spans[point_index - 1]
        next_span = axial_spans[point_index]
        previous_weight = 2.0 * next_span + previous_span
        next_weight = next_span + 2.0 * previous_span
        tangent_slopes[point_index] = (previous_weight + next_weight) / (
            previous_weight / previous_slope + next_weight / next_slope
        )

    final_span = axial_spans[-1]
    previous_span = axial_spans[-2]
    final_secant = secant_slopes[-1]
    previous_secant = secant_slopes[-2]
    final_tangent = (
        (2.0 * final_span + previous_span) * final_secant - final_span * previous_secant
    ) / (final_span + previous_span)
    if final_tangent * final_secant <= 0.0:
        final_tangent = 0.0
    elif previous_secant * final_secant < 0.0 and abs(final_tangent) > abs(3.0 * final_secant):
        final_tangent = 3.0 * final_secant
    tangent_slopes[-1] = final_tangent

    return tuple((1.0, tangent_slope) for tangent_slope in tangent_slopes)


def _validate_parameters(
    *,
    unit_width: int,
    unit_depth: int,
    unit_height: int,
    glass_length_mm: float,
    base_diameter_mm: float,
    base_height_mm: float,
    neck_diameter_mm: float,
    neck_height_mm: float,
    widest_diameter_mm: float,
    widest_height_from_top_mm: float,
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
        ("glass_length_mm", glass_length_mm),
        ("base_diameter_mm", base_diameter_mm),
        ("base_height_mm", base_height_mm),
        ("neck_diameter_mm", neck_diameter_mm),
        ("neck_height_mm", neck_height_mm),
        ("widest_diameter_mm", widest_diameter_mm),
        ("widest_height_from_top_mm", widest_height_from_top_mm),
        ("top_diameter_mm", top_diameter_mm),
        ("pocket_depth_mm", pocket_depth_mm),
        ("wall_thickness_mm", wall_thickness_mm),
    ):
        if value <= 0:
            raise ValueError(f"{name} must be greater than zero.")

    if fit_clearance_mm < 0:
        raise ValueError("fit_clearance_mm must not be negative.")
    if base_height_mm >= neck_height_mm:
        raise ValueError("base_height_mm must be smaller than neck_height_mm.")
    if neck_height_mm >= glass_length_mm:
        raise ValueError("neck_height_mm must be smaller than glass_length_mm.")
    widest_height_mm = glass_length_mm - widest_height_from_top_mm
    if widest_height_mm <= neck_height_mm:
        raise ValueError(
            "widest_height_from_top_mm must place the widest section above neck_height_mm."
        )
    if neck_diameter_mm >= min(base_diameter_mm, top_diameter_mm):
        raise ValueError("neck_diameter_mm must be smaller than the base and top diameters.")
    if widest_diameter_mm <= max(base_diameter_mm, neck_diameter_mm, top_diameter_mm):
        raise ValueError("widest_diameter_mm must be the largest profile diameter.")
