"""Gridfinity cradle with a smooth side-laid cutout for a whiskey snifter."""

from __future__ import annotations

import math

from print_models.models.gridfinity_box import FractionalDividerGridfinityBox

NAME = "gridfinity_whiskey_snifter"
DESCRIPTION = "Side-laid whiskey-snifter cradle for a compact 3x2 Gridfinity footprint."
PARAMETERS = {
    "unit_width": 3,
    "unit_depth": 2,
    "unit_height": 4,
    "glass_length_mm": 115.0,
    "base_diameter_mm": 46.0,
    "waist_diameter_mm": 32.0,
    "widest_diameter_mm": 67.0,
    "top_diameter_mm": 47.0,
    "pocket_depth_mm": 18.0,
    "fit_clearance_mm": 1.0,
    "wall_thickness_mm": 1.0,
}
PRINT_NOTES = (
    "Defaults fit the measured 115 mm tall whiskey snifter on its side in a compact 3x2, "
    "4U Gridfinity cradle. The smooth outer profile is rebuilt from Offnfopt's CC0 Glencairn "
    "Whisky Glass Silhouette and constrained to a 46 mm flat bottom and base flare at 4 mm, "
    "a 32 mm waist at 20 mm, a 67 mm bowl, and a 47 mm top. The 1 mm fit clearance is applied "
    "radially and at both ends."
)

GRIDFINITY_HEIGHT_UNIT_MM = 7.0
MINIMUM_CAVITY_FLOOR_MM = 2.0
MINIMUM_DECK_RING_MM = 2.0
BOOLEAN_OVERLAP_MM = 0.1

Point2D = tuple[float, float]
CubicBezier = tuple[Point2D, Point2D, Point2D, Point2D]

# CC0 source: "Glencairn Whisky Glass Silhouette" by Offnfopt.
# https://commons.wikimedia.org/wiki/File:Glencairn_Whisky_Glass_Silhouette.svg
# The right side of the source path is split at its base, waist, and bowl extrema so each
# feature can be scaled to a verified diameter without flattening the original Bézier curves.
SOURCE_AXIS_X = 120.507
SOURCE_TOP_Y = 22.997
SOURCE_BOTTOM_Y = 361.955
SOURCE_BOWL_SPLIT = 0.1356052414559627
SOURCE_WAIST_SPLIT = 0.024611773382227437
SOURCE_BASE_SPLIT = 0.5088482153360928
SOURCE_TOP_TO_BOTTOM_PROFILE: tuple[CubicBezier, ...] = (
    ((189.020, 22.997), (189.482, 55.555), (190.709, 85.141), (197.019, 113.986)),
    ((197.019, 113.986), (203.052, 141.569), (213.272, 167.919), (217.016, 192.976)),
    ((217.016, 192.976), (222.586, 230.246), (206.605, 256.524), (184.020, 271.966)),
    ((184.020, 271.966), (178.164, 275.971), (161.870, 282.483), (161.023, 287.964)),
    ((161.023, 287.964), (160.417, 291.894), (172.392, 309.247), (175.022, 314.961)),
    ((175.022, 314.961), (184.599, 335.771), (191.751, 351.047), (169.022, 361.955)),
)


