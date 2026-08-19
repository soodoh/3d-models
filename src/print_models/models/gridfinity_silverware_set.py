"""Split Gridfinity cutout modules for a Cambridge Beacon place setting for eight."""

from __future__ import annotations

from collections.abc import Sequence

from print_models.models.gridfinity_box import (
    FractionalDividerGridfinityBox,
    split_filled_gridfinity_cradle,
)

NAME = "gridfinity_silverware_set"
DESCRIPTION = (
    "Split fitted Gridfinity modules for eight Cambridge Beacon salad forks, dinner forks, "
    "teaspoons, dinner spoons, and individually slotted edge-down dinner knives."
)
PARAMETERS = {
    "unit_depth": 6,
    "unit_height": 6,
    "fork_unit_width": 2,
    "spoon_unit_width": 2,
    "knife_unit_width": 2,
    "split_depth_u": 3.0,
    "large_fork_width_mm": 25.0,
    "large_fork_length_mm": 208.0,
    "large_fork_stack_height_mm": 24.0,
    "large_fork_handle_bottom_width_mm": 10.0,
    "large_fork_handle_narrow_width_mm": 7.0,
    "small_fork_width_mm": 23.0,
    "small_fork_length_mm": 180.0,
    "small_fork_stack_height_mm": 22.0,
    "small_fork_handle_bottom_width_mm": 9.0,
    "small_fork_handle_narrow_width_mm": 7.0,
    "small_spoon_width_mm": 36.0,
    "small_spoon_length_mm": 175.0,
    "small_spoon_stack_height_mm": 23.0,
    "large_spoon_width_mm": 41.0,
    "large_spoon_length_mm": 201.0,
    "large_spoon_stack_height_mm": 24.0,
    "spoon_handle_bottom_width_mm": 10.0,
    "spoon_handle_narrow_width_mm": 7.0,
    "knife_count": 8,
    "knife_length_mm": 236.0,
    "knife_handle_length_mm": 125.0,
    "knife_blade_length_mm": 111.0,
    "knife_blade_width_mm": 19.0,
    "knife_blade_thickness_mm": 2.0,
    "knife_handle_width_mm": 14.0,
    "knife_handle_thickness_mm": 7.5,
    "fit_clearance_mm": 1.0,
    "vertical_clearance_mm": 1.0,
    "knife_slot_clearance_mm": 0.5,
    "cavity_gap_mm": 4.0,
    "knife_rib_mm": 1.2,
    "knife_lift_trough_width_mm": 76.0,
    "knife_lift_trough_length_mm": 26.0,
    "knife_lift_trough_extra_depth_mm": 9.0,
    "knife_lift_trough_bottom_radius_mm": 3.0,
    "finger_relief_diameter_mm": 24.0,
    "wall_thickness_mm": 1.0,
}
PRINT_NOTES = (
    "The fork and spoon modules store each group of eight in one full-depth, photo-scaled "
    "silhouette pocket that leaves a 2 mm floor and includes a 24 mm finger relief. The 2U spoon "
    "module keeps both spoons facing the same direction and staggers their cavities laterally and "
    "lengthwise. Fork handles use their measured 10 mm and 9 mm bottom widths and taper to 7 mm; "
    "spoon handles use a measured 10 mm bottom width and taper to 7 mm. Fit clearance is added "
    "outside those dimensions. The "
    "knife module stores eight knives side by side, blade-edge down, in stepped slots: the 125 mm "
    "handle sections are shallow and 8.5 mm wide by default, while the 111 mm blade sections are "
    "deeper and 3 mm wide. A rounded transverse trough beneath the handle centers provides room to "
    "lift the knives. Each 6U module is split at 3U into front and back STL parts for the "
    "configured print bed. Place each matching pair together on adjacent Gridfinity cells; the "
    "fitted cavity crosses the flush center seam. Print with the Gridfinity bases down."
)

GRIDFINITY_HEIGHT_UNIT_MM = 7.0
MINIMUM_CAVITY_FLOOR_MM = 2.0
MINIMUM_DECK_RING_MM = 2.0
BOOLEAN_OVERLAP_MM = 0.2
SPOON_CAVITY_OFFSETS_MM = ((-18.0, -20.0), (17.0, 20.0))

# Eating-end width ratios traced from the official overhead product image. Physical handle
# measurements supplied by the owner set the handle portion of each final profile.
_FORK_HEAD_WIDTH_PROFILE = (
    (0.70, 0.88),
    (0.75, 1.00),
    (0.82, 0.98),
    (0.90, 0.91),
    (0.98, 0.82),
    (1.00, 0.80),
)
_SPOON_BOWL_WIDTH_PROFILE = (
    (0.70, 0.36),
    (0.75, 0.81),
    (0.80, 0.97),
    (0.85, 1.00),
    (0.90, 0.95),
    (0.95, 0.78),
    (0.98, 0.55),
    (1.00, 0.00),
)


