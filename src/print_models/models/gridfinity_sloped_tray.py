"""Parametric Gridfinity tray with a solid-backed slope and front cradle wall."""

from __future__ import annotations

import math

from print_models.models.gridfinity_box import FractionalDividerGridfinityBox

NAME = "gridfinity_sloped_tray"
DESCRIPTION = (
    "Parametrically wide, 3U-deep Gridfinity tray with a solid-backed sloped surface and a "
    "bottom cradle wall."
)
PARAMETERS = {
    "unit_width": 5,
    "unit_depth": 3,
    "unit_height": 0,
    "surface_depth_mm": 114.0,
    "angle_degrees": 15.0,
    "item_length_mm": 112.0,
    "item_width_mm": 51.0,
    "item_height_mm": 51.0,
    "fit_clearance_mm": 1.0,
    "support_front_z_mm": 8.0,
    "max_drawer_height_mm": 91.0,
    "wall_thickness_mm": 1.0,
}
PRINT_NOTES = (
    "Defaults create a 5x3 Gridfinity module for one row of nominal 51x51x112 mm square "
    "spice jars. The tray rises 15 degrees; its slope is solid down to the base, with no "
    "underside ribs or overhangs. The closed side and back walls terminate exactly on the "
    "slope plane at the Gridfinity perimeter. At the low end, one full-width retaining body "
    "combines a perpendicular jar-contact face with a flat top at the standard 4U exterior "
    "height of 31.8 mm. The conservative item envelope reaches about 88.7 mm from the holder "
    "underside. Print in the modeled orientation without supports."
)

BASE_CONNECT_Z_MM = 4.0
GRIDFINITY_BASE_TOP_Z_MM = 5.0
PANEL_THICKNESS_MM = 2.4
FRONT_WALL_TOP_Z_MM = 31.8
OUTER_CORNER_RADIUS_MM = 4.0
PERIMETER_WALL_THICKNESS_MM = 1.6
BOOLEAN_OVERLAP_MM = 0.3


def _sloped_item_envelopes_mm(
    *,
    item_length_mm: float,
    item_height_mm: float,
    angle_degrees: float,
    fit_clearance_mm: float,
) -> tuple[float, float]:
    """Return vertical and front-to-back bounds for an item lying on the tray."""
    angle_radians = math.radians(angle_degrees)
    clear_length = item_length_mm + 2.0 * fit_clearance_mm
    clear_height = item_height_mm + 2.0 * fit_clearance_mm
    vertical = clear_length * math.sin(angle_radians) + clear_height * math.cos(angle_radians)
    front_to_back = clear_length * math.cos(angle_radians) + clear_height * math.sin(angle_radians)
    return vertical, front_to_back


def _clearance_y_bounds_mm(
    *,
    surface_depth_mm: float,
    item_length_mm: float,
    item_height_mm: float,
    fit_clearance_mm: float,
    angle_degrees: float,
    tray_offset_y_mm: float = 0.0,
) -> tuple[float, float]:
    """Return the front and rear clearance coordinates for an item resting on the tray."""
    angle_radians = math.radians(angle_degrees)
    clear_height_mm = item_height_mm + 2.0 * fit_clearance_mm
    item_front_y_mm = -surface_depth_mm / 2.0 + BOOLEAN_OVERLAP_MM - fit_clearance_mm
    item_rear_y_mm = (
        -surface_depth_mm / 2.0 + BOOLEAN_OVERLAP_MM + item_length_mm + fit_clearance_mm
    )
    front_y_mm = (
        item_front_y_mm * math.cos(angle_radians)
        - clear_height_mm * math.sin(angle_radians)
        + tray_offset_y_mm
    )
    rear_y_mm = item_rear_y_mm * math.cos(angle_radians) + tray_offset_y_mm
    return front_y_mm, rear_y_mm


def _build_solid_slope_support(
    *,
    width_mm: float,
    front_y_mm: float,
    rear_y_mm: float,
    tray_offset_y_mm: float,
    translation_z_mm: float,
    angle_degrees: float,
):
    """Build a full-width solid wedge from the base to the sloped panel underside."""
    import cadquery as cq

    angle_radians = math.radians(angle_degrees)
    panel_vertical_thickness = PANEL_THICKNESS_MM / math.cos(angle_radians)

    def underside_z(y_mm: float) -> float:
        return (
            (y_mm - tray_offset_y_mm) * math.tan(angle_radians)
            + translation_z_mm
            - panel_vertical_thickness
        )

    front_top_z = underside_z(front_y_mm) + BOOLEAN_OVERLAP_MM
    rear_top_z = underside_z(rear_y_mm) + BOOLEAN_OVERLAP_MM
    if front_top_z <= BASE_CONNECT_Z_MM or rear_top_z <= BASE_CONNECT_Z_MM:
        raise ValueError("The sloped panel is too low to connect its solid support to the base.")

    return (
        cq.Workplane("YZ")
        .polyline(
            (
                (front_y_mm, BASE_CONNECT_Z_MM),
                (rear_y_mm, BASE_CONNECT_Z_MM),
                (rear_y_mm, rear_top_z),
                (front_y_mm, front_top_z),
            )
        )
        .close()
        .extrude(width_mm / 2.0, both=True)
    )


