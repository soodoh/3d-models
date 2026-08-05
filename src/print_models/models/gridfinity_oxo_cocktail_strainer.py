"""Support-free face-down 3x5 Gridfinity holder for an OXO cocktail strainer."""

from __future__ import annotations

from print_models.models.gridfinity_box import FractionalDividerGridfinityBox

NAME = "gridfinity_oxo_cocktail_strainer"
DESCRIPTION = "Face-down OXO cocktail-strainer holder with a straight 18 mm pocket and 4U walls."
PARAMETERS = {
    "unit_width": 5,
    "unit_depth": 3,
    "unit_height": 4,
    "pocket_depth_mm": 18.0,
    "overall_length_mm": 214.0,
    "strainer_diameter_mm": 82.0,
    "small_handle_width_mm": 17.7,
    "wide_handle_width_mm": 26.0,
    "wide_handle_length_mm": 73.0,
    "wide_handle_straight_length_mm": 64.0,
    "thick_handle_height_mm": 12.7,
    "small_handle_height_mm": 3.5,
    "finger_scoop_diameter_mm": 20.0,
    "tip_loop_length_mm": 15.0,
    "tip_loop_outer_width_mm": 33.0,
    "strainer_rotation_degrees": 24.7,
    "fit_clearance_mm": 1.0,
    "wall_thickness_mm": 1.0,
}
PRINT_NOTES = (
    "The strainer drops in with its open face downward and its mesh dome upward. A straight-sided "
    "18 mm pocket follows the full rim, dual-rail handle, measured 73 x 26 mm thick-handle "
    "footprint, and the full outer tip-loop footprint, avoiding an insertion-blocking undercut. "
    "Paired rounded finger scoops beside the wide handle provide pinch access for removal. The "
    "strainer is turned 24.7 degrees to fit the 3x5 footprint with 1 mm clearance. The printed "
    "holder remains entirely within the normal 4U Gridfinity height and has no elevated supports."
)

GRIDFINITY_HEIGHT_UNIT_MM = 7.0
MINIMUM_CAVITY_FLOOR_MM = 2.0
BOOLEAN_OVERLAP_MM = 0.2
HANDLE_PROFILE_OVERLAP_MM = 1.0
TIP_LOOP_ATTACHMENT_OVERLAP_MM = 4.0