def _handled_utensil_width_profile(
    *,
    max_width_mm: float,
    bottom_handle_width_mm: float,
    narrow_handle_width_mm: float,
    eating_end_profile: Sequence[tuple[float, float]],
) -> tuple[tuple[float, float], ...]:
    """Return a profile with handle widths fixed in physical millimeters."""
    handle_width_span_mm = bottom_handle_width_mm - narrow_handle_width_mm
    handle_widths_mm = (
        (0.00, bottom_handle_width_mm),
        (0.02, bottom_handle_width_mm),
        (0.10, bottom_handle_width_mm - 0.10 * handle_width_span_mm),
        (0.30, bottom_handle_width_mm - 0.33 * handle_width_span_mm),
        (0.50, bottom_handle_width_mm - 0.67 * handle_width_span_mm),
        (0.65, narrow_handle_width_mm),
    )
    return (
        *(
            (length_fraction, width_mm / max_width_mm)
            for length_fraction, width_mm in handle_widths_mm
        ),
        *eating_end_profile,
    )


def _fork_width_profile(
    *, max_width_mm: float, bottom_handle_width_mm: float, narrow_handle_width_mm: float
) -> tuple[tuple[float, float], ...]:
    """Return a fork-head-scaled profile with measured handle widths."""
    return _handled_utensil_width_profile(
        max_width_mm=max_width_mm,
        bottom_handle_width_mm=bottom_handle_width_mm,
        narrow_handle_width_mm=narrow_handle_width_mm,
        eating_end_profile=_FORK_HEAD_WIDTH_PROFILE,
    )


def _spoon_width_profile(
    *, max_width_mm: float, bottom_handle_width_mm: float, narrow_handle_width_mm: float
) -> tuple[tuple[float, float], ...]:
    """Return a bowl-scaled profile with measured handle widths."""
    return _handled_utensil_width_profile(
        max_width_mm=max_width_mm,
        bottom_handle_width_mm=bottom_handle_width_mm,
        narrow_handle_width_mm=narrow_handle_width_mm,
        eating_end_profile=_SPOON_BOWL_WIDTH_PROFILE,
    )


def _monotonic_profile_samples(
    width_profile: Sequence[tuple[float, float]], *, samples_per_interval: int = 8
) -> tuple[tuple[float, float], ...]:
    """Sample a shape-preserving cubic profile without spline width undershoot."""
    fractions = tuple(point[0] for point in width_profile)
    widths = tuple(point[1] for point in width_profile)
    intervals = tuple(
        fractions[index + 1] - fractions[index] for index in range(len(fractions) - 1)
    )
    secants = tuple(
        (widths[index + 1] - widths[index]) / intervals[index] for index in range(len(intervals))
    )

    slopes = [_profile_endpoint_slope(intervals[0], intervals[1], secants[0], secants[1])]
    for index in range(1, len(fractions) - 1):
        previous_secant = secants[index - 1]
        next_secant = secants[index]
        if previous_secant * next_secant <= 0.0:
            slopes.append(0.0)
            continue
        previous_weight = 2.0 * intervals[index] + intervals[index - 1]
        next_weight = intervals[index] + 2.0 * intervals[index - 1]
        slopes.append(
            (previous_weight + next_weight)
            / (previous_weight / previous_secant + next_weight / next_secant)
        )
    slopes.append(_profile_endpoint_slope(intervals[-1], intervals[-2], secants[-1], secants[-2]))

    samples = []
    for index, interval in enumerate(intervals):
        for sample_index in range(samples_per_interval):
            parameter = sample_index / samples_per_interval
            parameter_squared = parameter * parameter
            parameter_cubed = parameter_squared * parameter
            width = (
                (2.0 * parameter_cubed - 3.0 * parameter_squared + 1.0) * widths[index]
                + (parameter_cubed - 2.0 * parameter_squared + parameter) * interval * slopes[index]
                + (-2.0 * parameter_cubed + 3.0 * parameter_squared) * widths[index + 1]
                + (parameter_cubed - parameter_squared) * interval * slopes[index + 1]
            )
            samples.append((fractions[index] + parameter * interval, width))
    samples.append(width_profile[-1])
    return tuple(samples)


