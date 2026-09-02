"""Lipless Gridfinity holder for one spice jar and two cylindrical items."""

from __future__ import annotations

import math
from dataclasses import dataclass

from print_models.models.gridfinity_box import FractionalDividerGridfinityBox

NAME = "gridfinity_spice_combo_holder"
DESCRIPTION = (
    "Lipless 3x4x4U Gridfinity holder with one modular spice-jar socket and two round pockets."
)
PARAMETERS = {
    "unit_width": 3,
    "unit_depth": 4,
    "unit_height": 4,
    "jar_width_mm": 53.0,
    "jar_depth_mm": 53.0,
    "jar_corner_radius_mm": 12.0,
    "large_item_diameter_mm": 91.3,
    "small_item_diameter_mm": 57.7,
    "pocket_depth_mm": 19.0,
    "fit_clearance_mm": 0.75,
    "wall_thickness_mm": 1.0,
}
PRINT_NOTES = (
    "The 53 mm rounded-square spice-jar socket continues the 63 mm center pitch of a "
    "bottom-aligned 3x2 spice holder placed to the left. The 91.3 mm and 57.7 mm item "
    "diameters each receive 0.75 mm radial clearance. All three flat-bottomed pockets are "
    "19 mm deep in a lipless 4U deck. The large round pocket occupies the upper region and "
    "the small round pocket shares the lower row with the spice jar."
)

GRIDFINITY_PITCH_MM = 42.0
GRIDFINITY_HEIGHT_UNIT_MM = 7.0
SPICE_JAR_PITCH_MM = 63.0
STACKING_LIP_ENABLED = False
MINIMUM_CAVITY_FLOOR_MM = 2.0
MINIMUM_DECK_RING_MM = 2.0
BOOLEAN_OVERLAP_MM = 0.1
OUTER_BODY_CORNER_RADIUS_MM = 4.0
TOP_EDGE_CHAMFER_MM = 0.8


@dataclass(frozen=True)
class PocketLayout:
    """Resolved pocket centers in model coordinates."""

    jar_center_mm: tuple[float, float]
    large_center_mm: tuple[float, float]
    small_center_mm: tuple[float, float]


