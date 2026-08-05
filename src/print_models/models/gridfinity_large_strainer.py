"""4U divided Gridfinity holder for a large rounded kitchen strainer."""

from __future__ import annotations

import math

from print_models.models.gridfinity_box import DividerSpec, FractionalDividerGridfinityBox

NAME = "gridfinity_large_strainer"
DESCRIPTION = (
    "3x5 Gridfinity holder for a large strainer with a filled circular-cutout section and an "
    "open lower compartment."
)
PARAMETERS = {
    "unit_width": 3,
    "unit_depth": 5,
    "unit_height": 4,
    "pocket_depth_mm": 18.0,
    "overall_length_mm": 215.5,
    "top_lip_diameter_mm": 95.5,
    "under_lip_diameter_mm": 87.0,
    "bottom_curve_diameter_mm": 82.0,
    "flat_bottom_diameter_mm": 68.0,
    "strainer_height_mm": 48.2,
    "bottom_curve_start_from_top_mm": 42.0,
    "lip_thickness_mm": 3.0,
    "handle_width_mm": 28.0,
    "strainer_rotation_degrees": 0.0,
    "divider_position_u": 2.6,
    "fit_clearance_mm": 1.0,
    "layout_clearance_mm": 1.0,
    "bottom_clearance_mm": 0.4,
    "support_ring_width_mm": 4.0,
    "handle_relief_overlap_mm": 4.0,
    "wall_thickness_mm": 1.0,
    "divider_thickness_mm": 1.2,
}
PRINT_NOTES = (
    "The holder is a 3x5x4U Gridfinity body with the 5U axis running top-to-bottom. The horizontal "
    "divider spans the 3U width at 2.6U from the bottom, or 2.4U from the top. The top section is "
    "filled around an 18 mm circular bowl cutout, while the lower section remains an open usable "
    "compartment. The footprint is 125.5 x 209.5 mm. The socket follows the measured 95.5 mm lip, "
    "87 mm under-lip body, 82 mm curve-transition diameter, and 48.2 mm overall height. The 68 mm "
    "flat-bottom diameter remains an adjustable photo-based estimate."
)

GRIDFINITY_GRID_UNIT_MM = 42.0
GRIDFINITY_HEIGHT_UNIT_MM = 7.0
PROFILE_SAMPLE_COUNT = 12
BOOLEAN_OVERLAP_MM = 0.2
LAYOUT_TOLERANCE_MM = 1e-6