def build(
    unit_width: int = 3,
    unit_depth: int = 2,
    unit_height: int = 4,
    glass_length_mm: float = 115.0,
    base_diameter_mm: float = 46.0,
    waist_diameter_mm: float = 32.0,
    widest_diameter_mm: float = 67.0,
    top_diameter_mm: float = 47.0,
    pocket_depth_mm: float = 18.0,
    fit_clearance_mm: float = 1.0,
    wall_thickness_mm: float = 1.0,
):
    """Build a filled Gridfinity cradle and subtract a horizontal snifter-shaped socket."""
    import cadquery as cq
    from cqgridfinity import GR_BASE_HEIGHT, GR_FLOOR

    _validate_parameters(
        unit_width=unit_width,
        unit_depth=unit_depth,
        unit_height=unit_height,
        glass_length_mm=glass_length_mm,
        base_diameter_mm=base_diameter_mm,
        waist_diameter_mm=waist_diameter_mm,
        widest_diameter_mm=widest_diameter_mm,
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
    minimum_radius = min(base_diameter_mm, waist_diameter_mm, top_diameter_mm) / 2.0
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
    cutter = _build_snifter_cutter(
        axis_z=deck_top_z + axis_height_above_deck,
        glass_length_mm=glass_length_mm,
        base_diameter_mm=base_diameter_mm,
        waist_diameter_mm=waist_diameter_mm,
        widest_diameter_mm=widest_diameter_mm,
        top_diameter_mm=top_diameter_mm,
        fit_clearance_mm=fit_clearance_mm,
    )
    return box.union(insert_fill).cut(cutter).clean()


def _build_snifter_cutter(
    *,
    axis_z: float,
    glass_length_mm: float,
    base_diameter_mm: float,
    waist_diameter_mm: float,
    widest_diameter_mm: float,
    top_diameter_mm: float,
    fit_clearance_mm: float,
):
    import cadquery as cq

    glass_start_x = -glass_length_mm / 2.0
    glass_end_x = glass_length_mm / 2.0
    cutter_start_x = glass_start_x - fit_clearance_mm
    cutter_end_x = glass_end_x + fit_clearance_mm
    profile_groups = _scaled_snifter_profile_groups(
        glass_length_mm=glass_length_mm,
        base_diameter_mm=base_diameter_mm,
        waist_diameter_mm=waist_diameter_mm,
        widest_diameter_mm=widest_diameter_mm,
        top_diameter_mm=top_diameter_mm,
    )
    base_radius = profile_groups[0][0][0][1] + fit_clearance_mm
    top_radius = profile_groups[-1][-1][-1][1] + fit_clearance_mm
    profile = (
        cq.Workplane("XZ")
        .moveTo(cutter_start_x, 0.0)
        .lineTo(cutter_start_x, base_radius)
        .lineTo(glass_start_x, base_radius)
    )
    for profile_group in profile_groups:
        for segment in profile_group:
            curve_points = [(x, radius + fit_clearance_mm) for x, radius in segment[1:]]
            profile = profile.bezier(curve_points, includeCurrent=True)

    profile = profile.lineTo(cutter_end_x, top_radius).lineTo(cutter_end_x, 0.0).close()
    return profile.revolve(360.0, (0.0, 0.0), (1.0, 0.0)).translate((0.0, 0.0, axis_z))


def _scaled_snifter_profile_groups(
    *,
    glass_length_mm: float,
    base_diameter_mm: float,
    waist_diameter_mm: float,
    widest_diameter_mm: float,
    top_diameter_mm: float,
) -> tuple[tuple[CubicBezier, ...], ...]:
    """Return the CC0 Bézier profile scaled to the verified feature dimensions."""
    source_groups = _source_profile_groups()
    source_anchor_radii = (source_groups[0][0][0][0] - SOURCE_AXIS_X,) + tuple(
        group[-1][-1][0] - SOURCE_AXIS_X for group in source_groups
    )
    source_anchor_positions = (0.0,) + tuple(
        SOURCE_BOTTOM_Y - group[-1][-1][1] for group in source_groups
    )
    source_height = SOURCE_BOTTOM_Y - SOURCE_TOP_Y
    base_radius = base_diameter_mm / 2.0
    target_anchor_radii = (
        base_radius,
        base_radius,
        waist_diameter_mm / 2.0,
        widest_diameter_mm / 2.0,
        top_diameter_mm / 2.0,
    )
    target_anchor_positions = (
        0.0,
        glass_length_mm * 4.0 / 115.0,
        glass_length_mm * 20.0 / 115.0,
        source_anchor_positions[3] / source_height * glass_length_mm,
        glass_length_mm,
    )
    glass_start_x = -glass_length_mm / 2.0
    scaled_groups = []

    for group_index, source_group in enumerate(source_groups):
        source_start_radius = source_anchor_radii[group_index]
        source_end_radius = source_anchor_radii[group_index + 1]
        target_start_radius = target_anchor_radii[group_index]
        target_end_radius = target_anchor_radii[group_index + 1]
        radius_scale = (target_end_radius - target_start_radius) / (
            source_end_radius - source_start_radius
        )
        source_start_position = source_anchor_positions[group_index]
        source_end_position = source_anchor_positions[group_index + 1]
        target_start_position = target_anchor_positions[group_index]
        target_end_position = target_anchor_positions[group_index + 1]
        axial_scale = (target_end_position - target_start_position) / (
            source_end_position - source_start_position
        )
        scaled_group = []
        for source_segment in source_group:
            scaled_segment = []
            for source_x, source_y in source_segment:
                source_position = SOURCE_BOTTOM_Y - source_y
                axial_position = (
                    target_start_position + (source_position - source_start_position) * axial_scale
                )
                source_radius = source_x - SOURCE_AXIS_X
                scaled_radius = (
                    target_start_radius + (source_radius - source_start_radius) * radius_scale
                )
                scaled_segment.append((glass_start_x + axial_position, scaled_radius))
            scaled_group.append(tuple(scaled_segment))
        scaled_groups.append(tuple(scaled_group))

    return tuple(scaled_groups)


def _source_profile_groups() -> tuple[tuple[CubicBezier, ...], ...]:
    """Split and reverse the CC0 outer profile into bottom-to-top feature groups."""
    bowl_top, bowl_bottom = _split_cubic_bezier(SOURCE_TOP_TO_BOTTOM_PROFILE[2], SOURCE_BOWL_SPLIT)
    waist_top, waist_bottom = _split_cubic_bezier(
        SOURCE_TOP_TO_BOTTOM_PROFILE[4], SOURCE_WAIST_SPLIT
    )
    base_top, base_bottom = _split_cubic_bezier(SOURCE_TOP_TO_BOTTOM_PROFILE[5], SOURCE_BASE_SPLIT)
    reverse = _reverse_cubic_bezier
    return (
        (reverse(base_bottom),),
        (reverse(base_top), reverse(waist_bottom)),
        (
            reverse(waist_top),
            reverse(SOURCE_TOP_TO_BOTTOM_PROFILE[3]),
            reverse(bowl_bottom),
        ),
        (
            reverse(bowl_top),
            reverse(SOURCE_TOP_TO_BOTTOM_PROFILE[1]),
            reverse(SOURCE_TOP_TO_BOTTOM_PROFILE[0]),
        ),
    )


def _split_cubic_bezier(segment: CubicBezier, parameter: float) -> tuple[CubicBezier, CubicBezier]:
    """Split a cubic Bézier using de Casteljau's construction."""
    start, first_control, second_control, end = segment
    first_edge = _interpolate_point(start, first_control, parameter)
    middle_edge = _interpolate_point(first_control, second_control, parameter)
    final_edge = _interpolate_point(second_control, end, parameter)
    first_inner = _interpolate_point(first_edge, middle_edge, parameter)
    second_inner = _interpolate_point(middle_edge, final_edge, parameter)
    split_point = _interpolate_point(first_inner, second_inner, parameter)
    return (
        (start, first_edge, first_inner, split_point),
        (split_point, second_inner, final_edge, end),
    )


def _reverse_cubic_bezier(segment: CubicBezier) -> CubicBezier:
    return segment[3], segment[2], segment[1], segment[0]


def _interpolate_point(start: Point2D, end: Point2D, parameter: float) -> Point2D:
    return (
        start[0] + (end[0] - start[0]) * parameter,
        start[1] + (end[1] - start[1]) * parameter,
    )


def _validate_parameters(
    *,
    unit_width: int,
    unit_depth: int,
    unit_height: int,
    glass_length_mm: float,
    base_diameter_mm: float,
    waist_diameter_mm: float,
    widest_diameter_mm: float,
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
        ("waist_diameter_mm", waist_diameter_mm),
        ("widest_diameter_mm", widest_diameter_mm),
        ("top_diameter_mm", top_diameter_mm),
        ("pocket_depth_mm", pocket_depth_mm),
        ("wall_thickness_mm", wall_thickness_mm),
    ):
        if value <= 0:
            raise ValueError(f"{name} must be greater than zero.")

    if fit_clearance_mm < 0:
        raise ValueError("fit_clearance_mm must not be negative.")
    if waist_diameter_mm >= base_diameter_mm:
        raise ValueError("waist_diameter_mm must be smaller than base_diameter_mm.")
    if waist_diameter_mm >= top_diameter_mm:
        raise ValueError("waist_diameter_mm must be smaller than top_diameter_mm.")
    if widest_diameter_mm <= max(base_diameter_mm, waist_diameter_mm, top_diameter_mm):
        raise ValueError("widest_diameter_mm must be the largest profile diameter.")
