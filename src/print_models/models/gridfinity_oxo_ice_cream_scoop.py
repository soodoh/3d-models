"""Measured fitted Gridfinity cradle for the OXO Classic Swipe Ice Cream Scoop.

The envelope combines owner-supplied caliper measurements with perspective-corrected
broadside and edge-profile photographs of OXO item 11295100. It is an editable fitted
envelope rather than manufacturer CAD or a 3D scan.
"""

from __future__ import annotations

from collections.abc import Sequence
from math import ceil, sqrt

from print_models.models.gridfinity_box import (
    FractionalDividerGridfinityBox,
    split_filled_gridfinity_cradle,
)

NAME = "gridfinity_oxo_ice_cream_scoop"
DESCRIPTION = (
    "Measured 2x6x6U fitted cradle for the OXO Good Grips Classic Swipe Ice Cream Scoop, "
    "split into two printable 2x3 halves."
)
PARAMETERS = {
    "unit_width": 2,
    "unit_depth": 6,
    "unit_height": 6,
    "split_depth_u": 3.0,
    "overall_length_mm": 224.4,
    "guard_face_from_handle_tip_mm": 120.6,
    "bowl_near_edge_from_handle_tip_mm": 163.6,
    "handle_width_mm": 33.5,
    "handle_depth_mm": 25.7,
    "guard_width_mm": 54.4,
    "guard_depth_mm": 35.0,
    "guard_upper_reach_mm": 40.4,
    "bowl_diameter_mm": 58.2,
    "bowl_depth_mm": 36.0,
    "mechanism_span_mm": 85.8,
    "mechanism_depth_mm": 22.5,
    "roll_angle_degrees": 47.0,
    "fit_clearance_mm": 1.0,
    "cavity_depth_mm": 33.0,
    "wall_thickness_mm": 1.0,
}
PRINT_NOTES = (
    "The fitted envelope uses owner measurements from a physical OXO 11295100: 224.4 mm "
    "overall length, 120.6 mm handle-tip-to-guard face, 163.6 mm handle-tip-to-near-bowl "
    "edge, 33.5 x 25.7 mm grip, 54.4 x 35 mm guard, 58.2 mm bowl diameter, 36 mm bowl "
    "depth, 85.8 mm broadside mechanism span, and 22.5 mm mechanism thickness. Calibrated "
    "trace photos define the asymmetric guard and curved metal release lever. The scoop is "
    "rolled 47 degrees with the metal lever uppermost, giving an approximately 70.4 mm installed "
    "height. Default clearance is 1 mm around every modeled surface. Export both front and back "
    "STL parts, print bases down, and place them together on adjacent 2x3 cell regions."
)

GRIDFINITY_HEIGHT_UNIT_MM = 7.0
MINIMUM_CAVITY_FLOOR_MM = 2.0
MINIMUM_DECK_RING_MM = 2.0
BOOLEAN_OVERLAP_MM = 0.2
HANDLE_BOTTOM_OFFSET_MM = 4.0
GUARD_AXIAL_LENGTH_MM = 11.0
SHAFT_WIDTH_MM = 20.0
SHAFT_DEPTH_MM = 20.0
PIN_RADIUS_MM = 3.0
PIN_CENTER_Z_MM = 3.0
LEVER_DEPTH_MM = 4.0


def _loft_elliptical_sections(
    sections: Sequence[tuple[float, float, float]],
    *,
    center_x: float = 0.0,
    center_z: float = 0.0,
):
    """Loft X/Z ellipses through increasing global-Y stations."""
    import cadquery as cq

    if len(sections) < 2:
        raise ValueError("An elliptical loft requires at least two sections.")
    if any(
        right_y <= left_y
        for (left_y, _, _), (right_y, _, _) in zip(sections[:-1], sections[1:], strict=True)
    ):
        raise ValueError("Elliptical loft stations must increase along Y.")
    if any(radius_x <= 0.0 or radius_z <= 0.0 for _, radius_x, radius_z in sections):
        raise ValueError("Elliptical loft radii must be positive.")

    start_y, start_radius_x, start_radius_z = sections[0]
    plane = cq.Plane(
        origin=(center_x, start_y, center_z),
        xDir=(1.0, 0.0, 0.0),
        normal=(0.0, 1.0, 0.0),
    )
    loft = cq.Workplane(plane).ellipse(start_radius_x, start_radius_z)
    previous_y = start_y
    for station_y, radius_x, radius_z in sections[1:]:
        loft = loft.workplane(offset=station_y - previous_y).ellipse(radius_x, radius_z)
        previous_y = station_y
    return loft.loft(combine=True, ruled=True)


