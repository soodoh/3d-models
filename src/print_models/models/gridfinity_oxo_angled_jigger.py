"""Upright Gridfinity holder for an OXO SteeL angled measuring jigger."""

from __future__ import annotations

import math

from print_models.models.gridfinity_box import FractionalDividerGridfinityBox

NAME = "gridfinity_oxo_angled_jigger"
DESCRIPTION = (
    "Upright 2x2 Gridfinity cradle for an OXO SteeL angled measuring jigger with "
    "photo-smoothed, scan-informed nested frustums and an angled transition."
)
PARAMETERS = {
    "unit_width": 2,
    "unit_depth": 2,
    "unit_height": 4,
    "jigger_height_mm": 53.0,
    "estimated_bottom_width_mm": 34.7,
    "bottom_length_mm": 37.3,
    "top_width_mm": 61.3,
    "top_length_mm": 74.0,
    "pocket_depth_mm": 18.0,
    "fit_clearance_mm": 1.0,
    "wall_thickness_mm": 1.0,
}
PRINT_NOTES = (
    "The asymmetric profiles use convex periodic curves derived from the supplied metric OBJ scan "
    "and normalized to the measured 61.3 x 74 x 53 mm envelope. Photo review removes reflective "
    "scan dents while retaining the two nested frustums, offset lower foot, and scan-informed "
    "diagonal transition. The rim is 74 mm long by 61.3 mm wide. At the 18 mm deck station, the "
    "nested lower bulge is approximately 44.1 mm long by 51.5 mm wide before clearance; this axis "
    "crossover matches the calibrated side and front photos. The 4U cradle preserves a 2 mm cavity "
    "floor. Bottom dimensions and fit clearance remain exposed for physical fit tuning."
)

GRIDFINITY_HEIGHT_UNIT_MM = 7.0
MINIMUM_CAVITY_FLOOR_MM = 2.0
MINIMUM_DECK_RING_MM = 2.0
BOOLEAN_OVERLAP_MM = 0.1
SCAN_REFERENCE_HEIGHT_MM = 53.0
SCAN_REFERENCE_BOTTOM_WIDTH_MM = 34.716
SCAN_REFERENCE_BOTTOM_LENGTH_MM = 37.303
SCAN_REFERENCE_TOP_WIDTH_MM = 61.3
SCAN_REFERENCE_TOP_LENGTH_MM = 74.0

# Convex smoothing removes reflective scan dents while retaining the measured envelopes.
_SCAN_BASE_PROFILE = (
    (15.054, -0.188),
    (14.235, 2.516),
    (13.135, 4.998),
    (11.526, 7.127),
    (9.443, 8.726),
    (7.155, 9.808),
    (4.874, 10.560),
    (2.617, 11.108),
    (0.316, 11.448),
    (-2.075, 11.553),
    (-4.594, 11.391),
    (-7.226, 10.837),
    (-9.808, 9.701),
    (-12.085, 7.905),
    (-13.889, 5.559),
    (-15.235, 2.833),
    (-16.238, -0.188),
    (-17.022, -3.557),
    (-17.601, -7.437),
    (-17.644, -11.910),
    (-16.498, -16.612),
    (-13.754, -20.756),
    (-9.656, -23.703),
    (-4.803, -25.324),
    (0.316, -25.749),
    (5.376, -25.031),
    (10.042, -23.122),
    (13.854, -19.978),
    (16.273, -15.774),
    (17.072, -11.123),
    (16.683, -6.810),
    (15.862, -3.209),
)

_SCAN_LOWER_PROFILE = (
    (19.753, -0.190),
    (17.580, 3.003),
    (15.545, 5.683),
    (13.547, 8.056),
    (11.393, 10.168),
    (8.960, 11.959),
    (6.214, 13.307),
    (3.236, 14.137),
    (0.140, 14.499),
    (-3.022, 14.442),
    (-6.186, 13.867),
    (-9.174, 12.640),
    (-11.789, 10.790),
    (-13.998, 8.505),
    (-15.970, 5.952),
    (-17.970, 3.125),
    (-20.125, -0.190),
    (-22.096, -4.262),
    (-23.050, -9.032),
    (-22.264, -13.969),
    (-19.689, -18.442),
    (-15.754, -22.085),
    (-10.901, -24.724),
    (-5.490, -26.241),
    (0.140, -26.593),
    (5.676, -25.810),
    (10.843, -23.975),
    (15.414, -21.232),
    (19.173, -17.710),
    (21.735, -13.472),
    (22.600, -8.754),
    (21.711, -4.140),
)