def _profile_endpoint_slope(
    endpoint_interval: float,
    adjacent_interval: float,
    endpoint_secant: float,
    adjacent_secant: float,
) -> float:
    """Return a shape-preserving endpoint slope for a monotonic cubic profile."""
    slope = (
        (2.0 * endpoint_interval + adjacent_interval) * endpoint_secant
        - endpoint_interval * adjacent_secant
    ) / (endpoint_interval + adjacent_interval)
    if slope * endpoint_secant <= 0.0:
        return 0.0
    if endpoint_secant * adjacent_secant < 0.0 and abs(slope) > abs(3.0 * endpoint_secant):
        return 3.0 * endpoint_secant
    return slope


def build(
    unit_depth: int = 6,
    unit_height: int = 6,
    fork_unit_width: int = 2,
    spoon_unit_width: int = 2,
    knife_unit_width: int = 2,
    split_depth_u: float = 3.0,
    large_fork_width_mm: float = 25.0,
    large_fork_length_mm: float = 208.0,
    large_fork_stack_height_mm: float = 24.0,
    large_fork_handle_bottom_width_mm: float = 10.0,
    large_fork_handle_narrow_width_mm: float = 7.0,
    small_fork_width_mm: float = 23.0,
    small_fork_length_mm: float = 180.0,
    small_fork_stack_height_mm: float = 22.0,
    small_fork_handle_bottom_width_mm: float = 9.0,
    small_fork_handle_narrow_width_mm: float = 7.0,
    small_spoon_width_mm: float = 36.0,
    small_spoon_length_mm: float = 175.0,
    small_spoon_stack_height_mm: float = 23.0,
    large_spoon_width_mm: float = 41.0,
    large_spoon_length_mm: float = 201.0,
    large_spoon_stack_height_mm: float = 24.0,
    spoon_handle_bottom_width_mm: float = 10.0,
    spoon_handle_narrow_width_mm: float = 7.0,
    knife_count: int = 8,
    knife_length_mm: float = 236.0,
    knife_handle_length_mm: float = 125.0,
    knife_blade_length_mm: float = 111.0,
    knife_blade_width_mm: float = 19.0,
    knife_blade_thickness_mm: float = 2.0,
    knife_handle_width_mm: float = 14.0,
    knife_handle_thickness_mm: float = 7.5,
    fit_clearance_mm: float = 1.0,
    vertical_clearance_mm: float = 1.0,
    knife_slot_clearance_mm: float = 0.5,
    cavity_gap_mm: float = 4.0,
    knife_rib_mm: float = 1.2,
    knife_lift_trough_width_mm: float = 76.0,
    knife_lift_trough_length_mm: float = 26.0,
    knife_lift_trough_extra_depth_mm: float = 9.0,
    knife_lift_trough_bottom_radius_mm: float = 3.0,
    finger_relief_diameter_mm: float = 24.0,
    wall_thickness_mm: float = 1.0,
):
    """Build three fitted modules and return their six print-bed-safe halves."""
    _validate_parameters(
        unit_depth=unit_depth,
        unit_height=unit_height,
        fork_unit_width=fork_unit_width,
        spoon_unit_width=spoon_unit_width,
        knife_unit_width=knife_unit_width,
        split_depth_u=split_depth_u,
        large_fork_width_mm=large_fork_width_mm,
        large_fork_length_mm=large_fork_length_mm,
        large_fork_stack_height_mm=large_fork_stack_height_mm,
        large_fork_handle_bottom_width_mm=large_fork_handle_bottom_width_mm,
        large_fork_handle_narrow_width_mm=large_fork_handle_narrow_width_mm,
        small_fork_width_mm=small_fork_width_mm,
        small_fork_length_mm=small_fork_length_mm,
        small_fork_stack_height_mm=small_fork_stack_height_mm,
        small_fork_handle_bottom_width_mm=small_fork_handle_bottom_width_mm,
        small_fork_handle_narrow_width_mm=small_fork_handle_narrow_width_mm,
        small_spoon_width_mm=small_spoon_width_mm,
        small_spoon_length_mm=small_spoon_length_mm,
        small_spoon_stack_height_mm=small_spoon_stack_height_mm,
        large_spoon_width_mm=large_spoon_width_mm,
        large_spoon_length_mm=large_spoon_length_mm,
        large_spoon_stack_height_mm=large_spoon_stack_height_mm,
        spoon_handle_bottom_width_mm=spoon_handle_bottom_width_mm,
        spoon_handle_narrow_width_mm=spoon_handle_narrow_width_mm,
        knife_count=knife_count,
        knife_length_mm=knife_length_mm,
        knife_handle_length_mm=knife_handle_length_mm,
        knife_blade_length_mm=knife_blade_length_mm,
        knife_blade_width_mm=knife_blade_width_mm,
        knife_blade_thickness_mm=knife_blade_thickness_mm,
        knife_handle_width_mm=knife_handle_width_mm,
        knife_handle_thickness_mm=knife_handle_thickness_mm,
        fit_clearance_mm=fit_clearance_mm,
        vertical_clearance_mm=vertical_clearance_mm,
        knife_slot_clearance_mm=knife_slot_clearance_mm,
        cavity_gap_mm=cavity_gap_mm,
        knife_rib_mm=knife_rib_mm,
        knife_lift_trough_width_mm=knife_lift_trough_width_mm,
        knife_lift_trough_length_mm=knife_lift_trough_length_mm,
        knife_lift_trough_extra_depth_mm=knife_lift_trough_extra_depth_mm,
        knife_lift_trough_bottom_radius_mm=knife_lift_trough_bottom_radius_mm,
        finger_relief_diameter_mm=finger_relief_diameter_mm,
        wall_thickness_mm=wall_thickness_mm,
    )

    fork_module = _build_stacked_utensil_module(
        unit_width=fork_unit_width,
        unit_depth=unit_depth,
        unit_height=unit_height,
        utensil_specs=(
            (
                small_fork_width_mm,
                small_fork_length_mm,
                small_fork_stack_height_mm,
                _fork_width_profile(
                    max_width_mm=small_fork_width_mm,
                    bottom_handle_width_mm=small_fork_handle_bottom_width_mm,
                    narrow_handle_width_mm=small_fork_handle_narrow_width_mm,
                ),
            ),
            (
                large_fork_width_mm,
                large_fork_length_mm,
                large_fork_stack_height_mm,
                _fork_width_profile(
                    max_width_mm=large_fork_width_mm,
                    bottom_handle_width_mm=large_fork_handle_bottom_width_mm,
                    narrow_handle_width_mm=large_fork_handle_narrow_width_mm,
                ),
            ),
        ),
        fit_clearance_mm=fit_clearance_mm,
        vertical_clearance_mm=vertical_clearance_mm,
        cavity_gap_mm=cavity_gap_mm,
        finger_relief_diameter_mm=finger_relief_diameter_mm,
        wall_thickness_mm=wall_thickness_mm,
    )
    spoon_module = _build_stacked_utensil_module(
        unit_width=spoon_unit_width,
        unit_depth=unit_depth,
        unit_height=unit_height,
        utensil_specs=(
            (
                small_spoon_width_mm,
                small_spoon_length_mm,
                small_spoon_stack_height_mm,
                _spoon_width_profile(
                    max_width_mm=small_spoon_width_mm,
                    bottom_handle_width_mm=spoon_handle_bottom_width_mm,
                    narrow_handle_width_mm=spoon_handle_narrow_width_mm,
                ),
            ),
            (
                large_spoon_width_mm,
                large_spoon_length_mm,
                large_spoon_stack_height_mm,
                _spoon_width_profile(
                    max_width_mm=large_spoon_width_mm,
                    bottom_handle_width_mm=spoon_handle_bottom_width_mm,
                    narrow_handle_width_mm=spoon_handle_narrow_width_mm,
                ),
            ),
        ),
        fit_clearance_mm=fit_clearance_mm,
        vertical_clearance_mm=vertical_clearance_mm,
        cavity_gap_mm=cavity_gap_mm,
        finger_relief_diameter_mm=finger_relief_diameter_mm,
        cavity_offsets_mm=SPOON_CAVITY_OFFSETS_MM,
        wall_thickness_mm=wall_thickness_mm,
    )
    knife_module = _build_knife_module(
        unit_width=knife_unit_width,
        unit_depth=unit_depth,
        unit_height=unit_height,
        knife_count=knife_count,
        knife_length_mm=knife_length_mm,
        knife_handle_length_mm=knife_handle_length_mm,
        knife_blade_length_mm=knife_blade_length_mm,
        knife_blade_width_mm=knife_blade_width_mm,
        knife_blade_thickness_mm=knife_blade_thickness_mm,
        knife_handle_width_mm=knife_handle_width_mm,
        knife_handle_thickness_mm=knife_handle_thickness_mm,
        vertical_clearance_mm=vertical_clearance_mm,
        knife_slot_clearance_mm=knife_slot_clearance_mm,
        knife_rib_mm=knife_rib_mm,
        knife_lift_trough_width_mm=knife_lift_trough_width_mm,
        knife_lift_trough_length_mm=knife_lift_trough_length_mm,
        knife_lift_trough_extra_depth_mm=knife_lift_trough_extra_depth_mm,
        knife_lift_trough_bottom_radius_mm=knife_lift_trough_bottom_radius_mm,
        wall_thickness_mm=wall_thickness_mm,
    )

    parts = {}
    parts.update(
        _split_module(
            "fork_module",
            fork_module,
            unit_width=fork_unit_width,
            unit_depth=unit_depth,
            unit_height=unit_height,
            split_depth_u=split_depth_u,
            wall_thickness_mm=wall_thickness_mm,
        )
    )
    parts.update(
        _split_module(
            "spoon_module",
            spoon_module,
            unit_width=spoon_unit_width,
            unit_depth=unit_depth,
            unit_height=unit_height,
            split_depth_u=split_depth_u,
            wall_thickness_mm=wall_thickness_mm,
        )
    )
    parts.update(
        _split_module(
            "knife_module",
            knife_module,
            unit_width=knife_unit_width,
            unit_depth=unit_depth,
            unit_height=unit_height,
            split_depth_u=split_depth_u,
            wall_thickness_mm=wall_thickness_mm,
        )
    )
    return parts


