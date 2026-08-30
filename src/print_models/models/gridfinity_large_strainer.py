"""4x3U Gridfinity holder with staggered large- and medium-strainer cavities."""

from __future__ import annotations

import math

from print_models.models.gridfinity_box import FractionalDividerGridfinityBox

NAME = "gridfinity_large_strainer"
DESCRIPTION = (
    "4x3 Gridfinity holder with staggered contoured cavities for a large and proportionally "
    "scaled medium kitchen strainer."
)
PARAMETERS = {
    "unit_width": 4,
    "unit_depth": 3,
    "unit_height": 4,
    "pocket_depth_mm": 18.0,
    "large_top_lip_diameter_mm": 95.5,
    "large_under_lip_diameter_mm": 87.0,
    "large_bottom_curve_diameter_mm": 82.0,
    "large_bottom_diameter_mm": 68.0,
    "large_strainer_height_mm": 48.2,
    "large_bottom_curve_start_from_top_mm": 42.0,
    "large_lip_thickness_mm": 3.0,
    "medium_top_lip_diameter_mm": 79.3,
    "fit_clearance_mm": 1.0,
    "support_ring_width_mm": 4.0,
    "wall_thickness_mm": 1.0,
}
PRINT_NOTES = (
    "The holder is a 4x3x4U Gridfinity body with two staggered 18 mm blind contoured cavities. "
    "The large cavity preserves the previous measured bowl profile, including its 68 mm flat "
    "bottom and 95.5 mm top lip. The medium cavity scales every bowl dimension by 79.3/95.5, "
    "giving an estimated 56.5 mm flat bottom. Both cavities include 1 mm radial fit clearance."
)

GRIDFINITY_HEIGHT_UNIT_MM = 7.0
BOOLEAN_OVERLAP_MM = 0.2
DEFAULT_DIVIDER_THICKNESS_MM = 1.2
PROFILE_SAMPLE_COUNT = 12