def _build_side_wall(
    *,
    x_mm: float,
    front_y_mm: float,
    rear_y_mm: float,
    tray_offset_y_mm: float,
    translation_z_mm: float,
    angle_degrees: float,
):
    """Build one closed side wall whose outer face follows the Gridfinity perimeter."""
    import cadquery as cq

    angle_radians = math.radians(angle_degrees)

    def wall_top_z(y_mm: float) -> float:
        return (y_mm - tray_offset_y_mm) * math.tan(angle_radians) + translation_z_mm

    front_top_z = wall_top_z(front_y_mm)
    rear_top_z = wall_top_z(rear_y_mm)
    return (
        cq.Workplane("YZ")
        .polyline(
            (
                (front_y_mm, BASE_CONNECT_Z_MM),
                (rear_y_mm, BASE_CONNECT_Z_MM),
                (rear_y_mm, rear_top_z),
                (front_y_mm, front_top_z),
            )
        )
        .close()
        .extrude(PERIMETER_WALL_THICKNESS_MM / 2.0, both=True)
        .translate((x_mm, 0.0, 0.0))
    )


def _build_back_wall(
    *,
    width_mm: float,
    rear_y_mm: float,
    tray_offset_y_mm: float,
    translation_z_mm: float,
    angle_degrees: float,
):
    """Build a full-width closed rear wall whose top follows the tray slope."""
    import cadquery as cq

    angle_radians = math.radians(angle_degrees)
    front_y_mm = rear_y_mm - PERIMETER_WALL_THICKNESS_MM

    def wall_top_z(y_mm: float) -> float:
        return (y_mm - tray_offset_y_mm) * math.tan(angle_radians) + translation_z_mm

    return (
        cq.Workplane("YZ")
        .polyline(
            (
                (front_y_mm, BASE_CONNECT_Z_MM),
                (rear_y_mm, BASE_CONNECT_Z_MM),
                (rear_y_mm, wall_top_z(rear_y_mm)),
                (front_y_mm, wall_top_z(front_y_mm)),
            )
        )
        .close()
        .extrude(width_mm / 2.0, both=True)
    )


def _build_rounded_footprint_mask(
    *, width_mm: float, depth_mm: float, bottom_z_mm: float, height_mm: float
):
    """Build a Gridfinity-sized clipping prism with typical rounded exterior corners."""
    import cadquery as cq

    return (
        cq.Workplane("XY")
        .box(width_mm, depth_mm, height_mm, centered=(True, True, False))
        .translate((0.0, 0.0, bottom_z_mm))
        .edges("|Z")
        .fillet(OUTER_CORNER_RADIUS_MM)
    )


def _build_front_stop(
    *,
    width_mm: float,
    footprint_depth_mm: float,
    front_y_mm: float,
    contact_bottom_y_mm: float,
    contact_bottom_z_mm: float,
    contact_top_y_mm: float,
    contact_top_z_mm: float,
):
    """Build one solid front stop with an angled contact face and a flat top."""
    import cadquery as cq

    stop = (
        cq.Workplane("YZ")
        .polyline(
            (
                (front_y_mm, BASE_CONNECT_Z_MM),
                (contact_bottom_y_mm, BASE_CONNECT_Z_MM),
                (contact_bottom_y_mm, contact_bottom_z_mm),
                (contact_top_y_mm, contact_top_z_mm),
                (front_y_mm, contact_top_z_mm),
            )
        )
        .close()
        .extrude(width_mm / 2.0, both=True)
    )
    rounded_footprint = _build_rounded_footprint_mask(
        width_mm=width_mm,
        depth_mm=footprint_depth_mm,
        bottom_z_mm=BASE_CONNECT_Z_MM - BOOLEAN_OVERLAP_MM,
        height_mm=(contact_top_z_mm - BASE_CONNECT_Z_MM + 2.0 * BOOLEAN_OVERLAP_MM),
    )
    return stop.intersect(rounded_footprint)


