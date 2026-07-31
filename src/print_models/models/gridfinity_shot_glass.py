"""Gridfinity holder with a straight tapered cutout for an upright shot glass."""

from __future__ import annotations

from print_models.models.gridfinity_box import FractionalDividerGridfinityBox

NAME = "gridfinity_shot_glass"
DESCRIPTION = "Upright straight-sided shot-glass holder for a compact 2x2 Gridfinity footprint."
PARAMETERS = {
    "unit_width": 2,
    "unit_depth": 2,
    "unit_height": 4,
    "glass_height_mm": 60.0,
    "bottom_diameter_mm": 38.0,
    "top_diameter_mm": 50.0,
    "pocket_depth_mm": 18.0,
    "fit_clearance_mm": 1.0,
    "wall_thickness_mm": 1.0,
}
PRINT_NOTES = (
    "Defaults fit a straight-sided 60 mm shot glass upright in a compact 2x2, 4U "
    "Gridfinity holder. The glass profile tapers linearly from a 38 mm flat bottom to a "
    "50 mm top. The 18 mm-deep pocket leaves 42 mm exposed for removal, and the 1 mm fit "
    "clearance is applied radially only."
)

GRIDFINITY_HEIGHT_UNIT_MM = 7.0
MINIMUM_CAVITY_FLOOR_MM = 2.0
MINIMUM_DECK_RING_MM = 2.0
BOOLEAN_OVERLAP_MM = 0.1


def build(
    unit_width: int = 2,
    unit_depth: int = 2,
    unit_height: int = 4,
    glass_height_mm: float = 60.0,
    bottom_diameter_mm: float = 38.0,
    top_diameter_mm: float = 50.0,
    pocket_depth_mm: float = 18.0,
    fit_clearance_mm: float = 1.0,
    wall_thickness_mm: float = 1.0,
):
    """Build a filled Gridfinity holder with one centered upright shot-glass socket."""
    import cadquery as cq
    from cqgridfinity import GR_BASE_HEIGHT, GR_FLOOR

    _validate_parameters(
        unit_width=unit_width,
        unit_depth=unit_depth,
        unit_height=unit_height,
        glass_height_mm=glass_height_mm,
        bottom_diameter_mm=bottom_diameter_mm,
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
    opening_diameter = 2.0 * (
        _shot_glass_radius_at_height(
            pocket_depth_mm,
            glass_height_mm=glass_height_mm,
            bottom_diameter_mm=bottom_diameter_mm,
            top_diameter_mm=top_diameter_mm,
        )
        + fit_clearance_mm
    )
    minimum_inner_span = min(inner_width, inner_depth)
    if opening_diameter + 2.0 * MINIMUM_DECK_RING_MM > minimum_inner_span:
        raise ValueError(
            f"The {opening_diameter:g} mm pocket opening does not leave a "
            f"{MINIMUM_DECK_RING_MM:g} mm deck ring in the selected Gridfinity footprint."
        )

    fill_bottom_z = floor_top_z - BOOLEAN_OVERLAP_MM
    fill_height = deck_top_z - fill_bottom_z
    insert_fill = (
        cq.Workplane("XY")
        .box(inner_width, inner_depth, fill_height)
        .translate((0.0, 0.0, fill_bottom_z + fill_height / 2.0))
    )
    cutter = _build_shot_glass_cutter(
        glass_bottom_z=cavity_bottom_z,
        glass_height_mm=glass_height_mm,
        bottom_diameter_mm=bottom_diameter_mm,
        top_diameter_mm=top_diameter_mm,
        fit_clearance_mm=fit_clearance_mm,
    )
    return box.union(insert_fill).cut(cutter).clean()


def _build_shot_glass_cutter(
    *,
    glass_bottom_z: float,
    glass_height_mm: float,
    bottom_diameter_mm: float,
    top_diameter_mm: float,
    fit_clearance_mm: float,
):
    """Build a flat-bottomed frustum cutter with radial-only fit clearance."""
    import cadquery as cq

    bottom_radius = bottom_diameter_mm / 2.0 + fit_clearance_mm
    top_radius = top_diameter_mm / 2.0 + fit_clearance_mm
    glass_top_z = glass_bottom_z + glass_height_mm
    profile = (
        cq.Workplane("XZ")
        .moveTo(0.0, glass_bottom_z)
        .lineTo(bottom_radius, glass_bottom_z)
        .lineTo(top_radius, glass_top_z)
        .lineTo(0.0, glass_top_z)
        .close()
    )
    return profile.revolve(360.0, (0.0, 0.0), (0.0, 1.0))


def _shot_glass_radius_at_height(
    height_mm: float,
    *,
    glass_height_mm: float,
    bottom_diameter_mm: float,
    top_diameter_mm: float,
) -> float:
    """Return the nominal straight-sided glass radius at a height above its base."""
    normalized_height = min(max(height_mm / glass_height_mm, 0.0), 1.0)
    bottom_radius = bottom_diameter_mm / 2.0
    top_radius = top_diameter_mm / 2.0
    return bottom_radius + (top_radius - bottom_radius) * normalized_height


def _validate_parameters(
    *,
    unit_width: int,
    unit_depth: int,
    unit_height: int,
    glass_height_mm: float,
    bottom_diameter_mm: float,
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
        ("glass_height_mm", glass_height_mm),
        ("bottom_diameter_mm", bottom_diameter_mm),
        ("top_diameter_mm", top_diameter_mm),
        ("pocket_depth_mm", pocket_depth_mm),
        ("wall_thickness_mm", wall_thickness_mm),
    ):
        if value <= 0:
            raise ValueError(f"{name} must be greater than zero.")

    if fit_clearance_mm < 0:
        raise ValueError("fit_clearance_mm must not be negative.")
    if top_diameter_mm <= bottom_diameter_mm:
        raise ValueError("top_diameter_mm must be greater than bottom_diameter_mm.")
    if pocket_depth_mm > glass_height_mm:
        raise ValueError("pocket_depth_mm must not exceed glass_height_mm.")