def build(
    unit_width: int = 5,
    unit_depth: int = 3,
    unit_height: int = 4,
    pocket_depth_mm: float = 18.0,
    overall_length_mm: float = 214.0,
    strainer_diameter_mm: float = 82.0,
    small_handle_width_mm: float = 17.7,
    wide_handle_width_mm: float = 26.0,
    wide_handle_length_mm: float = 73.0,
    wide_handle_straight_length_mm: float = 64.0,
    thick_handle_height_mm: float = 12.7,
    small_handle_height_mm: float = 3.5,
    finger_scoop_diameter_mm: float = 20.0,
    tip_loop_length_mm: float = 15.0,
    tip_loop_outer_width_mm: float = 33.0,
    strainer_rotation_degrees: float = 24.7,
    fit_clearance_mm: float = 1.0,
    wall_thickness_mm: float = 1.0,
):
    """Build one straight-walled face-down silhouette pocket in a filled 4U box."""
    from cqgridfinity import GR_BASE_HEIGHT, GR_FLOOR

    _validate_parameters(
        unit_width=unit_width,
        unit_depth=unit_depth,
        unit_height=unit_height,
        pocket_depth_mm=pocket_depth_mm,
        overall_length_mm=overall_length_mm,
        strainer_diameter_mm=strainer_diameter_mm,
        small_handle_width_mm=small_handle_width_mm,
        wide_handle_width_mm=wide_handle_width_mm,
        wide_handle_length_mm=wide_handle_length_mm,
        wide_handle_straight_length_mm=wide_handle_straight_length_mm,
        thick_handle_height_mm=thick_handle_height_mm,
        small_handle_height_mm=small_handle_height_mm,
        finger_scoop_diameter_mm=finger_scoop_diameter_mm,
        tip_loop_length_mm=tip_loop_length_mm,
        tip_loop_outer_width_mm=tip_loop_outer_width_mm,
        strainer_rotation_degrees=strainer_rotation_degrees,
        fit_clearance_mm=fit_clearance_mm,
        wall_thickness_mm=wall_thickness_mm,
    )

    floor_top_z = GR_BASE_HEIGHT + GR_FLOOR
    deck_top_z = unit_height * GRIDFINITY_HEIGHT_UNIT_MM
    pocket_bottom_z = deck_top_z - pocket_depth_mm
    if pocket_bottom_z - floor_top_z < MINIMUM_CAVITY_FLOOR_MM:
        raise ValueError(
            "unit_height is too short for pocket_depth_mm while preserving a "
            f"{MINIMUM_CAVITY_FLOOR_MM:g} mm cavity floor."
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
    inner_x_min = bounding_box.xmin + wall_thickness_mm
    inner_x_max = bounding_box.xmax - wall_thickness_mm
    inner_y_min = bounding_box.ymin + wall_thickness_mm
    inner_y_max = bounding_box.ymax - wall_thickness_mm

    raw_cutter = _build_face_down_pocket_cutter(
        pocket_bottom_z=pocket_bottom_z,
        deck_top_z=deck_top_z,
        overall_length_mm=overall_length_mm,
        strainer_diameter_mm=strainer_diameter_mm,
        small_handle_width_mm=small_handle_width_mm,
        wide_handle_width_mm=wide_handle_width_mm,
        wide_handle_length_mm=wide_handle_length_mm,
        wide_handle_straight_length_mm=wide_handle_straight_length_mm,
        small_handle_height_mm=small_handle_height_mm,
        finger_scoop_diameter_mm=finger_scoop_diameter_mm,
        tip_loop_length_mm=tip_loop_length_mm,
        tip_loop_outer_width_mm=tip_loop_outer_width_mm,
        fit_clearance_mm=fit_clearance_mm,
    )
    cutter, _, _ = _position_plan_cutter(
        raw_cutter,
        rotation_degrees=strainer_rotation_degrees,
        inner_x_min=inner_x_min,
        inner_x_max=inner_x_max,
        inner_y_min=inner_y_min,
        inner_y_max=inner_y_max,
    )

    insert_fill = _build_block(
        x_min=inner_x_min,
        x_max=inner_x_max,
        y_min=inner_y_min,
        y_max=inner_y_max,
        z_min=floor_top_z - BOOLEAN_OVERLAP_MM,
        z_max=deck_top_z,
    )
    return box.union(insert_fill).cut(cutter).clean()


def _build_face_down_pocket_cutter(
    *,
    pocket_bottom_z: float,
    deck_top_z: float,
    overall_length_mm: float,
    strainer_diameter_mm: float,
    small_handle_width_mm: float,
    wide_handle_width_mm: float,
    wide_handle_length_mm: float,
    wide_handle_straight_length_mm: float,
    small_handle_height_mm: float,
    finger_scoop_diameter_mm: float,
    tip_loop_length_mm: float,
    tip_loop_outer_width_mm: float,
    fit_clearance_mm: float,
):
    """Extrude the complete insertion silhouette with no undercuts or stepped floors."""
    import cadquery as cq

    object_start_x = -overall_length_mm / 2.0
    object_end_x = overall_length_mm / 2.0
    strainer_radius_mm = strainer_diameter_mm / 2.0
    bowl_center_x = object_end_x - tip_loop_length_mm - strainer_radius_mm
    bowl_left_x = bowl_center_x - strainer_radius_mm
    bowl_right_x = bowl_center_x + strainer_radius_mm
    wide_handle_end_x = object_start_x + wide_handle_length_mm
    cutter_top_z = deck_top_z + BOOLEAN_OVERLAP_MM

    bowl = (
        cq.Workplane("XY", origin=(bowl_center_x, 0.0, pocket_bottom_z))
        .circle(strainer_radius_mm + fit_clearance_mm)
        .extrude(cutter_top_z - pocket_bottom_z)
    )
    wide_handle = _build_wide_handle_cutter(
        start_x=object_start_x,
        end_x=wide_handle_end_x,
        wide_handle_width_mm=wide_handle_width_mm,
        wide_handle_straight_length_mm=wide_handle_straight_length_mm,
        bottom_z=pocket_bottom_z,
        top_z=cutter_top_z,
        fit_clearance_mm=fit_clearance_mm,
    )
    finger_scoops = _build_finger_scoop_cutters(
        center_x=object_start_x + wide_handle_length_mm * 0.45,
        handle_width_mm=wide_handle_width_mm + 2.0 * fit_clearance_mm,
        diameter_mm=finger_scoop_diameter_mm,
        bottom_z=pocket_bottom_z,
        top_z=cutter_top_z,
    )
    small_handle = _build_parallel_rail_cutter(
        start_x=wide_handle_end_x - HANDLE_PROFILE_OVERLAP_MM,
        end_x=bowl_left_x + HANDLE_PROFILE_OVERLAP_MM,
        outer_width_mm=small_handle_width_mm,
        rail_diameter_mm=small_handle_height_mm,
        bottom_z=pocket_bottom_z,
        top_z=cutter_top_z,
        fit_clearance_mm=fit_clearance_mm,
    )
    tip_loop = _build_tip_loop_cutter(
        attachment_x=bowl_right_x - TIP_LOOP_ATTACHMENT_OVERLAP_MM,
        object_end_x=object_end_x,
        outer_width_mm=tip_loop_outer_width_mm,
        bottom_z=pocket_bottom_z,
        top_z=cutter_top_z,
        fit_clearance_mm=fit_clearance_mm,
    )
    return bowl.union(wide_handle).union(finger_scoops).union(small_handle).union(tip_loop).clean()


def _position_plan_cutter(
    cutter,
    *,
    rotation_degrees: float,
    inner_x_min: float,
    inner_x_max: float,
    inner_y_min: float,
    inner_y_max: float,
):
    """Rotate and center the cleared insertion silhouette in the Gridfinity interior."""
    rotated_cutter = cutter.rotate(
        (0.0, 0.0, 0.0),
        (0.0, 0.0, 1.0),
        rotation_degrees,
    )
    rotated_bounds = rotated_cutter.val().BoundingBox()
    available_width = inner_x_max - inner_x_min
    available_depth = inner_y_max - inner_y_min
    if rotated_bounds.xlen > available_width or rotated_bounds.ylen > available_depth:
        raise ValueError("The face-down strainer does not fit the selected Gridfinity footprint.")

    plan_x = (inner_x_min + inner_x_max - rotated_bounds.xmin - rotated_bounds.xmax) / 2.0
    plan_y = (inner_y_min + inner_y_max - rotated_bounds.ymin - rotated_bounds.ymax) / 2.0
    return rotated_cutter.translate((plan_x, plan_y, 0.0)), plan_x, plan_y


def _build_wide_handle_cutter(
    *,
    start_x: float,
    end_x: float,
    wide_handle_width_mm: float,
    wide_handle_straight_length_mm: float,
    bottom_z: float,
    top_z: float,
    fit_clearance_mm: float,
):
    """Build the measured thick-handle footprint with shallow elliptical end curves."""
    import cadquery as cq

    physical_length_mm = end_x - start_x
    end_curve_depth_mm = (physical_length_mm - wide_handle_straight_length_mm) / 2.0
    cleared_width_mm = wide_handle_width_mm + 2.0 * fit_clearance_mm
    cleared_end_curve_depth_mm = end_curve_depth_mm + fit_clearance_mm
    start_curve_center_x = start_x + end_curve_depth_mm
    end_curve_center_x = end_x - end_curve_depth_mm
    center_x = (start_curve_center_x + end_curve_center_x) / 2.0
    height_mm = top_z - bottom_z

    body = (
        cq.Workplane("XY", origin=(center_x, 0.0, bottom_z))
        .rect(wide_handle_straight_length_mm, cleared_width_mm)
        .extrude(height_mm)
    )
    start_curve = (
        cq.Workplane("XY", origin=(start_curve_center_x, 0.0, bottom_z))
        .ellipse(cleared_end_curve_depth_mm, cleared_width_mm / 2.0)
        .extrude(height_mm)
    )
    end_curve = (
        cq.Workplane("XY", origin=(end_curve_center_x, 0.0, bottom_z))
        .ellipse(cleared_end_curve_depth_mm, cleared_width_mm / 2.0)
        .extrude(height_mm)
    )
    return body.union(start_curve).union(end_curve).clean()


def _build_finger_scoop_cutters(
    *,
    center_x: float,
    handle_width_mm: float,
    diameter_mm: float,
    bottom_z: float,
    top_z: float,
):
    """Build paired round pinch-access pockets overlapping the wide handle recess."""
    import cadquery as cq

    radius = diameter_mm / 2.0
    center_offset_y = handle_width_mm / 2.0 + diameter_mm * 0.3
    height_mm = top_z - bottom_z
    first_scoop = (
        cq.Workplane("XY", origin=(center_x, -center_offset_y, bottom_z))
        .circle(radius)
        .extrude(height_mm)
    )
    second_scoop = (
        cq.Workplane("XY", origin=(center_x, center_offset_y, bottom_z))
        .circle(radius)
        .extrude(height_mm)
    )
    return first_scoop.union(second_scoop).clean()


def _build_parallel_rail_cutter(
    *,
    start_x: float,
    end_x: float,
    outer_width_mm: float,
    rail_diameter_mm: float,
    bottom_z: float,
    top_z: float,
    fit_clearance_mm: float,
):
    """Build separate vertical-wall recesses for the two metal handle rails."""
    rail_center_offset = (outer_width_mm - rail_diameter_mm) / 2.0
    cleared_rail_diameter = rail_diameter_mm + 2.0 * fit_clearance_mm
    first_rail = _build_capsule_cutter(
        start_x=start_x - fit_clearance_mm,
        end_x=end_x + fit_clearance_mm,
        center_y=-rail_center_offset,
        diameter_mm=cleared_rail_diameter,
        bottom_z=bottom_z,
        top_z=top_z,
    )
    second_rail = _build_capsule_cutter(
        start_x=start_x - fit_clearance_mm,
        end_x=end_x + fit_clearance_mm,
        center_y=rail_center_offset,
        diameter_mm=cleared_rail_diameter,
        bottom_z=bottom_z,
        top_z=top_z,
    )
    return first_rail.union(second_rail).clean()


def _build_tip_loop_cutter(
    *,
    attachment_x: float,
    object_end_x: float,
    outer_width_mm: float,
    bottom_z: float,
    top_z: float,
    fit_clearance_mm: float,
):
    """Build a full-depth recess for the complete outer footprint of the tip loop."""
    import cadquery as cq

    height_mm = top_z - bottom_z
    outer_x_radius = object_end_x - attachment_x + fit_clearance_mm
    outer_y_radius = outer_width_mm / 2.0 + fit_clearance_mm
    outer = (
        cq.Workplane("XY", origin=(attachment_x, 0.0, bottom_z))
        .ellipse(outer_x_radius, outer_y_radius)
        .extrude(height_mm)
    )
    right_half = _build_block(
        x_min=attachment_x - BOOLEAN_OVERLAP_MM,
        x_max=attachment_x + outer_x_radius + BOOLEAN_OVERLAP_MM,
        y_min=-outer_y_radius - BOOLEAN_OVERLAP_MM,
        y_max=outer_y_radius + BOOLEAN_OVERLAP_MM,
        z_min=bottom_z - BOOLEAN_OVERLAP_MM,
        z_max=top_z + BOOLEAN_OVERLAP_MM,
    )
    return outer.intersect(right_half).clean()


def _build_capsule_cutter(
    *,
    start_x: float,
    end_x: float,
    center_y: float,
    diameter_mm: float,
    bottom_z: float,
    top_z: float,
):
    import cadquery as cq

    radius = diameter_mm / 2.0
    height_mm = top_z - bottom_z
    straight_length = end_x - start_x - diameter_mm
    center_x = (start_x + end_x) / 2.0
    body = (
        cq.Workplane("XY", origin=(center_x, center_y, bottom_z))
        .rect(straight_length, diameter_mm)
        .extrude(height_mm)
    )
    start_cap = (
        cq.Workplane("XY", origin=(start_x + radius, center_y, bottom_z))
        .circle(radius)
        .extrude(height_mm)
    )
    end_cap = (
        cq.Workplane("XY", origin=(end_x - radius, center_y, bottom_z))
        .circle(radius)
        .extrude(height_mm)
    )
    return body.union(start_cap).union(end_cap).clean()


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

    return (
        cq.Workplane("XY")
        .box(x_max - x_min, y_max - y_min, z_max - z_min)
        .translate(
            (
                (x_min + x_max) / 2.0,
                (y_min + y_max) / 2.0,
                (z_min + z_max) / 2.0,
            )
        )
    )


def _validate_parameters(
    *,
    unit_width: int,
    unit_depth: int,
    unit_height: int,
    pocket_depth_mm: float,
    overall_length_mm: float,
    strainer_diameter_mm: float,
    small_handle_width_mm: float,
    wide_handle_width_mm: float,
    wide_handle_length_mm: float,
    wide_handle_straight_length_mm: float,
    thick_handle_height_mm: float,
    small_handle_height_mm: float,
    finger_scoop_diameter_mm: float,
    tip_loop_length_mm: float,
    tip_loop_outer_width_mm: float,
    strainer_rotation_degrees: float,
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
        ("pocket_depth_mm", pocket_depth_mm),
        ("overall_length_mm", overall_length_mm),
        ("strainer_diameter_mm", strainer_diameter_mm),
        ("small_handle_width_mm", small_handle_width_mm),
        ("wide_handle_width_mm", wide_handle_width_mm),
        ("wide_handle_length_mm", wide_handle_length_mm),
        ("wide_handle_straight_length_mm", wide_handle_straight_length_mm),
        ("thick_handle_height_mm", thick_handle_height_mm),
        ("small_handle_height_mm", small_handle_height_mm),
        ("finger_scoop_diameter_mm", finger_scoop_diameter_mm),
        ("tip_loop_length_mm", tip_loop_length_mm),
        ("tip_loop_outer_width_mm", tip_loop_outer_width_mm),
        ("wall_thickness_mm", wall_thickness_mm),
    ):
        if value <= 0:
            raise ValueError(f"{name} must be greater than zero.")

    if fit_clearance_mm < 0:
        raise ValueError("fit_clearance_mm must not be negative.")
    if abs(strainer_rotation_degrees) >= 90.0:
        raise ValueError("strainer_rotation_degrees must remain between -90 and 90 degrees.")
    if strainer_diameter_mm + tip_loop_length_mm >= overall_length_mm:
        raise ValueError(
            "strainer_diameter_mm and tip_loop_length_mm must leave length for the handle."
        )

    handle_side_length_mm = overall_length_mm - strainer_diameter_mm - tip_loop_length_mm
    if wide_handle_length_mm >= handle_side_length_mm:
        raise ValueError("wide_handle_length_mm must leave space for the small handle rails.")
    if wide_handle_straight_length_mm >= wide_handle_length_mm:
        raise ValueError(
            "wide_handle_straight_length_mm must be shorter than wide_handle_length_mm."
        )
    if small_handle_width_mm > wide_handle_width_mm:
        raise ValueError("small_handle_width_mm must not exceed wide_handle_width_mm.")
    if small_handle_height_mm > small_handle_width_mm / 2.0:
        raise ValueError("small_handle_height_mm must leave separation between the two rails.")
    if small_handle_height_mm > thick_handle_height_mm:
        raise ValueError("small_handle_height_mm must not exceed thick_handle_height_mm.")
    if tip_loop_outer_width_mm > strainer_diameter_mm:
        raise ValueError("tip_loop_outer_width_mm must not exceed strainer_diameter_mm.")