def build(
    unit_width: int = 5,
    unit_depth: int = 3,
    unit_height: int = 0,
    surface_depth_mm: float = 114.0,
    angle_degrees: float = 15.0,
    item_length_mm: float = 112.0,
    item_width_mm: float = 51.0,
    item_height_mm: float = 51.0,
    fit_clearance_mm: float = 1.0,
    support_front_z_mm: float = 8.0,
    max_drawer_height_mm: float = 91.0,
    wall_thickness_mm: float = 1.0,
):
    """Build a continuous sloped tray whose slope is solid down to the base."""
    import cadquery as cq

    _validate_parameters(
        unit_width=unit_width,
        unit_depth=unit_depth,
        unit_height=unit_height,
        surface_depth_mm=surface_depth_mm,
        angle_degrees=angle_degrees,
        item_length_mm=item_length_mm,
        item_width_mm=item_width_mm,
        item_height_mm=item_height_mm,
        fit_clearance_mm=fit_clearance_mm,
        support_front_z_mm=support_front_z_mm,
        max_drawer_height_mm=max_drawer_height_mm,
        wall_thickness_mm=wall_thickness_mm,
    )

    clearance_vertical_mm, clearance_depth_mm = _sloped_item_envelopes_mm(
        item_length_mm=item_length_mm,
        item_height_mm=item_height_mm,
        angle_degrees=angle_degrees,
        fit_clearance_mm=fit_clearance_mm,
    )
    clearance_top_z_mm = support_front_z_mm + clearance_vertical_mm
    if clearance_top_z_mm > max_drawer_height_mm:
        raise ValueError(
            f"The inclined item clearance envelope reaches {clearance_top_z_mm:.2f} mm, "
            f"above max_drawer_height_mm={max_drawer_height_mm:g}."
        )

    base = FractionalDividerGridfinityBox(
        unit_width=unit_width,
        unit_depth=unit_depth,
        unit_height=unit_height,
        horizontal_specs=(),
        vertical_specs=(),
        wall_thickness_mm=wall_thickness_mm,
        divider_thickness_mm=1.2,
        scoops=False,
        lip_enabled=False,
    ).render()
    base_bounds = base.val().BoundingBox()
    base = base.union(
        _build_rounded_footprint_mask(
            width_mm=base_bounds.xlen,
            depth_mm=base_bounds.ylen,
            bottom_z_mm=BASE_CONNECT_Z_MM - BOOLEAN_OVERLAP_MM,
            height_mm=(GRIDFINITY_BASE_TOP_Z_MM - BASE_CONNECT_Z_MM + BOOLEAN_OVERLAP_MM),
        )
    ).clean()
    tray_width_mm = base_bounds.xlen - 2.0 * PERIMETER_WALL_THICKNESS_MM
    if item_width_mm + 2.0 * fit_clearance_mm > tray_width_mm:
        raise ValueError("The item width does not fit the selected Gridfinity tray width.")
    if clearance_depth_mm > base_bounds.ylen:
        raise ValueError("The inclined item does not fit the fixed 3U tray depth.")
    if item_length_mm + 2.0 * fit_clearance_mm > surface_depth_mm:
        raise ValueError("surface_depth_mm is too short for the item length and fit clearance.")

    angle_radians = math.radians(angle_degrees)
    clearance_y_min, clearance_y_max = _clearance_y_bounds_mm(
        surface_depth_mm=surface_depth_mm,
        item_length_mm=item_length_mm,
        item_height_mm=item_height_mm,
        fit_clearance_mm=fit_clearance_mm,
        angle_degrees=angle_degrees,
    )
    usable_rear_y_mm = base_bounds.ymax - PERIMETER_WALL_THICKNESS_MM
    target_clearance_center_y_mm = (base_bounds.ymin + usable_rear_y_mm) / 2.0
    tray_offset_y_mm = target_clearance_center_y_mm - (clearance_y_min + clearance_y_max) / 2.0
    clearance_y_min += tray_offset_y_mm
    clearance_y_max += tray_offset_y_mm
    if clearance_y_min < base_bounds.ymin or clearance_y_max > usable_rear_y_mm:
        raise ValueError("The inclined item clearance envelope does not fit inside the tray walls.")

    panel = (
        cq.Workplane("XY")
        .box(tray_width_mm, surface_depth_mm, PANEL_THICKNESS_MM)
        .translate((0.0, 0.0, -PANEL_THICKNESS_MM / 2.0))
    )
    translation_z_mm = support_front_z_mm + surface_depth_mm * math.sin(angle_radians) / 2.0
    positioned_panel = panel.rotate((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), angle_degrees).translate(
        (0.0, tray_offset_y_mm, translation_z_mm)
    )
    tray_bounds = positioned_panel.val().BoundingBox()
    if (
        tray_bounds.xmin < base_bounds.xmin
        or tray_bounds.xmax > base_bounds.xmax
        or tray_bounds.ymin < base_bounds.ymin
        or tray_bounds.ymax > base_bounds.ymax
    ):
        raise ValueError("The tray surface extends outside the Gridfinity footprint.")

    contact_local_y_mm = -surface_depth_mm / 2.0 + BOOLEAN_OVERLAP_MM
    contact_bottom_y_mm = contact_local_y_mm * math.cos(angle_radians) + tray_offset_y_mm
    contact_bottom_z_mm = contact_local_y_mm * math.sin(angle_radians) + translation_z_mm
    contact_top_z_mm = FRONT_WALL_TOP_Z_MM
    contact_top_y_mm = contact_bottom_y_mm - (contact_top_z_mm - contact_bottom_z_mm) * math.tan(
        angle_radians
    )

    front_support_y_mm = (
        -surface_depth_mm * math.cos(angle_radians) / 2.0
        + PANEL_THICKNESS_MM * math.sin(angle_radians)
        + tray_offset_y_mm
    )
    rear_support_y_mm = (
        surface_depth_mm * math.cos(angle_radians) / 2.0
        + PANEL_THICKNESS_MM * math.sin(angle_radians)
        + tray_offset_y_mm
    )

    result = base.union(positioned_panel)
    result = result.union(
        _build_solid_slope_support(
            width_mm=tray_width_mm,
            front_y_mm=front_support_y_mm,
            rear_y_mm=rear_support_y_mm,
            tray_offset_y_mm=tray_offset_y_mm,
            translation_z_mm=translation_z_mm,
            angle_degrees=angle_degrees,
        )
    )

    for x_mm in (
        base_bounds.xmin + PERIMETER_WALL_THICKNESS_MM / 2.0,
        base_bounds.xmax - PERIMETER_WALL_THICKNESS_MM / 2.0,
    ):
        result = result.union(
            _build_side_wall(
                x_mm=x_mm,
                front_y_mm=base_bounds.ymin,
                rear_y_mm=base_bounds.ymax,
                tray_offset_y_mm=tray_offset_y_mm,
                translation_z_mm=translation_z_mm,
                angle_degrees=angle_degrees,
            )
        )
    result = result.union(
        _build_back_wall(
            width_mm=base_bounds.xlen,
            rear_y_mm=base_bounds.ymax,
            tray_offset_y_mm=tray_offset_y_mm,
            translation_z_mm=translation_z_mm,
            angle_degrees=angle_degrees,
        )
    )
    result = result.union(
        _build_front_stop(
            width_mm=base_bounds.xlen,
            footprint_depth_mm=base_bounds.ylen,
            front_y_mm=base_bounds.ymin,
            contact_bottom_y_mm=contact_bottom_y_mm,
            contact_bottom_z_mm=contact_bottom_z_mm,
            contact_top_y_mm=contact_top_y_mm,
            contact_top_z_mm=contact_top_z_mm,
        )
    )
    rounded_envelope = _build_rounded_footprint_mask(
        width_mm=base_bounds.xlen,
        depth_mm=base_bounds.ylen,
        bottom_z_mm=-BOOLEAN_OVERLAP_MM,
        height_mm=max_drawer_height_mm + 2.0 * BOOLEAN_OVERLAP_MM,
    )
    result = base.union(result.intersect(rounded_envelope)).clean()
    result_bounds = result.val().BoundingBox()
    if result_bounds.zmax > max_drawer_height_mm:
        raise ValueError("The tray itself exceeds max_drawer_height_mm.")
    return result