def build(
    unit_width: int = 4,
    unit_depth: int = 3,
    unit_height: int = 4,
    pocket_depth_mm: float = 18.0,
    large_top_lip_diameter_mm: float = 95.5,
    large_under_lip_diameter_mm: float = 87.0,
    large_bottom_curve_diameter_mm: float = 82.0,
    large_bottom_diameter_mm: float = 68.0,
    large_strainer_height_mm: float = 48.2,
    large_bottom_curve_start_from_top_mm: float = 42.0,
    large_lip_thickness_mm: float = 3.0,
    medium_top_lip_diameter_mm: float = 79.3,
    fit_clearance_mm: float = 1.0,
    support_ring_width_mm: float = 4.0,
    wall_thickness_mm: float = 1.0,
):
    """Build a filled 4x3U holder with two staggered contoured blind cavities."""
    from cqgridfinity import GR_BASE_HEIGHT, GR_FLOOR

    _validate_parameters(
        unit_width=unit_width,
        unit_depth=unit_depth,
        unit_height=unit_height,
        pocket_depth_mm=pocket_depth_mm,
        large_top_lip_diameter_mm=large_top_lip_diameter_mm,
        large_under_lip_diameter_mm=large_under_lip_diameter_mm,
        large_bottom_curve_diameter_mm=large_bottom_curve_diameter_mm,
        large_bottom_diameter_mm=large_bottom_diameter_mm,
        large_strainer_height_mm=large_strainer_height_mm,
        large_bottom_curve_start_from_top_mm=large_bottom_curve_start_from_top_mm,
        large_lip_thickness_mm=large_lip_thickness_mm,
        medium_top_lip_diameter_mm=medium_top_lip_diameter_mm,
        fit_clearance_mm=fit_clearance_mm,
        support_ring_width_mm=support_ring_width_mm,
        wall_thickness_mm=wall_thickness_mm,
    )

    box = FractionalDividerGridfinityBox(
        unit_width=unit_width,
        unit_depth=unit_depth,
        unit_height=unit_height,
        horizontal_specs=(),
        vertical_specs=(),
        wall_thickness_mm=wall_thickness_mm,
        divider_thickness_mm=DEFAULT_DIVIDER_THICKNESS_MM,
        scoops=False,
        lip_enabled=True,
    ).render()
    bounding_box = box.val().BoundingBox()

    floor_top_z = GR_BASE_HEIGHT + GR_FLOOR
    support_top_z = unit_height * GRIDFINITY_HEIGHT_UNIT_MM
    pocket_bottom_z = support_top_z - pocket_depth_mm
    if pocket_bottom_z <= floor_top_z - BOOLEAN_OVERLAP_MM:
        raise ValueError("unit_height is too short for the selected pocket_depth_mm.")

    inner_x_min = bounding_box.xmin + wall_thickness_mm
    inner_x_max = bounding_box.xmax - wall_thickness_mm
    inner_y_min = bounding_box.ymin + wall_thickness_mm
    inner_y_max = bounding_box.ymax - wall_thickness_mm

    medium_scale = medium_top_lip_diameter_mm / large_top_lip_diameter_mm
    large_cavity = _build_strainer_cavity(
        item_bottom_z=pocket_bottom_z,
        pocket_depth_mm=pocket_depth_mm,
        top_lip_diameter_mm=large_top_lip_diameter_mm,
        under_lip_diameter_mm=large_under_lip_diameter_mm,
        bottom_curve_diameter_mm=large_bottom_curve_diameter_mm,
        flat_bottom_diameter_mm=large_bottom_diameter_mm,
        strainer_height_mm=large_strainer_height_mm,
        bottom_curve_start_from_top_mm=large_bottom_curve_start_from_top_mm,
        lip_thickness_mm=large_lip_thickness_mm,
        fit_clearance_mm=fit_clearance_mm,
    )
    medium_cavity = _build_strainer_cavity(
        item_bottom_z=pocket_bottom_z,
        pocket_depth_mm=pocket_depth_mm,
        top_lip_diameter_mm=medium_top_lip_diameter_mm,
        under_lip_diameter_mm=large_under_lip_diameter_mm * medium_scale,
        bottom_curve_diameter_mm=large_bottom_curve_diameter_mm * medium_scale,
        flat_bottom_diameter_mm=large_bottom_diameter_mm * medium_scale,
        strainer_height_mm=large_strainer_height_mm * medium_scale,
        bottom_curve_start_from_top_mm=large_bottom_curve_start_from_top_mm * medium_scale,
        lip_thickness_mm=large_lip_thickness_mm * medium_scale,
        fit_clearance_mm=fit_clearance_mm,
    )
    large_radius_mm = large_cavity.val().BoundingBox().xlen / 2.0
    medium_radius_mm = medium_cavity.val().BoundingBox().xlen / 2.0
    large_center, medium_center = _calculate_cutout_centers(
        inner_x_min=inner_x_min,
        inner_x_max=inner_x_max,
        inner_y_min=inner_y_min,
        inner_y_max=inner_y_max,
        large_radius_mm=large_radius_mm,
        medium_radius_mm=medium_radius_mm,
        support_ring_width_mm=support_ring_width_mm,
    )

    surrounding_fill = _build_block(
        x_min=inner_x_min - BOOLEAN_OVERLAP_MM,
        x_max=inner_x_max + BOOLEAN_OVERLAP_MM,
        y_min=inner_y_min - BOOLEAN_OVERLAP_MM,
        y_max=inner_y_max + BOOLEAN_OVERLAP_MM,
        z_min=floor_top_z - BOOLEAN_OVERLAP_MM,
        z_max=support_top_z + BOOLEAN_OVERLAP_MM,
    )
    positioned_large_cavity = large_cavity.translate((large_center[0], large_center[1], 0.0))
    positioned_medium_cavity = medium_cavity.translate((medium_center[0], medium_center[1], 0.0))

    return (
        box.union(surrounding_fill)
        .cut(positioned_large_cavity)
        .cut(positioned_medium_cavity)
        .clean()
    )