_SCAN_DECK_PROFILE = (
    (24.284, -0.116),
    (21.859, 4.047),
    (18.685, 7.298),
    (15.522, 9.826),
    (12.586, 11.961),
    (9.675, 13.801),
    (6.581, 15.206),
    (3.294, 16.020),
    (-0.069, 16.246),
    (-3.421, 15.965),
    (-6.705, 15.174),
    (-9.847, 13.850),
    (-12.857, 12.088),
    (-15.939, 10.004),
    (-19.299, 7.486),
    (-22.699, 4.180),
    (-25.310, -0.116),
    (-26.292, -5.094),
    (-25.484, -10.162),
    (-23.278, -14.916),
    (-20.050, -19.185),
    (-15.958, -22.810),
    (-11.117, -25.570),
    (-5.729, -27.273),
    (-0.069, -27.817),
    (5.568, -27.160),
    (10.872, -25.324),
    (15.564, -22.444),
    (19.461, -18.754),
    (22.475, -14.491),
    (24.490, -9.824),
    (25.207, -4.914),
)

_SCAN_UPPER_PROFILE = (
    (25.332, -0.011),
    (24.049, 4.653),
    (21.282, 8.577),
    (17.714, 11.505),
    (14.070, 13.652),
    (10.605, 15.354),
    (7.197, 16.710),
    (3.702, 17.583),
    (0.132, 17.828),
    (-3.415, 17.470),
    (-6.903, 16.638),
    (-10.389, 15.424),
    (-13.986, 13.829),
    (-17.776, 11.719),
    (-21.552, 8.794),
    (-24.651, 4.821),
    (-26.350, -0.011),
    (-26.453, -5.195),
    (-25.397, -10.377),
    (-23.083, -15.216),
    (-19.889, -19.637),
    (-15.850, -23.457),
    (-11.018, -26.397),
    (-5.597, -28.244),
    (0.132, -28.854),
    (5.840, -28.144),
    (11.159, -26.108),
    (15.729, -22.893),
    (19.360, -18.859),
    (22.405, -14.598),
    (24.463, -9.890),
    (25.210, -4.901),
)

_SCAN_RIM_PROFILE = (
    (30.796, 0.158),
    (30.154, 6.418),
    (28.428, 12.445),
    (25.777, 18.123),
    (22.295, 23.398),
    (17.985, 28.184),
    (12.810, 32.283),
    (6.785, 35.331),
    (0.104, 36.794),
    (-6.733, 36.156),
    (-13.036, 33.381),
    (-18.355, 29.091),
    (-22.694, 24.034),
    (-26.187, 18.556),
    (-28.759, 12.679),
    (-30.204, 6.472),
    (-30.504, 0.158),
    (-29.904, -6.094),
    (-28.622, -12.304),
    (-26.564, -18.505),
    (-23.420, -24.480),
    (-18.997, -29.782),
    (-13.386, -33.951),
    (-6.870, -36.565),
    (0.104, -37.206),
    (6.919, -35.724),
    (13.027, -32.516),
    (18.221, -28.238),
    (22.528, -23.327),
    (25.989, -17.956),
    (28.596, -12.202),
    (30.254, -6.123),
)

SCAN_PROFILE_SECTIONS = (
    (0.0, _SCAN_BASE_PROFILE),
    (3.0, _SCAN_BASE_PROFILE),
    (9.0, _SCAN_LOWER_PROFILE),
    (18.0, _SCAN_DECK_PROFILE),
    (24.0, _SCAN_UPPER_PROFILE),
    (53.0, _SCAN_RIM_PROFILE),
)