def _extrude_profile(
    points: Sequence[tuple[float, float]],
    *,
    bottom_z: float,
    depth_mm: float,
    clearance_mm: float,
):
    """Extrude a measured broadside X/Y profile with an optional planar offset."""
    import cadquery as cq

    if len(points) < 3 or depth_mm <= 0.0:
        raise ValueError("A profile extrusion requires three points and positive depth.")
    profile = cq.Workplane("XY").polyline(points).close()
    if clearance_mm > 0.0:
        profile = profile.offset2D(clearance_mm)
    return profile.extrude(depth_mm + 2.0 * clearance_mm).translate(
        (0.0, 0.0, bottom_z - clearance_mm)
    )


def _build_bowl_dome(
    *,
    center_y: float,
    diameter_mm: float,
    depth_mm: float,
    clearance_mm: float,
):
    """Build the measured hemispherical cup envelope from its rim plane to its crown."""
    import cadquery as cq

    radius_mm = diameter_mm / 2.0 + clearance_mm
    cleared_depth_mm = depth_mm + 2.0 * clearance_mm
    rim_z = -clearance_mm
    plane = cq.Plane(
        origin=(0.0, center_y, rim_z),
        xDir=(1.0, 0.0, 0.0),
        normal=(0.0, 0.0, 1.0),
    )
    dome = cq.Workplane(plane).circle(radius_mm)
    previous_z = rim_z
    for section_index in range(1, 9):
        fraction = section_index / 8.0
        station_z = rim_z + cleared_depth_mm * fraction
        profile_scale = sqrt(max(0.0, 1.0 - fraction * fraction))
        section_radius = max(0.8 + clearance_mm, radius_mm * profile_scale)
        dome = dome.workplane(offset=station_z - previous_z).circle(section_radius)
        previous_z = station_z
    return dome.loft(combine=True, ruled=True)