def _build_strainer_cavity(
    *,
    item_bottom_z: float,
    pocket_depth_mm: float,
    top_lip_diameter_mm: float,
    under_lip_diameter_mm: float,
    bottom_curve_diameter_mm: float,
    flat_bottom_diameter_mm: float,
    strainer_height_mm: float,
    bottom_curve_start_from_top_mm: float,
    lip_thickness_mm: float,
    fit_clearance_mm: float,
):
    """Build a strainer's measured or proportionally scaled outer-bowl cavity."""
    import cadquery as cq

    cavity_height = pocket_depth_mm + BOOLEAN_OVERLAP_MM
    curve_height = strainer_height_mm - bottom_curve_start_from_top_mm
    under_lip_height = strainer_height_mm - lip_thickness_mm
    curve_points = []
    curve_end_height = min(curve_height, cavity_height)
    for sample_index in range(1, PROFILE_SAMPLE_COUNT + 1):
        height = curve_end_height * sample_index / PROFILE_SAMPLE_COUNT
        curve_points.append(
            (
                _radius_at_height(
                    height,
                    top_lip_diameter_mm=top_lip_diameter_mm,
                    under_lip_diameter_mm=under_lip_diameter_mm,
                    bottom_curve_diameter_mm=bottom_curve_diameter_mm,
                    flat_bottom_diameter_mm=flat_bottom_diameter_mm,
                    strainer_height_mm=strainer_height_mm,
                    curve_height=curve_height,
                    under_lip_height=under_lip_height,
                )
                + fit_clearance_mm,
                item_bottom_z + height,
            )
        )

    profile = (
        cq.Workplane("XZ")
        .moveTo(0.0, item_bottom_z)
        .lineTo(flat_bottom_diameter_mm / 2.0 + fit_clearance_mm, item_bottom_z)
    )
    if curve_points:
        profile = profile.spline(curve_points, includeCurrent=True)
    last_height = curve_end_height
    if under_lip_height < cavity_height and under_lip_height > last_height:
        profile = profile.lineTo(
            _radius_at_height(
                under_lip_height,
                top_lip_diameter_mm=top_lip_diameter_mm,
                under_lip_diameter_mm=under_lip_diameter_mm,
                bottom_curve_diameter_mm=bottom_curve_diameter_mm,
                flat_bottom_diameter_mm=flat_bottom_diameter_mm,
                strainer_height_mm=strainer_height_mm,
                curve_height=curve_height,
                under_lip_height=under_lip_height,
            )
            + fit_clearance_mm,
            item_bottom_z + under_lip_height,
        )
        last_height = under_lip_height
    if cavity_height > last_height:
        profile = profile.lineTo(
            _radius_at_height(
                cavity_height,
                top_lip_diameter_mm=top_lip_diameter_mm,
                under_lip_diameter_mm=under_lip_diameter_mm,
                bottom_curve_diameter_mm=bottom_curve_diameter_mm,
                flat_bottom_diameter_mm=flat_bottom_diameter_mm,
                strainer_height_mm=strainer_height_mm,
                curve_height=curve_height,
                under_lip_height=under_lip_height,
            )
            + fit_clearance_mm,
            item_bottom_z + cavity_height,
        )
    profile = profile.lineTo(0.0, item_bottom_z + cavity_height).close()
    return profile.revolve(360.0, (0.0, 0.0), (0.0, 1.0))


def _radius_at_height(
    height_mm: float,
    *,
    top_lip_diameter_mm: float,
    under_lip_diameter_mm: float,
    bottom_curve_diameter_mm: float,
    flat_bottom_diameter_mm: float,
    strainer_height_mm: float,
    curve_height: float,
    under_lip_height: float,
) -> float:
    """Return the estimated outer radius at a height above the flat bottom."""
    if height_mm <= 0.0:
        return flat_bottom_diameter_mm / 2.0
    if height_mm < curve_height:
        normalized_height = height_mm / curve_height
        blend = math.sin(normalized_height * math.pi / 2.0)
        return (
            flat_bottom_diameter_mm / 2.0
            + (bottom_curve_diameter_mm / 2.0 - flat_bottom_diameter_mm / 2.0) * blend
        )
    if height_mm < under_lip_height:
        normalized_height = (height_mm - curve_height) / (under_lip_height - curve_height)
        return (
            bottom_curve_diameter_mm / 2.0
            + (under_lip_diameter_mm / 2.0 - bottom_curve_diameter_mm / 2.0) * normalized_height
        )
    if height_mm < strainer_height_mm:
        return under_lip_diameter_mm / 2.0 + (
            top_lip_diameter_mm / 2.0 - under_lip_diameter_mm / 2.0
        ) * (height_mm - under_lip_height) / (strainer_height_mm - under_lip_height)
    return top_lip_diameter_mm / 2.0