def build(
    unit_width: int = 3,
    unit_depth: int = 5,
    unit_height: int = 4,
    pocket_depth_mm: float = 18.0,
    overall_length_mm: float = 215.5,
    top_lip_diameter_mm: float = 95.5,
    under_lip_diameter_mm: float = 87.0,
    bottom_curve_diameter_mm: float = 82.0,
    flat_bottom_diameter_mm: float = 68.0,
    strainer_height_mm: float = 48.2,
    bottom_curve_start_from_top_mm: float = 42.0,
    lip_thickness_mm: float = 3.0,
    handle_width_mm: float = 28.0,
    strainer_rotation_degrees: float = 0.0,
    divider_position_u: float = 2.6,
    fit_clearance_mm: float = 1.0,
    layout_clearance_mm: float = 1.0,
    bottom_clearance_mm: float = 0.4,
    support_ring_width_mm: float = 4.0,
    handle_relief_overlap_mm: float = 4.0,
    wall_thickness_mm: float = 1.0,
    divider_thickness_mm: float = 1.2,
):
    """Build a 4U divided holder with a filled top circular socket and open bottom compartment."""
    from cqgridfinity import GR_BASE_HEIGHT, GR_FLOOR

    _validate_parameters(
        unit_width=unit_width,
        unit_depth=unit_depth,
        unit_height=unit_height,
        pocket_depth_mm=pocket_depth_mm,
        overall_length_mm=overall_length_mm,
        top_lip_diameter_mm=top_lip_diameter_mm,
        under_lip_diameter_mm=under_lip_diameter_mm,
        bottom_curve_diameter_mm=bottom_curve_diameter_mm,
        flat_bottom_diameter_mm=flat_bottom_diameter_mm,
        strainer_height_mm=strainer_height_mm,
        bottom_curve_start_from_top_mm=bottom_curve_start_from_top_mm,
        lip_thickness_mm=lip_thickness_mm,
        handle_width_mm=handle_width_mm,
        strainer_rotation_degrees=strainer_rotation_degrees,
        divider_position_u=divider_position_u,
        fit_clearance_mm=fit_clearance_mm,
        layout_clearance_mm=layout_clearance_mm,
        bottom_clearance_mm=bottom_clearance_mm,
        support_ring_width_mm=support_ring_width_mm,
        handle_relief_overlap_mm=handle_relief_overlap_mm,
        wall_thickness_mm=wall_thickness_mm,
        divider_thickness_mm=divider_thickness_mm,
    )

    horizontal_specs = (
        DividerSpec(
            position_u=divider_position_u,
            span_start_u=0.0,
            span_end_u=float(unit_width),
        ),
    )
    box = FractionalDividerGridfinityBox(
        unit_width=unit_width,
        unit_depth=unit_depth,
        unit_height=unit_height,
        horizontal_specs=horizontal_specs,
        vertical_specs=(),
        wall_thickness_mm=wall_thickness_mm,
        divider_thickness_mm=divider_thickness_mm,
        scoops=False,
        lip_enabled=True,
    ).render()
    bounding_box = box.val().BoundingBox()

    floor_top_z = GR_BASE_HEIGHT + GR_FLOOR
    support_top_z = unit_height * GRIDFINITY_HEIGHT_UNIT_MM
    item_bottom_z = support_top_z - pocket_depth_mm
    if item_bottom_z <= floor_top_z - BOOLEAN_OVERLAP_MM:
        raise ValueError("unit_height is too short for the selected pocket_depth_mm.")

    inner_x_min = bounding_box.xmin + wall_thickness_mm
    inner_x_max = bounding_box.xmax - wall_thickness_mm
    inner_y_min = bounding_box.ymin + wall_thickness_mm
    inner_y_max = bounding_box.ymax - wall_thickness_mm
    divider_center_y = divider_position_u * GRIDFINITY_GRID_UNIT_MM + inner_y_min
    divider_top_y = divider_center_y + divider_thickness_mm / 2.0
    top_compartment_min_y = divider_top_y + BOOLEAN_OVERLAP_MM
    bowl_center_x = (inner_x_min + inner_x_max) / 2.0
    bowl_center_y = (top_compartment_min_y + inner_y_max) / 2.0

    bowl_cavity = _build_strainer_cavity(
        item_bottom_z=item_bottom_z,
        pocket_depth_mm=pocket_depth_mm,
        top_lip_diameter_mm=top_lip_diameter_mm,
        under_lip_diameter_mm=under_lip_diameter_mm,
        bottom_curve_diameter_mm=bottom_curve_diameter_mm,
        flat_bottom_diameter_mm=flat_bottom_diameter_mm,
        strainer_height_mm=strainer_height_mm,
        bottom_curve_start_from_top_mm=bottom_curve_start_from_top_mm,
        lip_thickness_mm=lip_thickness_mm,
        fit_clearance_mm=fit_clearance_mm,
        center_x=bowl_center_x,
    )
    positioned_cavity = bowl_cavity.translate((0.0, bowl_center_y, 0.0))
    cavity_bounds = positioned_cavity.val().BoundingBox()
    if (
        cavity_bounds.xmin < inner_x_min + support_ring_width_mm
        or cavity_bounds.xmax > inner_x_max - support_ring_width_mm
        or cavity_bounds.ymin < top_compartment_min_y + support_ring_width_mm
        or cavity_bounds.ymax > inner_y_max - support_ring_width_mm
    ):
        raise ValueError("The circular cavity does not leave the requested surrounding deck ring.")

    surrounding_fill = _build_block(
        x_min=inner_x_min - BOOLEAN_OVERLAP_MM,
        x_max=inner_x_max + BOOLEAN_OVERLAP_MM,
        y_min=top_compartment_min_y - BOOLEAN_OVERLAP_MM,
        y_max=inner_y_max + BOOLEAN_OVERLAP_MM,
        z_min=floor_top_z - BOOLEAN_OVERLAP_MM,
        z_max=support_top_z + BOOLEAN_OVERLAP_MM,
    )
    return box.union(surrounding_fill).cut(positioned_cavity).clean()