def _build_scoop_envelope(
    *,
    overall_length_mm: float,
    guard_face_from_handle_tip_mm: float,
    bowl_near_edge_from_handle_tip_mm: float,
    handle_width_mm: float,
    handle_depth_mm: float,
    guard_width_mm: float,
    guard_depth_mm: float,
    guard_upper_reach_mm: float,
    bowl_diameter_mm: float,
    bowl_depth_mm: float,
    mechanism_span_mm: float,
    mechanism_depth_mm: float,
    clearance_mm: float,
):
    """Build the measured, unrolled clearance envelope around the longitudinal Y axis."""
    dimensions = (
        overall_length_mm,
        guard_face_from_handle_tip_mm,
        bowl_near_edge_from_handle_tip_mm,
        handle_width_mm,
        handle_depth_mm,
        guard_width_mm,
        guard_depth_mm,
        bowl_diameter_mm,
        bowl_depth_mm,
        mechanism_span_mm,
        mechanism_depth_mm,
    )
    if any(dimension <= 0.0 for dimension in dimensions):
        raise ValueError("Scoop dimensions must be positive.")
    if clearance_mm < 0.0:
        raise ValueError("fit_clearance_mm cannot be negative.")
    if not guard_face_from_handle_tip_mm < bowl_near_edge_from_handle_tip_mm:
        raise ValueError("The guard face must precede the bowl rim.")
    bowl_far_edge_mm = bowl_near_edge_from_handle_tip_mm + bowl_diameter_mm
    if bowl_far_edge_mm > overall_length_mm:
        raise ValueError("The measured bowl extends beyond the overall scoop length.")
    if guard_upper_reach_mm <= guard_width_mm / 2.0:
        raise ValueError("guard_upper_reach_mm must include the measured asymmetric offset.")
    if mechanism_span_mm <= guard_upper_reach_mm:
        raise ValueError("mechanism_span_mm must reach across the shaft centerline.")

    origin_y = -overall_length_mm / 2.0
    guard_face_y = origin_y + guard_face_from_handle_tip_mm
    guard_start_y = guard_face_y - GUARD_AXIAL_LENGTH_MM
    bowl_near_y = origin_y + bowl_near_edge_from_handle_tip_mm
    bowl_center_y = bowl_near_y + bowl_diameter_mm / 2.0
    bowl_far_y = bowl_near_y + bowl_diameter_mm
    pin_end_y = origin_y + overall_length_mm + clearance_mm

    handle_radius_x = handle_width_mm / 2.0 + clearance_mm
    handle_radius_z = handle_depth_mm / 2.0 + clearance_mm
    handle_center_z = HANDLE_BOTTOM_OFFSET_MM + handle_depth_mm / 2.0
    handle_end_y = guard_start_y + 5.0
    handle = _loft_elliptical_sections(
        (
            (origin_y - clearance_mm, 0.8 + clearance_mm, 0.8 + clearance_mm),
            (origin_y + 4.0, 11.0 + clearance_mm, 9.0 + clearance_mm),
            (origin_y + 10.0, handle_radius_x, handle_radius_z),
            (origin_y + 95.0, handle_radius_x, handle_radius_z),
            (handle_end_y, 15.5 + clearance_mm, 12.0 + clearance_mm),
        ),
        center_z=handle_center_z,
    )

    guard_lower_reach_mm = guard_upper_reach_mm - guard_width_mm
    guard_center_x = (guard_upper_reach_mm + guard_lower_reach_mm) / 2.0
    guard = _loft_elliptical_sections(
        (
            (
                guard_start_y - clearance_mm,
                guard_width_mm / 2.0 + clearance_mm,
                guard_depth_mm / 2.0 + clearance_mm,
            ),
            (
                guard_face_y + clearance_mm,
                guard_width_mm / 2.0 + clearance_mm,
                guard_depth_mm / 2.0 + clearance_mm,
            ),
        ),
        center_x=guard_center_x,
        center_z=guard_depth_mm / 2.0,
    )

    shaft_center_z = mechanism_depth_mm / 2.0
    shaft = _loft_elliptical_sections(
        (
            (
                guard_start_y + 5.0,
                SHAFT_WIDTH_MM / 2.0 + clearance_mm,
                SHAFT_DEPTH_MM / 2.0 + clearance_mm,
            ),
            (
                bowl_near_y + 5.0,
                SHAFT_WIDTH_MM / 2.0 + clearance_mm,
                SHAFT_DEPTH_MM / 2.0 + clearance_mm,
            ),
        ),
        center_z=shaft_center_z,
    )

    gap_mm = bowl_near_edge_from_handle_tip_mm - guard_face_from_handle_tip_mm
    main_plate_points = (
        (10.0, guard_face_y - 1.0),
        (12.0, guard_face_y + gap_mm * 0.60),
        (5.0, bowl_near_y - 2.0),
        (-20.0, bowl_near_y - 1.0),
        (-30.0, guard_face_y + gap_mm * 0.68),
        (-27.0, guard_face_y + gap_mm * 0.32),
        (-18.0, guard_face_y),
    )
    main_plate = _extrude_profile(
        main_plate_points,
        bottom_z=0.0,
        depth_mm=mechanism_depth_mm,
        clearance_mm=clearance_mm,
    )

    lever_lower_reach_mm = guard_upper_reach_mm - mechanism_span_mm
    lever_points = (
        (-20.0, bowl_near_y - 3.0),
        (-28.0, bowl_near_y - 8.0),
        (-36.0, guard_face_y + gap_mm * 0.38),
        (lever_lower_reach_mm, guard_face_y + 5.0),
        (lever_lower_reach_mm, guard_face_y + 1.0),
        (lever_lower_reach_mm + 5.0, guard_face_y + 3.0),
        (-32.0, guard_face_y + gap_mm * 0.28),
        (-23.0, bowl_near_y - 7.0),
        (-16.0, bowl_near_y - 4.0),
    )
    lever = _extrude_profile(
        lever_points,
        bottom_z=1.0,
        depth_mm=LEVER_DEPTH_MM,
        clearance_mm=clearance_mm,
    )

    bowl = _build_bowl_dome(
        center_y=bowl_center_y,
        diameter_mm=bowl_diameter_mm,
        depth_mm=bowl_depth_mm,
        clearance_mm=clearance_mm,
    )

    import cadquery as cq

    pin_plane = cq.Plane(
        origin=(0.0, bowl_far_y - 3.0, PIN_CENTER_Z_MM),
        xDir=(1.0, 0.0, 0.0),
        normal=(0.0, 1.0, 0.0),
    )
    pin = (
        cq.Workplane(pin_plane)
        .circle(PIN_RADIUS_MM + clearance_mm)
        .extrude(pin_end_y - (bowl_far_y - 3.0))
    )

    return (
        handle.union(guard)
        .union(shaft)
        .union(main_plate)
        .union(lever)
        .union(bowl)
        .union(pin)
        .clean()
    )


