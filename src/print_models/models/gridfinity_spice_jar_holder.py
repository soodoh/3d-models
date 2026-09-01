"""Gridfinity holder for two upright rounded-square spice jars."""

from __future__ import annotations

from print_models.models.gridfinity_box import FractionalDividerGridfinityBox

NAME = "gridfinity_spice_jar_holder"
DESCRIPTION = (
    "Two-socket Gridfinity holder for 53 mm rounded-square spice jars, with modular spacing."
)
PARAMETERS = {
    "unit_width": 3,
    "unit_depth": 2,
    "unit_height": 4,
    "jar_width_mm": 53.0,
    "jar_depth_mm": 53.0,
    "jar_corner_radius_mm": 12.0,
    "pocket_depth_mm": 19.0,
    "fit_clearance_mm": 0.75,
    "wall_thickness_mm": 1.0,
}
PRINT_NOTES = (
    "Defaults fit two upright 53 x 53 mm spice jars with 12 mm plan-view corner radii in "
    "a lipless, 4U-tall holder. A flat chamfered deck replaces the raised Gridfinity bin "
    "walls. The 0.75 mm fit clearance is applied per side, and each flat-bottomed socket is "
    "19 mm deep. Jar centers are 63 mm apart along the 3U footprint axis. Adjacent holders "
    "preserve the same 63 mm center spacing and 10 mm nominal jar-to-jar gap."
)

GRIDFINITY_PITCH_MM = 42.0
GRIDFINITY_HEIGHT_UNIT_MM = 7.0
JAR_COUNT = 2
STACKING_LIP_ENABLED = False
MINIMUM_CAVITY_FLOOR_MM = 2.0
MINIMUM_DECK_RING_MM = 2.0
BOOLEAN_OVERLAP_MM = 0.1
OUTER_BODY_CORNER_RADIUS_MM = 4.0
TOP_EDGE_CHAMFER_MM = 0.8