def _build_stacked_utensil_module(
    *,
    unit_width: int,
    unit_depth: int,
    unit_height: int,
    utensil_specs: Sequence[tuple[float, float, float, tuple[tuple[float, float], ...]]],
    fit_clearance_mm: float,
    vertical_clearance_mm: float,
    cavity_gap_mm: float,
    finger_relief_diameter_mm: float,
    wall_thickness_mm: float,
    cavity_offsets_mm: Sequence[tuple[float, float]] | None = None,
):
    from cqgridfinity import GR_BASE_HEIGHT, GR_FLOOR

    box = _render_empty_module(
        unit_width=unit_width,
        unit_depth=unit_depth,
        unit_height=unit_height,
        wall_thickness_mm=wall_thickness_mm,
    )
    bounds = box.val().BoundingBox()
    floor_top_z = GR_BASE_HEIGHT + GR_FLOOR
    deck_top_z = unit_height * GRIDFINITY_HEIGHT_UNIT_MM
    inner_x_min = bounds.xmin + wall_thickness_mm
    inner_x_max = bounds.xmax - wall_thickness_mm
    inner_y_min = bounds.ymin + wall_thickness_mm
    inner_y_max = bounds.ymax - wall_thickness_mm

    cleared_widths = tuple(spec[0] + 2.0 * fit_clearance_mm for spec in utensil_specs)
    if cavity_offsets_mm is None:
        cavity_centers = tuple(
            (center_x, 0.0) for center_x in _packed_centers(cleared_widths, gap_mm=cavity_gap_mm)
        )
        total_cavity_width = sum(cleared_widths) + cavity_gap_mm * (len(cleared_widths) - 1)
        if total_cavity_width + 2.0 * MINIMUM_DECK_RING_MM > inner_x_max - inner_x_min:
            raise ValueError(
                "The utensil cavities do not leave a safe deck ring in the selected width."
            )
    else:
        if len(cavity_offsets_mm) != len(utensil_specs):
            raise ValueError("cavity_offsets_mm must provide one center for each utensil cavity.")
        cavity_centers = tuple(cavity_offsets_mm)

    pocket_depth_mm = deck_top_z - floor_top_z - MINIMUM_CAVITY_FLOOR_MM
    cavities = []
    for (center_x, center_y), (width_mm, length_mm, stack_height_mm, width_profile) in zip(
        cavity_centers, utensil_specs, strict=True
    ):
        _validate_cavity_floor(
            deck_top_z=deck_top_z,
            floor_top_z=floor_top_z,
            pocket_depth_mm=stack_height_mm + vertical_clearance_mm,
        )
        cavity = _build_utensil_cutter(
            center_x=center_x,
            center_y=center_y,
            bottom_z=deck_top_z - pocket_depth_mm,
            top_z=deck_top_z + BOOLEAN_OVERLAP_MM,
            width_mm=width_mm,
            length_mm=length_mm,
            width_profile=width_profile,
            fit_clearance_mm=fit_clearance_mm,
            finger_relief_diameter_mm=finger_relief_diameter_mm,
        )
        cavity_bounds = cavity.val().BoundingBox()
        if (
            cavity_bounds.xmin < inner_x_min + MINIMUM_DECK_RING_MM
            or cavity_bounds.xmax > inner_x_max - MINIMUM_DECK_RING_MM
            or cavity_bounds.ymin < inner_y_min + MINIMUM_DECK_RING_MM
            or cavity_bounds.ymax > inner_y_max - MINIMUM_DECK_RING_MM
        ):
            raise ValueError("A utensil cavity does not leave the required surrounding deck ring.")
        if any(
            cavity.val().distance(existing_cavity.val()) < cavity_gap_mm
            for existing_cavity in cavities
        ):
            raise ValueError("The utensil cavities do not leave the required gap.")
        cavities.append(cavity)

    cutter = cavities[0]
    for cavity in cavities[1:]:
        cutter = cutter.union(cavity)

    fill = _build_block(
        x_min=inner_x_min,
        x_max=inner_x_max,
        y_min=inner_y_min,
        y_max=inner_y_max,
        z_min=floor_top_z - BOOLEAN_OVERLAP_MM,
        z_max=deck_top_z,
    )
    return box.union(fill).cut(cutter).clean()


