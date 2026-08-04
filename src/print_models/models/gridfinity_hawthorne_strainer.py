"""Shallow spring-side-down Gridfinity cradle for a Hawthorne cocktail strainer."""

from __future__ import annotations

from print_models.models.gridfinity_box import FractionalDividerGridfinityBox

NAME = "gridfinity_hawthorne_strainer"
DESCRIPTION = (
    "Spring-side-down 3x4 Gridfinity cradle with a photo-traced Hawthorne-strainer "
    "silhouette, deep spring well, and shallow handle track."
)
PARAMETERS = {
    "unit_width": 3,
    "unit_depth": 4,
    "unit_height": 4,
    "pocket_depth_mm": 18.0,
    "spring_height_mm": 18.0,
    "overall_length_mm": 137.0,
    "widest_width_mm": 99.0,
    "handle_straight_width_mm": 30.0,
    "handle_pocket_depth_mm": 3.0,
    "fit_clearance_mm": 1.0,
    "wall_thickness_mm": 1.0,
}
PRINT_NOTES = (
    "The strainer is stored horizontally with the spring facing down. The broad head follows "
    "the supplied overhead photo: a 99 mm shoulder span, rounded spring crown, and smooth flare "
    "into the measured 30 mm straight handle. The 18 mm-deep head well fits the measured spring "
    "height, while the handle remains supported in a shallow 3 mm track. The photo-estimated "
    "curve landmarks scale with the measured 137 mm overall length. Defaults use a 3x4, 4U "
    "Gridfinity box with 1 mm fit clearance."
)

GRIDFINITY_HEIGHT_UNIT_MM = 7.0
MINIMUM_CAVITY_FLOOR_MM = 2.0
MINIMUM_DECK_RING_MM = 2.0
BOOLEAN_OVERLAP_MM = 0.1
REFERENCE_PROFILE_LENGTH_MM = 137.0
HANDLE_TIP_END_FROM_BOTTOM_MM = 15.0
HANDLE_STRAIGHT_END_FROM_BOTTOM_MM = 39.0
WIDEST_SECTION_START_FROM_BOTTOM_MM = 99.0
WIDEST_SECTION_END_FROM_BOTTOM_MM = 108.0
SPRING_CROWN_START_FROM_BOTTOM_MM = 114.0