def _orient_scoop_envelope(*, scoop, roll_angle_degrees: float, cavity_bottom_z: float):
    """Roll the measured metal lever upward and laterally center the installed envelope."""
    if not 0.0 < roll_angle_degrees < 90.0:
        raise ValueError("roll_angle_degrees must be between 0 and 90 degrees.")

    rolled = scoop.rotate((0.0, 0.0, 0.0), (0.0, 1.0, 0.0), roll_angle_degrees)
    bounds = rolled.val().BoundingBox()
    center_x = (bounds.xmin + bounds.xmax) / 2.0
    return rolled.translate((-center_x, 0.0, cavity_bottom_z - bounds.zmin))


def _build_vertical_release_cutter(*, fitted_cutter, deck_top_z: float, step_mm: float = 2.0):
    """Sweep the fitted envelope upward so every pocket feature can lift out vertically."""
    if step_mm <= 0.0:
        raise ValueError("The vertical release step must be positive.")

    bounds = fitted_cutter.val().BoundingBox()
    shift_count = ceil((deck_top_z + BOOLEAN_OVERLAP_MM - bounds.zmin) / step_mm)
    release_cutter = fitted_cutter
    for shift_index in range(1, shift_count + 1):
        release_cutter = release_cutter.union(
            fitted_cutter.translate((0.0, 0.0, shift_index * step_mm)),
            clean=False,
        )
    return release_cutter.clean()


def _build_filled_holder(
    *,
    unit_width: int,
    unit_depth: int,
    unit_height: int,
    wall_thickness_mm: float,
    cutter,
):
    """Fill an empty Gridfinity shell through its nominal top and cut the fitted pocket."""
    import cadquery as cq
    from cqgridfinity import GR_BASE_HEIGHT, GR_FLOOR

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
    bounds = box.val().BoundingBox()
    floor_top_z = GR_BASE_HEIGHT + GR_FLOOR
    deck_top_z = unit_height * GRIDFINITY_HEIGHT_UNIT_MM
    inner_x_min = bounds.xmin + wall_thickness_mm
    inner_x_max = bounds.xmax - wall_thickness_mm
    inner_y_min = bounds.ymin + wall_thickness_mm
    inner_y_max = bounds.ymax - wall_thickness_mm
    cutter_bounds = cutter.val().BoundingBox()

    if cutter_bounds.zmin < floor_top_z + MINIMUM_CAVITY_FLOOR_MM - 1e-6:
        raise ValueError("The scoop cavity does not leave the required 2 mm floor.")
    if (
        cutter_bounds.xmin < inner_x_min + MINIMUM_DECK_RING_MM
        or cutter_bounds.xmax > inner_x_max - MINIMUM_DECK_RING_MM
        or cutter_bounds.ymin < inner_y_min + MINIMUM_DECK_RING_MM
        or cutter_bounds.ymax > inner_y_max - MINIMUM_DECK_RING_MM
    ):
        raise ValueError("The scoop cavity does not leave the required surrounding deck ring.")

    fill = (
        cq.Workplane("XY")
        .box(
            inner_x_max - inner_x_min,
            inner_y_max - inner_y_min,
            deck_top_z - floor_top_z + BOOLEAN_OVERLAP_MM,
            centered=(True, True, False),
        )
        .translate((0.0, 0.0, floor_top_z - BOOLEAN_OVERLAP_MM))
    )
    return box.union(fill).cut(cutter).clean()