def _build_knife_module(
    *,
    unit_width: int,
    unit_depth: int,
    unit_height: int,
    knife_count: int,
    knife_length_mm: float,
    knife_handle_length_mm: float,
    knife_blade_length_mm: float,
    knife_blade_width_mm: float,
    knife_blade_thickness_mm: float,
    knife_handle_width_mm: float,
    knife_handle_thickness_mm: float,
    vertical_clearance_mm: float,
    knife_slot_clearance_mm: float,
    knife_rib_mm: float,
    knife_lift_trough_width_mm: float,
    knife_lift_trough_length_mm: float,
    knife_lift_trough_extra_depth_mm: float,
    knife_lift_trough_bottom_radius_mm: float,
    wall_thickness_mm: float,
):
    from cqgridfinity import GR_BASE_HEIGHT, GR_FLOOR

    box = _render_empty_module(
        unit_width=unit_width,
        unit_depth=unit_depth,
        unit_height=unit_height,
        wall_thickness_mm=wall_thickness_mm,
    )
    bounds = box.val().BoundingBox()
    floor_top_z = GR_BASE_HEIGHT + GR_FLOOR
    deck_top_z = unit_height * GRIDFINITY_HEIGHT_UNIT_MM
    inner_x_min = bounds.xmin + wall_thickness_mm
    inner_x_max = bounds.xmax - wall_thickness_mm
    inner_y_min = bounds.ymin + wall_thickness_mm
    inner_y_max = bounds.ymax - wall_thickness_mm

    handle_slot_width = knife_handle_thickness_mm + 2.0 * knife_slot_clearance_mm
    blade_slot_width = knife_blade_thickness_mm + 2.0 * knife_slot_clearance_mm
    slot_pitch = handle_slot_width + knife_rib_mm
    slots_width = knife_count * handle_slot_width + (knife_count - 1) * knife_rib_mm
    if slots_width + 2.0 * MINIMUM_DECK_RING_MM > inner_x_max - inner_x_min:
        raise ValueError("The knife slots do not leave a safe deck ring in the selected width.")
    cleared_length = knife_length_mm + 2.0 * knife_slot_clearance_mm
    if cleared_length + 2.0 * MINIMUM_DECK_RING_MM > inner_y_max - inner_y_min:
        raise ValueError("The knife slots do not leave a safe deck ring in the selected depth.")

    handle_depth = knife_handle_width_mm + vertical_clearance_mm
    blade_depth = knife_blade_width_mm + vertical_clearance_mm
    trough_depth = handle_depth + knife_lift_trough_extra_depth_mm
    _validate_cavity_floor(
        deck_top_z=deck_top_z,
        floor_top_z=floor_top_z,
        pocket_depth_mm=max(trough_depth, blade_depth),
    )
    if knife_lift_trough_width_mm + 2.0 * MINIMUM_DECK_RING_MM > inner_x_max - inner_x_min:
        raise ValueError("The knife lift trough does not leave a safe deck ring.")
    if knife_lift_trough_length_mm >= knife_handle_length_mm:
        raise ValueError("The knife lift trough must leave handle support on both sides.")
    if knife_lift_trough_bottom_radius_mm * 2.0 > min(
        knife_lift_trough_width_mm, knife_lift_trough_length_mm
    ):
        raise ValueError("The knife lift trough bottom radius is too large.")
    first_center_x = -(knife_count - 1) * slot_pitch / 2.0
    handle_start_y = -knife_length_mm / 2.0 - knife_slot_clearance_mm
    transition_y = -knife_length_mm / 2.0 + knife_handle_length_mm
    blade_end_y = knife_length_mm / 2.0 + knife_slot_clearance_mm

    cutter = None
    for slot_index in range(knife_count):
        center_x = first_center_x + slot_index * slot_pitch
        handle = _build_rounded_section_along_y(
            center_x=center_x,
            start_y=handle_start_y,
            end_y=transition_y + BOOLEAN_OVERLAP_MM,
            width_mm=handle_slot_width,
            bottom_z=deck_top_z - handle_depth,
            top_z=deck_top_z + BOOLEAN_OVERLAP_MM,
            round_start=True,
            round_end=False,
        )
        blade = _build_rounded_section_along_y(
            center_x=center_x,
            start_y=transition_y - BOOLEAN_OVERLAP_MM,
            end_y=blade_end_y,
            width_mm=blade_slot_width,
            bottom_z=deck_top_z - blade_depth,
            top_z=deck_top_z + BOOLEAN_OVERLAP_MM,
            round_start=False,
            round_end=True,
        )
        slot = handle.union(blade)
        cutter = slot if cutter is None else cutter.union(slot)

    lift_trough = _build_rounded_trough(
        center_x=0.0,
        center_y=(handle_start_y + transition_y) / 2.0,
        width_mm=knife_lift_trough_width_mm,
        length_mm=knife_lift_trough_length_mm,
        bottom_z=deck_top_z - trough_depth,
        top_z=deck_top_z + BOOLEAN_OVERLAP_MM,
        bottom_radius_mm=knife_lift_trough_bottom_radius_mm,
    )
    cutter = cutter.union(lift_trough)

    fill = _build_block(
        x_min=inner_x_min,
        x_max=inner_x_max,
        y_min=inner_y_min,
        y_max=inner_y_max,
        z_min=floor_top_z - BOOLEAN_OVERLAP_MM,
        z_max=deck_top_z,
    )
    return box.union(fill).cut(cutter).clean()