def _calculate_cutout_centers(
    *,
    inner_x_min: float,
    inner_x_max: float,
    inner_y_min: float,
    inner_y_max: float,
    large_radius_mm: float,
    medium_radius_mm: float,
    support_ring_width_mm: float,
) -> tuple[tuple[float, float], tuple[float, float]]:
    """Place the large cavity at lower left and the medium cavity at upper right."""
    usable_x_min = inner_x_min + support_ring_width_mm
    usable_x_max = inner_x_max - support_ring_width_mm
    usable_y_min = inner_y_min + support_ring_width_mm
    usable_y_max = inner_y_max - support_ring_width_mm

    large_center = (usable_x_min + large_radius_mm, usable_y_min + large_radius_mm)
    medium_center = (usable_x_max - medium_radius_mm, usable_y_max - medium_radius_mm)

    if (
        large_center[0] + large_radius_mm > usable_x_max
        or large_center[1] + large_radius_mm > usable_y_max
        or medium_center[0] - medium_radius_mm < usable_x_min
        or medium_center[1] - medium_radius_mm < usable_y_min
    ):
        raise ValueError("The strainer cavities do not fit within the requested support ring.")

    center_distance_squared = (medium_center[0] - large_center[0]) ** 2 + (
        medium_center[1] - large_center[1]
    ) ** 2
    minimum_distance = large_radius_mm + medium_radius_mm + 2.0 * support_ring_width_mm
    if center_distance_squared < minimum_distance**2:
        raise ValueError("The strainer cavities do not leave enough material between them.")

    return large_center, medium_center


def _build_block(
    *,
    x_min: float,
    x_max: float,
    y_min: float,
    y_max: float,
    z_min: float,
    z_max: float,
):
    import cadquery as cq

    return cq.Workplane("XY", origin=(x_min, y_min, z_min)).box(
        x_max - x_min, y_max - y_min, z_max - z_min, centered=(False, False, False)
    )


def _validate_parameters(
    *,
    unit_width: int,
    unit_depth: int,
    unit_height: int,
    pocket_depth_mm: float,
    large_top_lip_diameter_mm: float,
    large_under_lip_diameter_mm: float,
    large_bottom_curve_diameter_mm: float,
    large_bottom_diameter_mm: float,
    large_strainer_height_mm: float,
    large_bottom_curve_start_from_top_mm: float,
    large_lip_thickness_mm: float,
    medium_top_lip_diameter_mm: float,
    fit_clearance_mm: float,
    support_ring_width_mm: float,
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
        ("pocket_depth_mm", pocket_depth_mm),
        ("large_top_lip_diameter_mm", large_top_lip_diameter_mm),
        ("large_under_lip_diameter_mm", large_under_lip_diameter_mm),
        ("large_bottom_curve_diameter_mm", large_bottom_curve_diameter_mm),
        ("large_bottom_diameter_mm", large_bottom_diameter_mm),
        ("large_strainer_height_mm", large_strainer_height_mm),
        ("large_bottom_curve_start_from_top_mm", large_bottom_curve_start_from_top_mm),
        ("large_lip_thickness_mm", large_lip_thickness_mm),
        ("medium_top_lip_diameter_mm", medium_top_lip_diameter_mm),
        ("wall_thickness_mm", wall_thickness_mm),
    ):
        if value <= 0:
            raise ValueError(f"{name} must be greater than zero.")

    for name, value in (
        ("fit_clearance_mm", fit_clearance_mm),
        ("support_ring_width_mm", support_ring_width_mm),
    ):
        if value < 0:
            raise ValueError(f"{name} must not be negative.")

    if unit_width < 4 or unit_depth < 3 or unit_height < 4:
        raise ValueError("The dual strainer holder requires at least a 4x3x4U footprint.")
    if medium_top_lip_diameter_mm >= large_top_lip_diameter_mm:
        raise ValueError("medium_top_lip_diameter_mm must be smaller than the large top lip.")
    if large_under_lip_diameter_mm <= large_bottom_curve_diameter_mm:
        raise ValueError("large_under_lip_diameter_mm must exceed the bottom curve diameter.")
    if large_top_lip_diameter_mm <= large_under_lip_diameter_mm:
        raise ValueError("large_top_lip_diameter_mm must exceed the under-lip diameter.")
    if large_bottom_curve_diameter_mm <= large_bottom_diameter_mm:
        raise ValueError("large_bottom_curve_diameter_mm must exceed the bottom diameter.")
    if large_bottom_curve_start_from_top_mm >= large_strainer_height_mm:
        raise ValueError("The large bottom curve start must be below the strainer height.")
    curve_height = large_strainer_height_mm - large_bottom_curve_start_from_top_mm
    if large_lip_thickness_mm >= curve_height:
        raise ValueError("large_lip_thickness_mm leaves no room for the tapered bowl wall.")
    medium_scale = medium_top_lip_diameter_mm / large_top_lip_diameter_mm
    if pocket_depth_mm > large_strainer_height_mm * medium_scale:
        raise ValueError("pocket_depth_mm must not exceed the scaled medium strainer height.")