def build(
    unit_width: int = 2,
    unit_depth: int = 2,
    unit_height: int = 4,
    jigger_height_mm: float = 53.0,
    estimated_bottom_width_mm: float = 34.7,
    bottom_length_mm: float = 37.3,
    top_width_mm: float = 61.3,
    top_length_mm: float = 74.0,
    pocket_depth_mm: float = 18.0,
    fit_clearance_mm: float = 1.0,
    wall_thickness_mm: float = 1.0,
):
    """Build a filled Gridfinity cradle and subtract an upright jigger socket."""
    import cadquery as cq
    from cqgridfinity import GR_BASE_HEIGHT, GR_FLOOR

    _validate_parameters(
        unit_width=unit_width,
        unit_depth=unit_depth,
        unit_height=unit_height,
        jigger_height_mm=jigger_height_mm,
        estimated_bottom_width_mm=estimated_bottom_width_mm,
        bottom_length_mm=bottom_length_mm,
        top_width_mm=top_width_mm,
        top_length_mm=top_length_mm,
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
    opening_width_mm, opening_length_mm = _opening_dimensions_at_height(
        height_mm=pocket_depth_mm,
        jigger_height_mm=jigger_height_mm,
        estimated_bottom_width_mm=estimated_bottom_width_mm,
        bottom_length_mm=bottom_length_mm,
        top_width_mm=top_width_mm,
        top_length_mm=top_length_mm,
        fit_clearance_mm=fit_clearance_mm,
    )
    if opening_width_mm + 2.0 * MINIMUM_DECK_RING_MM > inner_width:
        raise ValueError(
            f"The {opening_width_mm:g} mm jigger opening does not leave a "
            f"{MINIMUM_DECK_RING_MM:g} mm deck ring in the selected width."
        )
    if opening_length_mm + 2.0 * MINIMUM_DECK_RING_MM > inner_depth:
        raise ValueError(
            f"The {opening_length_mm:g} mm jigger opening does not leave a "
            f"{MINIMUM_DECK_RING_MM:g} mm deck ring in the selected depth."
        )

    cutter = _build_angled_jigger_cutter(
        cavity_bottom_z=cavity_bottom_z,
        jigger_height_mm=jigger_height_mm,
        estimated_bottom_width_mm=estimated_bottom_width_mm,
        bottom_length_mm=bottom_length_mm,
        top_width_mm=top_width_mm,
        top_length_mm=top_length_mm,
        fit_clearance_mm=fit_clearance_mm,
    )
    fill_bottom_z = floor_top_z - BOOLEAN_OVERLAP_MM
    fill_height = deck_top_z - fill_bottom_z
    insert_fill = (
        cq.Workplane("XY")
        .box(inner_width, inner_depth, fill_height)
        .translate((0.0, 0.0, fill_bottom_z + fill_height / 2.0))
    )
    return box.union(insert_fill).cut(cutter).clean()


def _build_angled_jigger_cutter(
    *,
    cavity_bottom_z: float,
    jigger_height_mm: float,
    estimated_bottom_width_mm: float,
    bottom_length_mm: float,
    top_width_mm: float,
    top_length_mm: float,
    fit_clearance_mm: float,
):
    """Loft convex, periodic sections that retain the scan-derived frustum angles."""
    import cadquery as cq

    height_scale = jigger_height_mm / SCAN_REFERENCE_HEIGHT_MM
    first_reference_height, first_reference_points = SCAN_PROFILE_SECTIONS[0]
    first_height = first_reference_height * height_scale
    first_points = _scaled_profile_points(
        height_mm=first_height,
        reference_points=first_reference_points,
        jigger_height_mm=jigger_height_mm,
        estimated_bottom_width_mm=estimated_bottom_width_mm,
        bottom_length_mm=bottom_length_mm,
        top_width_mm=top_width_mm,
        top_length_mm=top_length_mm,
        fit_clearance_mm=fit_clearance_mm,
    )
    workplane = cq.Workplane("XY", origin=(0.0, 0.0, cavity_bottom_z + first_height)).spline(
        first_points, periodic=True, makeWire=True
    )
    previous_height = first_height
    for reference_height, reference_points in SCAN_PROFILE_SECTIONS[1:]:
        height = reference_height * height_scale
        points = _scaled_profile_points(
            height_mm=height,
            reference_points=reference_points,
            jigger_height_mm=jigger_height_mm,
            estimated_bottom_width_mm=estimated_bottom_width_mm,
            bottom_length_mm=bottom_length_mm,
            top_width_mm=top_width_mm,
            top_length_mm=top_length_mm,
            fit_clearance_mm=fit_clearance_mm,
        )
        workplane = workplane.workplane(offset=height - previous_height).spline(
            points, periodic=True, makeWire=True
        )
        previous_height = height
    return workplane.loft(combine=True, ruled=True).clean()


def _opening_dimensions_at_height(
    *,
    height_mm: float,
    jigger_height_mm: float,
    estimated_bottom_width_mm: float,
    bottom_length_mm: float,
    top_width_mm: float,
    top_length_mm: float,
    fit_clearance_mm: float,
) -> tuple[float, float]:
    """Return the scan-derived plan envelope where the pocket meets the deck."""
    reference_height = height_mm * SCAN_REFERENCE_HEIGHT_MM / jigger_height_mm
    reference_points = _interpolated_reference_profile(reference_height)
    points = _scaled_profile_points(
        height_mm=height_mm,
        reference_points=reference_points,
        jigger_height_mm=jigger_height_mm,
        estimated_bottom_width_mm=estimated_bottom_width_mm,
        bottom_length_mm=bottom_length_mm,
        top_width_mm=top_width_mm,
        top_length_mm=top_length_mm,
        fit_clearance_mm=fit_clearance_mm,
    )
    x_coordinates = tuple(point[0] for point in points)
    y_coordinates = tuple(point[1] for point in points)
    return max(x_coordinates) - min(x_coordinates), max(y_coordinates) - min(y_coordinates)


def _interpolated_reference_profile(
    reference_height_mm: float,
) -> tuple[tuple[float, float], ...]:
    clamped_height = min(max(reference_height_mm, 0.0), SCAN_REFERENCE_HEIGHT_MM)
    for section_index in range(1, len(SCAN_PROFILE_SECTIONS)):
        lower_height, lower_points = SCAN_PROFILE_SECTIONS[section_index - 1]
        upper_height, upper_points = SCAN_PROFILE_SECTIONS[section_index]
        if clamped_height <= upper_height:
            height_span = upper_height - lower_height
            fraction = 0.0 if height_span == 0.0 else (clamped_height - lower_height) / height_span
            return tuple(
                (
                    lower_x + (upper_x - lower_x) * fraction,
                    lower_y + (upper_y - lower_y) * fraction,
                )
                for (lower_x, lower_y), (upper_x, upper_y) in zip(
                    lower_points, upper_points, strict=True
                )
            )
    return SCAN_PROFILE_SECTIONS[-1][1]


def _scaled_profile_points(
    *,
    height_mm: float,
    reference_points: tuple[tuple[float, float], ...],
    jigger_height_mm: float,
    estimated_bottom_width_mm: float,
    bottom_length_mm: float,
    top_width_mm: float,
    top_length_mm: float,
    fit_clearance_mm: float,
) -> tuple[tuple[float, float], ...]:
    height_fraction = min(max(height_mm / jigger_height_mm, 0.0), 1.0)
    bottom_width_scale = estimated_bottom_width_mm / SCAN_REFERENCE_BOTTOM_WIDTH_MM
    bottom_length_scale = bottom_length_mm / SCAN_REFERENCE_BOTTOM_LENGTH_MM
    top_width_scale = top_width_mm / SCAN_REFERENCE_TOP_WIDTH_MM
    top_length_scale = top_length_mm / SCAN_REFERENCE_TOP_LENGTH_MM
    width_scale = bottom_width_scale + (top_width_scale - bottom_width_scale) * height_fraction
    length_scale = bottom_length_scale + (top_length_scale - bottom_length_scale) * height_fraction

    points = []
    for reference_x, reference_y in reference_points:
        x = reference_x * width_scale
        y = reference_y * length_scale
        radius = math.hypot(x, y)
        if radius > 0.0:
            clearance_scale = (radius + fit_clearance_mm) / radius
            x *= clearance_scale
            y *= clearance_scale
        points.append((x, y))
    return tuple(points)


def _validate_parameters(
    *,
    unit_width: int,
    unit_depth: int,
    unit_height: int,
    jigger_height_mm: float,
    estimated_bottom_width_mm: float,
    bottom_length_mm: float,
    top_width_mm: float,
    top_length_mm: float,
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
        ("jigger_height_mm", jigger_height_mm),
        ("estimated_bottom_width_mm", estimated_bottom_width_mm),
        ("bottom_length_mm", bottom_length_mm),
        ("top_width_mm", top_width_mm),
        ("top_length_mm", top_length_mm),
        ("pocket_depth_mm", pocket_depth_mm),
        ("wall_thickness_mm", wall_thickness_mm),
    ):
        if value <= 0:
            raise ValueError(f"{name} must be greater than zero.")

    if fit_clearance_mm < 0:
        raise ValueError("fit_clearance_mm must not be negative.")
    if top_width_mm <= estimated_bottom_width_mm:
        raise ValueError("top_width_mm must be greater than estimated_bottom_width_mm.")
    if top_length_mm <= bottom_length_mm:
        raise ValueError("top_length_mm must be greater than bottom_length_mm.")
    if pocket_depth_mm > jigger_height_mm:
        raise ValueError("pocket_depth_mm must not exceed jigger_height_mm.")