def build(
    unit_width: int = 3,
    unit_depth: int = 4,
    unit_height: int = 4,
    pocket_depth_mm: float = 18.0,
    spring_height_mm: float = 18.0,
    overall_length_mm: float = 137.0,
    widest_width_mm: float = 99.0,
    handle_straight_width_mm: float = 30.0,
    handle_pocket_depth_mm: float = 3.0,
    fit_clearance_mm: float = 1.0,
    wall_thickness_mm: float = 1.0,
):
    """Build a filled Gridfinity cradle with a traced spring well and handle track."""
    from cqgridfinity import GR_BASE_HEIGHT, GR_FLOOR

    _validate_parameters(
        unit_width=unit_width,
        unit_depth=unit_depth,
        unit_height=unit_height,
        pocket_depth_mm=pocket_depth_mm,
        spring_height_mm=spring_height_mm,
        overall_length_mm=overall_length_mm,
        widest_width_mm=widest_width_mm,
        handle_straight_width_mm=handle_straight_width_mm,
        handle_pocket_depth_mm=handle_pocket_depth_mm,
        fit_clearance_mm=fit_clearance_mm,
        wall_thickness_mm=wall_thickness_mm,
    )

    floor_top_z = GR_BASE_HEIGHT + GR_FLOOR
    deck_top_z = unit_height * GRIDFINITY_HEIGHT_UNIT_MM
    head_pocket_bottom_z = deck_top_z - pocket_depth_mm
    if head_pocket_bottom_z - floor_top_z < MINIMUM_CAVITY_FLOOR_MM:
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

    cleared_width = widest_width_mm + 2.0 * fit_clearance_mm
    cleared_length = overall_length_mm + 2.0 * fit_clearance_mm
    if cleared_width + 2.0 * MINIMUM_DECK_RING_MM > inner_x_max - inner_x_min:
        raise ValueError(
            "The strainer pocket does not leave a safe deck ring in the selected width."
        )
    if cleared_length + 2.0 * MINIMUM_DECK_RING_MM > inner_y_max - inner_y_min:
        raise ValueError(
            "The strainer cutout does not leave a safe deck ring in the selected depth."
        )

    cutter = _build_spring_side_down_cutter(
        deck_top_z=deck_top_z,
        head_pocket_bottom_z=head_pocket_bottom_z,
        overall_length_mm=overall_length_mm,
        widest_width_mm=widest_width_mm,
        handle_straight_width_mm=handle_straight_width_mm,
        handle_pocket_depth_mm=handle_pocket_depth_mm,
        fit_clearance_mm=fit_clearance_mm,
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


def _build_spring_side_down_cutter(
    *,
    deck_top_z: float,
    head_pocket_bottom_z: float,
    overall_length_mm: float,
    widest_width_mm: float,
    handle_straight_width_mm: float,
    handle_pocket_depth_mm: float,
    fit_clearance_mm: float,
):
    """Build a deep traced head well beneath the full shallow insertion silhouette."""
    cutter_top_z = deck_top_z + BOOLEAN_OVERLAP_MM
    silhouette = _build_profile_cutter(
        overall_length_mm=overall_length_mm,
        widest_width_mm=widest_width_mm,
        handle_straight_width_mm=handle_straight_width_mm,
        bottom_z=deck_top_z - handle_pocket_depth_mm,
        top_z=cutter_top_z,
        fit_clearance_mm=fit_clearance_mm,
        include_handle=True,
    )
    head = _build_profile_cutter(
        overall_length_mm=overall_length_mm,
        widest_width_mm=widest_width_mm,
        handle_straight_width_mm=handle_straight_width_mm,
        bottom_z=head_pocket_bottom_z,
        top_z=cutter_top_z,
        fit_clearance_mm=fit_clearance_mm,
        include_handle=False,
    )
    return silhouette.union(head).clean()


def _build_profile_cutter(
    *,
    overall_length_mm: float,
    widest_width_mm: float,
    handle_straight_width_mm: float,
    bottom_z: float,
    top_z: float,
    fit_clearance_mm: float,
    include_handle: bool,
):
    """Extrude the symmetric photo-estimated outer silhouette or only its broad head."""
    import cadquery as cq

    profile_scale = overall_length_mm / REFERENCE_PROFILE_LENGTH_MM
    object_start_y = -overall_length_mm / 2.0
    object_end_y = overall_length_mm / 2.0
    cleared_start_y = object_start_y - fit_clearance_mm
    cleared_end_y = object_end_y + fit_clearance_mm
    tip_end_y = object_start_y + HANDLE_TIP_END_FROM_BOTTOM_MM * profile_scale
    straight_end_y = object_start_y + HANDLE_STRAIGHT_END_FROM_BOTTOM_MM * profile_scale
    widest_start_y = object_start_y + WIDEST_SECTION_START_FROM_BOTTOM_MM * profile_scale
    widest_end_y = object_start_y + WIDEST_SECTION_END_FROM_BOTTOM_MM * profile_scale
    crown_start_y = object_start_y + SPRING_CROWN_START_FROM_BOTTOM_MM * profile_scale

    handle_half_width = handle_straight_width_mm / 2.0 + fit_clearance_mm
    widest_half_width = widest_width_mm / 2.0 + fit_clearance_mm
    shoulder_half_width = widest_width_mm * (47.0 / 99.0) + fit_clearance_mm
    crown_control_half_width = widest_width_mm * (42.0 / 99.0) + fit_clearance_mm
    crown_top_control_half_width = widest_width_mm * (28.0 / 99.0) + fit_clearance_mm

    vector = cq.Vector
    upper_segments = [
        [
            vector(handle_half_width, straight_end_y, bottom_z),
            vector(handle_half_width, object_start_y + 53.5 * profile_scale, bottom_z),
            vector(widest_half_width, object_start_y + 80.5 * profile_scale, bottom_z),
            vector(widest_half_width, widest_start_y, bottom_z),
        ],
        [
            vector(widest_half_width, widest_start_y, bottom_z),
            vector(widest_half_width, widest_end_y, bottom_z),
        ],
        [
            vector(widest_half_width, widest_end_y, bottom_z),
            vector(widest_half_width, object_start_y + 111.5 * profile_scale, bottom_z),
            vector(
                shoulder_half_width,
                object_start_y + 113.5 * profile_scale,
                bottom_z,
            ),
            vector(shoulder_half_width, crown_start_y, bottom_z),
        ],
        [
            vector(shoulder_half_width, crown_start_y, bottom_z),
            vector(crown_control_half_width, object_start_y + 115.5 * profile_scale, bottom_z),
            vector(crown_top_control_half_width, cleared_end_y, bottom_z),
            vector(0.0, cleared_end_y, bottom_z),
        ],
    ]
    if include_handle:
        right_segments = [
            [
                vector(0.0, cleared_start_y, bottom_z),
                vector(handle_half_width * 0.53, cleared_start_y, bottom_z),
                vector(handle_half_width, object_start_y + 6.5 * profile_scale, bottom_z),
                vector(handle_half_width, tip_end_y, bottom_z),
            ],
            [
                vector(handle_half_width, tip_end_y, bottom_z),
                vector(handle_half_width, straight_end_y, bottom_z),
            ],
            *upper_segments,
        ]
    else:
        right_segments = [
            [
                vector(0.0, straight_end_y, bottom_z),
                vector(handle_half_width, straight_end_y, bottom_z),
            ],
            *upper_segments,
        ]

    def mirrored(point):
        return vector(-point.x, point.y, point.z)

    edges = []
    for segment in right_segments:
        edges.append(_profile_edge(segment))
    for segment in reversed(right_segments):
        edges.append(_profile_edge([mirrored(point) for point in reversed(segment)]))

    wire = cq.Wire.assembleEdges(edges)
    solid = cq.Solid.extrudeLinear(wire, [], vector(0.0, 0.0, top_z - bottom_z))
    return cq.Workplane(obj=solid)


def _profile_edge(points):
    """Build one straight or cubic-Bezier edge from ordered profile control points."""
    import cadquery as cq

    if len(points) == 2:
        return cq.Edge.makeLine(points[0], points[1])
    return cq.Edge.makeBezier(points)


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
    spring_height_mm: float,
    overall_length_mm: float,
    widest_width_mm: float,
    handle_straight_width_mm: float,
    handle_pocket_depth_mm: float,
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
        ("spring_height_mm", spring_height_mm),
        ("overall_length_mm", overall_length_mm),
        ("widest_width_mm", widest_width_mm),
        ("handle_straight_width_mm", handle_straight_width_mm),
        ("handle_pocket_depth_mm", handle_pocket_depth_mm),
        ("wall_thickness_mm", wall_thickness_mm),
    ):
        if value <= 0:
            raise ValueError(f"{name} must be greater than zero.")

    if fit_clearance_mm < 0:
        raise ValueError("fit_clearance_mm must not be negative.")
    if pocket_depth_mm < spring_height_mm:
        raise ValueError("pocket_depth_mm must be at least spring_height_mm.")
    if handle_pocket_depth_mm > pocket_depth_mm:
        raise ValueError("handle_pocket_depth_mm must not exceed pocket_depth_mm.")
    if widest_width_mm >= overall_length_mm:
        raise ValueError("overall_length_mm must exceed widest_width_mm.")
    if handle_straight_width_mm >= widest_width_mm:
        raise ValueError("handle_straight_width_mm must be narrower than widest_width_mm.")