def build(
    unit_width: int = 2,
    unit_depth: int = 6,
    unit_height: int = 6,
    split_depth_u: float = 3.0,
    overall_length_mm: float = 224.4,
    guard_face_from_handle_tip_mm: float = 120.6,
    bowl_near_edge_from_handle_tip_mm: float = 163.6,
    handle_width_mm: float = 33.5,
    handle_depth_mm: float = 25.7,
    guard_width_mm: float = 54.4,
    guard_depth_mm: float = 35.0,
    guard_upper_reach_mm: float = 40.4,
    bowl_diameter_mm: float = 58.2,
    bowl_depth_mm: float = 36.0,
    mechanism_span_mm: float = 85.8,
    mechanism_depth_mm: float = 22.5,
    roll_angle_degrees: float = 47.0,
    fit_clearance_mm: float = 1.0,
    cavity_depth_mm: float = 33.0,
    wall_thickness_mm: float = 1.0,
):
    """Build front and back 2x3 halves of the measured 2x6x6U scoop cradle."""
    from cqgridfinity import GR_BASE_HEIGHT, GR_FLOOR

    if unit_width != 2 or unit_depth != 6 or unit_height != 6:
        raise ValueError("This fitted holder is constrained to a 2x6x6U Gridfinity envelope.")
    if split_depth_u <= 0.0 or split_depth_u >= unit_depth:
        raise ValueError("split_depth_u must lie inside the module depth.")
    if cavity_depth_mm <= 0.0:
        raise ValueError("cavity_depth_mm must be positive.")
    if wall_thickness_mm <= 0.0:
        raise ValueError("wall_thickness_mm must be positive.")

    deck_top_z = unit_height * GRIDFINITY_HEIGHT_UNIT_MM
    floor_top_z = GR_BASE_HEIGHT + GR_FLOOR
    cavity_bottom_z = deck_top_z - cavity_depth_mm
    if cavity_bottom_z < floor_top_z + MINIMUM_CAVITY_FLOOR_MM:
        raise ValueError("cavity_depth_mm must preserve at least 2 mm over the Gridfinity floor.")

    scoop = _build_scoop_envelope(
        overall_length_mm=overall_length_mm,
        guard_face_from_handle_tip_mm=guard_face_from_handle_tip_mm,
        bowl_near_edge_from_handle_tip_mm=bowl_near_edge_from_handle_tip_mm,
        handle_width_mm=handle_width_mm,
        handle_depth_mm=handle_depth_mm,
        guard_width_mm=guard_width_mm,
        guard_depth_mm=guard_depth_mm,
        guard_upper_reach_mm=guard_upper_reach_mm,
        bowl_diameter_mm=bowl_diameter_mm,
        bowl_depth_mm=bowl_depth_mm,
        mechanism_span_mm=mechanism_span_mm,
        mechanism_depth_mm=mechanism_depth_mm,
        clearance_mm=fit_clearance_mm,
    )
    fitted_cutter = _orient_scoop_envelope(
        scoop=scoop,
        roll_angle_degrees=roll_angle_degrees,
        cavity_bottom_z=cavity_bottom_z,
    )
    release_cutter = _build_vertical_release_cutter(
        fitted_cutter=fitted_cutter,
        deck_top_z=deck_top_z,
    )
    holder = _build_filled_holder(
        unit_width=unit_width,
        unit_depth=unit_depth,
        unit_height=unit_height,
        wall_thickness_mm=wall_thickness_mm,
        cutter=release_cutter,
    )
    split_parts = split_filled_gridfinity_cradle(
        holder,
        unit_width=unit_width,
        unit_depth=unit_depth,
        unit_height=unit_height,
        split_width_positions_u=(),
        split_depth_positions_u=(split_depth_u,),
        wall_thickness_mm=wall_thickness_mm,
    )
    return {
        "scoop_holder_front": split_parts["depth_1_of_2"],
        "scoop_holder_back": split_parts["depth_2_of_2"],
    }