def _build_strainer_plan_envelope(
    *,
    object_start_x: float,
    bowl_left_x: float,
    bowl_center_x: float,
    top_lip_diameter_mm: float,
    handle_width_mm: float,
    layout_clearance_mm: float,
):
    """Build the rounded top-view envelope used to place the strainer diagonally."""
    handle_diameter = handle_width_mm + 2.0 * layout_clearance_mm
    handle = _build_capsule(
        start_x=object_start_x,
        end_x=bowl_left_x,
        diameter_mm=handle_diameter,
        bottom_z=0.0,
        top_z=0.1,
    )
    bowl = (
        cq_workplane()
        .center(bowl_center_x, 0.0)
        .circle(top_lip_diameter_mm / 2.0 + layout_clearance_mm)
        .extrude(0.1)
    )
    return handle.union(bowl).clean()


def _position_plan_shape(
    shape,
    *,
    rotation_degrees: float,
    inner_x_min: float,
    inner_x_max: float,
    inner_y_min: float,
    inner_y_max: float,
):
    """Rotate and center a plan envelope inside the usable Gridfinity interior."""
    rotated = shape.rotate((0.0, 0.0, 0.0), (0.0, 0.0, 1.0), rotation_degrees)
    rotated_bounds = rotated.val().BoundingBox()
    available_width = inner_x_max - inner_x_min
    available_depth = inner_y_max - inner_y_min
    if rotated_bounds.xlen > available_width or rotated_bounds.ylen > available_depth:
        raise ValueError(
            "The diagonal large-strainer envelope does not fit the selected footprint."
        )
    plan_x = (inner_x_min + inner_x_max - rotated_bounds.xmin - rotated_bounds.xmax) / 2.0
    plan_y = (inner_y_min + inner_y_max - rotated_bounds.ymin - rotated_bounds.ymax) / 2.0
    return rotated.translate((plan_x, plan_y, 0.0)), plan_x, plan_y


def _position_shape(shape, *, rotation_degrees: float, translation: tuple[float, float, float]):
    return shape.rotate((0.0, 0.0, 0.0), (0.0, 0.0, 1.0), rotation_degrees).translate(translation)


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
    center_x: float,
):
    """Build the measured outer-bowl volume used to subtract the recessed socket."""
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
    return profile.revolve(360.0, (0.0, 0.0), (0.0, 1.0)).translate((center_x, 0.0, 0.0))


def _build_handle_relief(
    *,
    object_start_x: float,
    bowl_center_x: float,
    top_lip_diameter_mm: float,
    handle_width_mm: float,
    handle_relief_overlap_mm: float,
    fit_clearance_mm: float,
    bottom_z: float,
    top_z: float,
):
    """Clear the handle's projected path from the edge of the bowl support pod."""
    return _build_block(
        x_min=object_start_x - fit_clearance_mm,
        x_max=bowl_center_x - top_lip_diameter_mm / 2.0 + handle_relief_overlap_mm,
        y_min=-handle_width_mm / 2.0 - fit_clearance_mm,
        y_max=handle_width_mm / 2.0 + fit_clearance_mm,
        z_min=bottom_z,
        z_max=top_z,
    )


def _build_capsule(
    *,
    start_x: float,
    end_x: float,
    diameter_mm: float,
    bottom_z: float,
    top_z: float,
):
    """Build a capsule whose endpoints are the outside bounds, not cap centers."""
    radius = diameter_mm / 2.0
    straight_length = end_x - start_x - diameter_mm
    height_mm = top_z - bottom_z
    if straight_length <= 0:
        return (
            cq_workplane(origin=(start_x + (end_x - start_x) / 2.0, 0.0, bottom_z))
            .circle((end_x - start_x) / 2.0)
            .extrude(height_mm)
        )
    body = cq_workplane(origin=((start_x + end_x) / 2.0, 0.0, bottom_z)).box(
        straight_length, diameter_mm, height_mm, centered=(True, True, False)
    )
    start_cap = (
        cq_workplane(origin=(start_x + radius, 0.0, bottom_z)).circle(radius).extrude(height_mm)
    )
    end_cap = cq_workplane(origin=(end_x - radius, 0.0, bottom_z)).circle(radius).extrude(height_mm)
    return body.union(start_cap).union(end_cap).clean()


def cq_workplane(*, origin: tuple[float, float, float] = (0.0, 0.0, 0.0)):
    import cadquery as cq

    return cq.Workplane("XY", origin=origin)