def build(
    unit_width: int = 3,
    unit_depth: int = 4,
    unit_height: int = 4,
    jar_width_mm: float = 53.0,
    jar_depth_mm: float = 53.0,
    jar_corner_radius_mm: float = 12.0,
    large_item_diameter_mm: float = 91.3,
    small_item_diameter_mm: float = 57.7,
    pocket_depth_mm: float = 19.0,
    fit_clearance_mm: float = 0.75,
    wall_thickness_mm: float = 1.0,
):
    """Build the filled lipless holder and subtract its three upright pockets."""
    import cadquery as cq
    from cqgridfinity import GR_BASE_HEIGHT, GR_FLOOR

    _validate_parameters(
        unit_width=unit_width,
        unit_depth=unit_depth,
        unit_height=unit_height,
        jar_width_mm=jar_width_mm,
        jar_depth_mm=jar_depth_mm,
        jar_corner_radius_mm=jar_corner_radius_mm,
        large_item_diameter_mm=large_item_diameter_mm,
        small_item_diameter_mm=small_item_diameter_mm,
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
    jar_pocket_width_mm = jar_width_mm + 2.0 * fit_clearance_mm
    jar_pocket_depth_mm = jar_depth_mm + 2.0 * fit_clearance_mm
    jar_pocket_corner_radius_mm = jar_corner_radius_mm + fit_clearance_mm
    large_pocket_radius_mm = large_item_diameter_mm / 2.0 + fit_clearance_mm
    small_pocket_radius_mm = small_item_diameter_mm / 2.0 + fit_clearance_mm
    layout = _resolve_pocket_layout(
        unit_width=unit_width,
        unit_depth=unit_depth,
        inner_width_mm=inner_width_mm,
        inner_depth_mm=inner_depth_mm,
        jar_pocket_width_mm=jar_pocket_width_mm,
        jar_pocket_depth_mm=jar_pocket_depth_mm,
        large_pocket_radius_mm=large_pocket_radius_mm,
        small_pocket_radius_mm=small_pocket_radius_mm,
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
    jar_socket = _rounded_rectangle_prism(
        width_mm=jar_pocket_width_mm,
        depth_mm=jar_pocket_depth_mm,
        corner_radius_mm=jar_pocket_corner_radius_mm,
        height_mm=cutter_height_mm,
    ).translate((*layout.jar_center_mm, cavity_bottom_z))
    large_socket = (
        cq.Workplane("XY")
        .center(*layout.large_center_mm)
        .circle(large_pocket_radius_mm)
        .extrude(cutter_height_mm)
        .translate((0.0, 0.0, cavity_bottom_z))
    )
    small_socket = (
        cq.Workplane("XY")
        .center(*layout.small_center_mm)
        .circle(small_pocket_radius_mm)
        .extrude(cutter_height_mm)
        .translate((0.0, 0.0, cavity_bottom_z))
    )
    cutter = jar_socket.union(large_socket).union(small_socket).clean()
    return holder.cut(cutter).clean()


def _resolve_pocket_layout(
    *,
    unit_width: int,
    unit_depth: int,
    inner_width_mm: float,
    inner_depth_mm: float,
    jar_pocket_width_mm: float,
    jar_pocket_depth_mm: float,
    large_pocket_radius_mm: float,
    small_pocket_radius_mm: float,
) -> PocketLayout:
    """Place the pockets and reject layouts without a printable deck web."""
    grid_left_mm = -unit_width * GRIDFINITY_PITCH_MM / 2.0
    grid_bottom_mm = -unit_depth * GRIDFINITY_PITCH_MM / 2.0
    jar_center_mm = (
        grid_left_mm + SPICE_JAR_PITCH_MM / 2.0,
        grid_bottom_mm + GRIDFINITY_PITCH_MM,
    )

    jar_right_mm = jar_center_mm[0] + jar_pocket_width_mm / 2.0
    inner_right_mm = inner_width_mm / 2.0
    available_small_web_mm = inner_right_mm - jar_right_mm - 2.0 * small_pocket_radius_mm
    small_side_web_mm = available_small_web_mm / 2.0
    small_center_mm = (
        jar_right_mm + small_side_web_mm + small_pocket_radius_mm,
        jar_center_mm[1],
    )
    large_center_mm = (
        0.0,
        inner_depth_mm / 2.0 - large_pocket_radius_mm - MINIMUM_DECK_RING_MM,
    )
    layout = PocketLayout(
        jar_center_mm=jar_center_mm,
        large_center_mm=large_center_mm,
        small_center_mm=small_center_mm,
    )
    _validate_pocket_layout(
        layout=layout,
        inner_width_mm=inner_width_mm,
        inner_depth_mm=inner_depth_mm,
        jar_pocket_width_mm=jar_pocket_width_mm,
        jar_pocket_depth_mm=jar_pocket_depth_mm,
        large_pocket_radius_mm=large_pocket_radius_mm,
        small_pocket_radius_mm=small_pocket_radius_mm,
    )
    return layout


def _validate_pocket_layout(
    *,
    layout: PocketLayout,
    inner_width_mm: float,
    inner_depth_mm: float,
    jar_pocket_width_mm: float,
    jar_pocket_depth_mm: float,
    large_pocket_radius_mm: float,
    small_pocket_radius_mm: float,
) -> None:
    inner_left_mm = -inner_width_mm / 2.0
    inner_right_mm = inner_width_mm / 2.0
    inner_bottom_mm = -inner_depth_mm / 2.0
    inner_top_mm = inner_depth_mm / 2.0
    jar_left_mm = layout.jar_center_mm[0] - jar_pocket_width_mm / 2.0
    jar_right_mm = layout.jar_center_mm[0] + jar_pocket_width_mm / 2.0
    jar_bottom_mm = layout.jar_center_mm[1] - jar_pocket_depth_mm / 2.0
    jar_top_mm = layout.jar_center_mm[1] + jar_pocket_depth_mm / 2.0

    outer_rings_mm = (
        jar_left_mm - inner_left_mm,
        inner_right_mm - jar_right_mm,
        jar_bottom_mm - inner_bottom_mm,
        inner_top_mm - jar_top_mm,
        layout.large_center_mm[0] - large_pocket_radius_mm - inner_left_mm,
        inner_right_mm - layout.large_center_mm[0] - large_pocket_radius_mm,
        layout.large_center_mm[1] - large_pocket_radius_mm - inner_bottom_mm,
        inner_top_mm - layout.large_center_mm[1] - large_pocket_radius_mm,
        layout.small_center_mm[0] - small_pocket_radius_mm - inner_left_mm,
        inner_right_mm - layout.small_center_mm[0] - small_pocket_radius_mm,
        layout.small_center_mm[1] - small_pocket_radius_mm - inner_bottom_mm,
        inner_top_mm - layout.small_center_mm[1] - small_pocket_radius_mm,
    )
    if min(outer_rings_mm) + 1e-9 < MINIMUM_DECK_RING_MM:
        raise ValueError(
            f"The pockets do not leave the required {MINIMUM_DECK_RING_MM:g} mm outer deck ring."
        )

    jar_to_small_web_mm = layout.small_center_mm[0] - small_pocket_radius_mm - jar_right_mm
    jar_to_large_web_mm = layout.large_center_mm[1] - large_pocket_radius_mm - jar_top_mm
    large_to_small_web_mm = math.dist(layout.large_center_mm, layout.small_center_mm) - (
        large_pocket_radius_mm + small_pocket_radius_mm
    )
    if min(jar_to_small_web_mm, jar_to_large_web_mm, large_to_small_web_mm) + 1e-9 < (
        MINIMUM_DECK_RING_MM
    ):
        raise ValueError(
            "The pockets do not leave the required "
            f"{MINIMUM_DECK_RING_MM:g} mm deck web between openings."
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
        cq.Workplane("XY").rect(width_mm - 2.0 * corner_radius_mm, depth_mm).extrude(height_mm)
    )
    vertical_bar = (
        cq.Workplane("XY").rect(width_mm, depth_mm - 2.0 * corner_radius_mm).extrude(height_mm)
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


def _validate_parameters(
    *,
    unit_width: int,
    unit_depth: int,
    unit_height: int,
    jar_width_mm: float,
    jar_depth_mm: float,
    jar_corner_radius_mm: float,
    large_item_diameter_mm: float,
    small_item_diameter_mm: float,
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

    if (unit_width, unit_depth) != (3, 4):
        raise ValueError("This holder is constrained to a 3x4 Gridfinity footprint.")

    for name, value in (
        ("jar_width_mm", jar_width_mm),
        ("jar_depth_mm", jar_depth_mm),
        ("jar_corner_radius_mm", jar_corner_radius_mm),
        ("large_item_diameter_mm", large_item_diameter_mm),
        ("small_item_diameter_mm", small_item_diameter_mm),
        ("pocket_depth_mm", pocket_depth_mm),
        ("wall_thickness_mm", wall_thickness_mm),
    ):
        if value <= 0:
            raise ValueError(f"{name} must be greater than zero.")

    if fit_clearance_mm < 0:
        raise ValueError("fit_clearance_mm must not be negative.")
    if 2.0 * jar_corner_radius_mm >= min(jar_width_mm, jar_depth_mm):
        raise ValueError("jar_corner_radius_mm must be less than half the shortest jar side.")