def build(
    unit_width: int = 3,
    unit_depth: int = 2,
    unit_height: int = 4,
    jar_width_mm: float = 53.0,
    jar_depth_mm: float = 53.0,
    jar_corner_radius_mm: float = 12.0,
    pocket_depth_mm: float = 19.0,
    fit_clearance_mm: float = 0.75,
    wall_thickness_mm: float = 1.0,
):
    """Build a filled 3x2 Gridfinity holder with two rounded-square sockets."""
    import cadquery as cq
    from cqgridfinity import GR_BASE_HEIGHT, GR_FLOOR

    _validate_parameters(
        unit_width=unit_width,
        unit_depth=unit_depth,
        unit_height=unit_height,
        jar_width_mm=jar_width_mm,
        jar_depth_mm=jar_depth_mm,
        jar_corner_radius_mm=jar_corner_radius_mm,
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
        lip_enabled=STACKING_LIP_ENABLED,
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

    inner_width_mm = bounding_box.xlen - 2.0 * wall_thickness_mm
    inner_depth_mm = bounding_box.ylen - 2.0 * wall_thickness_mm
    pocket_width_mm = jar_width_mm + 2.0 * fit_clearance_mm
    pocket_depth_span_mm = jar_depth_mm + 2.0 * fit_clearance_mm
    pocket_corner_radius_mm = jar_corner_radius_mm + fit_clearance_mm
    jar_centers_x_mm = _jar_center_x_positions_mm(
        unit_width=unit_width,
        jar_count=JAR_COUNT,
    )
    _validate_socket_layout(
        jar_centers_x_mm=jar_centers_x_mm,
        pocket_width_mm=pocket_width_mm,
        pocket_depth_span_mm=pocket_depth_span_mm,
        inner_width_mm=inner_width_mm,
        inner_depth_mm=inner_depth_mm,
    )

    base_crop_bottom_z = bounding_box.zmin - BOOLEAN_OVERLAP_MM
    base_crop_height_mm = floor_top_z - base_crop_bottom_z + BOOLEAN_OVERLAP_MM
    base_crop = (
        cq.Workplane("XY")
        .box(
            bounding_box.xlen + 2.0 * BOOLEAN_OVERLAP_MM,
            bounding_box.ylen + 2.0 * BOOLEAN_OVERLAP_MM,
            base_crop_height_mm,
        )
        .translate((0.0, 0.0, base_crop_bottom_z + base_crop_height_mm / 2.0))
    )
    gridfinity_base = box.intersect(base_crop)

    deck_bottom_z = floor_top_z - BOOLEAN_OVERLAP_MM
    deck_height_mm = deck_top_z - deck_bottom_z
    flat_deck = _rounded_rectangle_prism(
        width_mm=bounding_box.xlen,
        depth_mm=bounding_box.ylen,
        corner_radius_mm=OUTER_BODY_CORNER_RADIUS_MM,
        height_mm=deck_height_mm,
    ).translate((0.0, 0.0, deck_bottom_z))
    flat_deck = flat_deck.faces(">Z").edges().chamfer(TOP_EDGE_CHAMFER_MM)
    holder = gridfinity_base.union(flat_deck).clean()

    cutter_height_mm = pocket_depth_mm + BOOLEAN_OVERLAP_MM
    cutter = None
    for center_x_mm in jar_centers_x_mm:
        socket = _rounded_rectangle_prism(
            width_mm=pocket_width_mm,
            depth_mm=pocket_depth_span_mm,
            corner_radius_mm=pocket_corner_radius_mm,
            height_mm=cutter_height_mm,
        ).translate((center_x_mm, 0.0, cavity_bottom_z))
        cutter = socket if cutter is None else cutter.union(socket)

    if cutter is None:
        raise RuntimeError("At least one spice-jar socket is required.")

    return holder.cut(cutter).clean()


def _jar_center_x_positions_mm(*, unit_width: int, jar_count: int) -> tuple[float, ...]:
    """Return centers that repeat at a constant pitch across adjacent holders."""
    if isinstance(unit_width, bool) or not isinstance(unit_width, int) or unit_width < 1:
        raise ValueError("unit_width must be a positive integer.")
    if isinstance(jar_count, bool) or not isinstance(jar_count, int) or jar_count < 1:
        raise ValueError("jar_count must be a positive integer.")

    holder_pitch_mm = unit_width * GRIDFINITY_PITCH_MM
    jar_pitch_mm = holder_pitch_mm / jar_count
    return tuple(
        -holder_pitch_mm / 2.0 + jar_pitch_mm * (index + 0.5) for index in range(jar_count)
    )


def _rounded_rectangle_prism(
    *,
    width_mm: float,
    depth_mm: float,
    corner_radius_mm: float,
    height_mm: float,
):
    """Build a rounded-rectangle prism whose bottom is on the XY plane."""
    import cadquery as cq

    horizontal_bar = (
        cq.Workplane("XY")
        .rect(
            width_mm - 2.0 * corner_radius_mm,
            depth_mm,
        )
        .extrude(height_mm)
    )
    vertical_bar = (
        cq.Workplane("XY")
        .rect(
            width_mm,
            depth_mm - 2.0 * corner_radius_mm,
        )
        .extrude(height_mm)
    )
    result = horizontal_bar.union(vertical_bar)

    corner_x_mm = width_mm / 2.0 - corner_radius_mm
    corner_y_mm = depth_mm / 2.0 - corner_radius_mm
    for x_mm in (-corner_x_mm, corner_x_mm):
        for y_mm in (-corner_y_mm, corner_y_mm):
            corner = (
                cq.Workplane("XY").center(x_mm, y_mm).circle(corner_radius_mm).extrude(height_mm)
            )
            result = result.union(corner)

    return result.clean()


def _validate_socket_layout(
    *,
    jar_centers_x_mm: tuple[float, ...],
    pocket_width_mm: float,
    pocket_depth_span_mm: float,
    inner_width_mm: float,
    inner_depth_mm: float,
) -> None:
    for left_center_mm, right_center_mm in zip(
        jar_centers_x_mm, jar_centers_x_mm[1:], strict=False
    ):
        deck_web_mm = right_center_mm - left_center_mm - pocket_width_mm
        if deck_web_mm < MINIMUM_DECK_RING_MM:
            raise ValueError(
                "The spice-jar sockets do not leave the required "
                f"{MINIMUM_DECK_RING_MM:g} mm deck web between jars."
            )

    outer_ring_mm = min(
        inner_width_mm / 2.0
        - max(abs(center_x_mm) + pocket_width_mm / 2.0 for center_x_mm in jar_centers_x_mm),
        (inner_depth_mm - pocket_depth_span_mm) / 2.0,
    )
    if outer_ring_mm < MINIMUM_DECK_RING_MM:
        raise ValueError(
            "The spice-jar sockets do not leave the required "
            f"{MINIMUM_DECK_RING_MM:g} mm outer deck ring."
        )


def _validate_parameters(
    *,
    unit_width: int,
    unit_depth: int,
    unit_height: int,
    jar_width_mm: float,
    jar_depth_mm: float,
    jar_corner_radius_mm: float,
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

    if (unit_width, unit_depth) != (3, 2):
        raise ValueError("This holder is constrained to a 3x2 Gridfinity footprint.")

    for name, value in (
        ("jar_width_mm", jar_width_mm),
        ("jar_depth_mm", jar_depth_mm),
        ("jar_corner_radius_mm", jar_corner_radius_mm),
        ("pocket_depth_mm", pocket_depth_mm),
        ("wall_thickness_mm", wall_thickness_mm),
    ):
        if value <= 0:
            raise ValueError(f"{name} must be greater than zero.")

    if fit_clearance_mm < 0:
        raise ValueError("fit_clearance_mm must not be negative.")

    minimum_jar_span_mm = min(jar_width_mm, jar_depth_mm)
    if 2.0 * jar_corner_radius_mm >= minimum_jar_span_mm:
        raise ValueError("jar_corner_radius_mm must be less than half the shortest jar side.")