def _validate_parameters(
    *,
    unit_width: int,
    unit_depth: int,
    unit_height: int,
    surface_depth_mm: float,
    angle_degrees: float,
    item_length_mm: float,
    item_width_mm: float,
    item_height_mm: float,
    fit_clearance_mm: float,
    support_front_z_mm: float,
    max_drawer_height_mm: float,
    wall_thickness_mm: float,
) -> None:
    if unit_width <= 0:
        raise ValueError("unit_width must be a positive integer.")
    if (unit_depth, unit_height) != (3, 0):
        raise ValueError("This tray is constrained to a 3U depth and a base-only Gridfinity foot.")
    for name, value in (
        ("surface_depth_mm", surface_depth_mm),
        ("item_length_mm", item_length_mm),
        ("item_width_mm", item_width_mm),
        ("item_height_mm", item_height_mm),
        ("support_front_z_mm", support_front_z_mm),
        ("max_drawer_height_mm", max_drawer_height_mm),
        ("wall_thickness_mm", wall_thickness_mm),
    ):
        if value <= 0.0:
            raise ValueError(f"{name} must be positive.")
    if angle_degrees <= 0.0 or angle_degrees >= 30.0:
        raise ValueError("angle_degrees must be greater than 0 and less than 30.")
    if fit_clearance_mm < 0.0:
        raise ValueError("fit_clearance_mm cannot be negative.")
    if support_front_z_mm <= BASE_CONNECT_Z_MM + PANEL_THICKNESS_MM:
        raise ValueError("support_front_z_mm is too low to connect the tray to the base.")