def _build_rounded_trough(
    *,
    center_x: float,
    center_y: float,
    width_mm: float,
    length_mm: float,
    bottom_z: float,
    top_z: float,
    bottom_radius_mm: float,
):
    import cadquery as cq

    radius = length_mm / 2.0
    straight_width = width_mm - length_mm
    height = top_z - bottom_z
    trough = (
        cq.Workplane("XY", origin=(center_x, center_y, bottom_z))
        .rect(straight_width, length_mm)
        .extrude(height)
    )
    for cap_center_x in (-straight_width / 2.0, straight_width / 2.0):
        cap = (
            cq.Workplane("XY", origin=(center_x + cap_center_x, center_y, bottom_z))
            .circle(radius)
            .extrude(height)
        )
        trough = trough.union(cap)
    return trough.clean().edges("<Z").fillet(bottom_radius_mm)


def _render_empty_module(
    *, unit_width: int, unit_depth: int, unit_height: int, wall_thickness_mm: float
):
    return FractionalDividerGridfinityBox(
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


def _build_utensil_cutter(
    *,
    center_x: float,
    center_y: float,
    bottom_z: float,
    top_z: float,
    width_mm: float,
    length_mm: float,
    width_profile: tuple[tuple[float, float], ...],
    fit_clearance_mm: float,
    finger_relief_diameter_mm: float,
):
    import cadquery as cq

    half_width = width_mm / 2.0
    object_start_y = -length_mm / 2.0
    object_end_y = length_mm / 2.0
    cleared_start_y = object_start_y - fit_clearance_mm
    cleared_end_y = object_end_y + fit_clearance_mm
    right_points = [
        (
            half_width * width_ratio + fit_clearance_mm,
            object_start_y + length_mm * length_fraction,
        )
        for length_fraction, width_ratio in _monotonic_profile_samples(width_profile)
    ]
    profile_closes_at_end = width_profile[-1][1] == 0.0
    if not profile_closes_at_end:
        right_points[-1] = (right_points[-1][0], cleared_end_y)
    left_points = [(-x, y) for x, y in reversed(right_points)]
    outline_points = [
        (0.0, cleared_start_y),
        *right_points,
        (0.0, cleared_end_y),
        *left_points,
    ]
    profile = (
        cq.Workplane("XY", origin=(center_x, center_y, bottom_z))
        .polyline(outline_points)
        .close()
        .extrude(top_z - bottom_z)
    )
    if profile_closes_at_end and fit_clearance_mm > 0.0:
        end_clearance = (
            cq.Workplane("XY", origin=(center_x, center_y + object_end_y, bottom_z))
            .circle(fit_clearance_mm)
            .extrude(top_z - bottom_z)
        )
        profile = profile.union(end_clearance)
    relief_center_y = object_start_y + min(28.0, length_mm * 0.16)
    relief = (
        cq.Workplane("XY", origin=(center_x, center_y + relief_center_y, bottom_z))
        .circle(finger_relief_diameter_mm / 2.0)
        .extrude(top_z - bottom_z)
    )
    return profile.union(relief).clean()


def _build_rounded_section_along_y(
    *,
    center_x: float,
    start_y: float,
    end_y: float,
    width_mm: float,
    bottom_z: float,
    top_z: float,
    round_start: bool,
    round_end: bool,
):
    import cadquery as cq

    radius = width_mm / 2.0
    body_start_y = start_y + radius if round_start else start_y
    body_end_y = end_y - radius if round_end else end_y
    height = top_z - bottom_z
    section = (
        cq.Workplane(
            "XY",
            origin=(center_x, (body_start_y + body_end_y) / 2.0, bottom_z),
        )
        .rect(width_mm, body_end_y - body_start_y)
        .extrude(height)
    )
    if round_start:
        start_cap = (
            cq.Workplane("XY", origin=(center_x, start_y + radius, bottom_z))
            .circle(radius)
            .extrude(height)
        )
        section = section.union(start_cap)
    if round_end:
        end_cap = (
            cq.Workplane("XY", origin=(center_x, end_y - radius, bottom_z))
            .circle(radius)
            .extrude(height)
        )
        section = section.union(end_cap)
    return section.clean()


def _packed_centers(widths: Sequence[float], *, gap_mm: float) -> tuple[float, ...]:
    total_width = sum(widths) + gap_mm * (len(widths) - 1)
    next_edge = -total_width / 2.0
    centers = []
    for width in widths:
        centers.append(next_edge + width / 2.0)
        next_edge += width + gap_mm
    return tuple(centers)


def _split_module(
    module_name: str,
    module,
    *,
    unit_width: int,
    unit_depth: int,
    unit_height: int,
    split_depth_u: float,
    wall_thickness_mm: float,
) -> dict[str, object]:
    split_parts = split_filled_gridfinity_cradle(
        module,
        unit_width=unit_width,
        unit_depth=unit_depth,
        unit_height=unit_height,
        split_width_positions_u=(),
        split_depth_positions_u=(split_depth_u,),
        wall_thickness_mm=wall_thickness_mm,
    )
    return {
        f"{module_name}_front": split_parts["depth_1_of_2"],
        f"{module_name}_back": split_parts["depth_2_of_2"],
    }


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


def _validate_cavity_floor(
    *, deck_top_z: float, floor_top_z: float, pocket_depth_mm: float
) -> None:
    if deck_top_z - pocket_depth_mm - floor_top_z < MINIMUM_CAVITY_FLOOR_MM:
        raise ValueError(
            "unit_height is too short for the selected cavity depth while preserving a "
            f"{MINIMUM_CAVITY_FLOOR_MM:g} mm cavity floor."
        )


def _validate_parameters(**parameters) -> None:
    integer_names = (
        "unit_depth",
        "unit_height",
        "fork_unit_width",
        "spoon_unit_width",
        "knife_unit_width",
        "knife_count",
    )
    for name in integer_names:
        value = parameters[name]
        if isinstance(value, bool) or not isinstance(value, int) or value < 1:
            raise ValueError(f"{name} must be a positive integer.")

    nonnegative_names = (
        "fit_clearance_mm",
        "vertical_clearance_mm",
        "knife_slot_clearance_mm",
    )
    for name, value in parameters.items():
        if name in integer_names or name in nonnegative_names:
            continue
        if value <= 0:
            raise ValueError(f"{name} must be greater than zero.")
    for name in nonnegative_names:
        if parameters[name] < 0:
            raise ValueError(f"{name} must not be negative.")

    unit_depth = parameters["unit_depth"]
    split_depth_u = parameters["split_depth_u"]
    if not 0.0 < split_depth_u < unit_depth:
        raise ValueError("split_depth_u must be inside the module depth.")
    for fork_size in ("large", "small"):
        bottom_width_name = f"{fork_size}_fork_handle_bottom_width_mm"
        narrow_width_name = f"{fork_size}_fork_handle_narrow_width_mm"
        fork_width_name = f"{fork_size}_fork_width_mm"
        if parameters[bottom_width_name] <= parameters[narrow_width_name]:
            raise ValueError(f"{bottom_width_name} must exceed {narrow_width_name}.")
        if parameters[bottom_width_name] >= parameters[fork_width_name]:
            raise ValueError(
                f"{fork_size.capitalize()} fork handle widths must remain narrower than the fork "
                "head."
            )
    spoon_handle_bottom_width_mm = parameters["spoon_handle_bottom_width_mm"]
    spoon_handle_narrow_width_mm = parameters["spoon_handle_narrow_width_mm"]
    if spoon_handle_bottom_width_mm <= spoon_handle_narrow_width_mm:
        raise ValueError("spoon_handle_bottom_width_mm must exceed spoon_handle_narrow_width_mm.")
    if spoon_handle_bottom_width_mm >= min(
        parameters["small_spoon_width_mm"], parameters["large_spoon_width_mm"]
    ):
        raise ValueError("Spoon handle widths must remain narrower than both spoon bowls.")
    knife_length_mm = parameters["knife_length_mm"]
    component_length = parameters["knife_handle_length_mm"] + parameters["knife_blade_length_mm"]
    if abs(component_length - knife_length_mm) > 1e-6:
        raise ValueError("knife handle and blade lengths must add up to knife_length_mm.")