def _build_block(
    *,
    x_min: float,
    x_max: float,
    y_min: float,
    y_max: float,
    z_min: float,
    z_max: float,
):
    return (
        cq_workplane()
        .box(x_max - x_min, y_max - y_min, z_max - z_min)
        .translate(
            (
                (x_min + x_max) / 2.0,
                (y_min + y_max) / 2.0,
                (z_min + z_max) / 2.0,
            )
        )
    )


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


def _validate_parameters(
    *,
    unit_width: int,
    unit_depth: int,
    unit_height: int,
    pocket_depth_mm: float,
    overall_length_mm: float,
    top_lip_diameter_mm: float,
    under_lip_diameter_mm: float,
    bottom_curve_diameter_mm: float,
    flat_bottom_diameter_mm: float,
    strainer_height_mm: float,
    bottom_curve_start_from_top_mm: float,
    lip_thickness_mm: float,
    handle_width_mm: float,
    strainer_rotation_degrees: float,
    divider_position_u: float,
    fit_clearance_mm: float,
    layout_clearance_mm: float,
    bottom_clearance_mm: float,
    support_ring_width_mm: float,
    handle_relief_overlap_mm: float,
    wall_thickness_mm: float,
    divider_thickness_mm: float,
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
        ("overall_length_mm", overall_length_mm),
        ("top_lip_diameter_mm", top_lip_diameter_mm),
        ("under_lip_diameter_mm", under_lip_diameter_mm),
        ("bottom_curve_diameter_mm", bottom_curve_diameter_mm),
        ("flat_bottom_diameter_mm", flat_bottom_diameter_mm),
        ("strainer_height_mm", strainer_height_mm),
        ("bottom_curve_start_from_top_mm", bottom_curve_start_from_top_mm),
        ("lip_thickness_mm", lip_thickness_mm),
        ("handle_width_mm", handle_width_mm),
        ("wall_thickness_mm", wall_thickness_mm),
        ("divider_thickness_mm", divider_thickness_mm),
    ):
        if value <= 0:
            raise ValueError(f"{name} must be greater than zero.")

    for name, value in (
        ("fit_clearance_mm", fit_clearance_mm),
        ("layout_clearance_mm", layout_clearance_mm),
        ("bottom_clearance_mm", bottom_clearance_mm),
        ("support_ring_width_mm", support_ring_width_mm),
        ("handle_relief_overlap_mm", handle_relief_overlap_mm),
    ):
        if value < 0:
            raise ValueError(f"{name} must not be negative.")

    if unit_width < 3 or unit_depth < 5 or unit_height < 4:
        raise ValueError("The large strainer holder requires at least a 3x5x4U footprint.")
    if divider_position_u <= 0 or divider_position_u >= unit_depth:
        raise ValueError("divider_position_u must lie strictly inside the Gridfinity depth.")
    if abs(strainer_rotation_degrees) >= 90.0:
        raise ValueError("strainer_rotation_degrees must remain between -90 and 90 degrees.")
    if under_lip_diameter_mm <= bottom_curve_diameter_mm:
        raise ValueError("under_lip_diameter_mm must exceed bottom_curve_diameter_mm.")
    if top_lip_diameter_mm <= under_lip_diameter_mm:
        raise ValueError("top_lip_diameter_mm must exceed under_lip_diameter_mm.")
    if bottom_curve_diameter_mm <= flat_bottom_diameter_mm:
        raise ValueError("bottom_curve_diameter_mm must exceed flat_bottom_diameter_mm.")
    if bottom_curve_start_from_top_mm >= strainer_height_mm:
        raise ValueError("bottom_curve_start_from_top_mm must be below strainer_height_mm.")
    if lip_thickness_mm >= strainer_height_mm - bottom_curve_start_from_top_mm:
        raise ValueError("lip_thickness_mm leaves no room for the tapered bowl wall.")
    if pocket_depth_mm > strainer_height_mm:
        raise ValueError("pocket_depth_mm must not exceed strainer_height_mm.")
    if overall_length_mm <= top_lip_diameter_mm:
        raise ValueError("overall_length_mm must leave room for the handle beyond the bowl.")
    if divider_thickness_mm >= divider_position_u * GRIDFINITY_GRID_UNIT_MM:
        raise ValueError("divider_position_u leaves insufficient room for divider thickness.")
    if divider_thickness_mm >= (unit_depth - divider_position_u) * GRIDFINITY_GRID_UNIT_MM:
        raise ValueError(
            "divider_position_u leaves insufficient room for the opposite compartment."
        )
