"""Split Gridfinity cutout modules for a Cambridge Beacon place setting and steak knives."""

from __future__ import annotations

from collections.abc import Sequence
from math import cos, pi, sin

from print_models.models.gridfinity_box import (
    FractionalDividerGridfinityBox,
    split_filled_gridfinity_cradle,
)

NAME = "gridfinity_silverware_set"
DESCRIPTION = (
    "Split fitted Gridfinity modules for eight Cambridge Beacon salad forks, dinner forks, "
    "teaspoons, dinner spoons, dinner knives, and full-profile steak knives."
)
PARAMETERS = {
    "unit_depth": 6,
    "unit_height": 6,
    "fork_unit_width": 2,
    "spoon_unit_width": 2,
    "knife_unit_width": 2,
    "steak_knife_unit_width": 4,
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
    "steak_knife_count": 8,
    "steak_knife_length_mm": 222.0,
    "steak_knife_handle_length_mm": 106.0,
    "steak_knife_blade_length_mm": 116.0,
    "steak_knife_blade_width_mm": 17.6,
    "steak_knife_blade_thickness_mm": 1.0,
    "steak_knife_handle_top_width_mm": 24.0,
    "steak_knife_handle_narrow_width_mm": 16.5,
    "steak_knife_handle_main_width_mm": 21.0,
    "steak_knife_handle_bottom_width_mm": 27.5,
    "steak_knife_handle_thickness_mm": 15.2,
    "steak_knife_handle_neck_thickness_mm": 11.0,
    "steak_knife_handle_tip_thickness_mm": 6.0,
    "steak_knife_handle_cap_length_mm": 11.0,
    "steak_knife_handle_cap_peak_offset_mm": 5.0,
    "steak_knife_handle_neck_length_mm": 22.0,
    "steak_knife_handle_edge_bulb_length_mm": 18.0,
    "steak_knife_handle_edge_bulb_peak_offset_mm": 9.0,
    "steak_knife_handle_edge_bulb_flat_length_mm": 12.0,
    "steak_knife_slot_middle_extension_mm": 4.0,
    "fit_clearance_mm": 1.0,
    "vertical_clearance_mm": 1.0,
    "knife_slot_clearance_mm": 0.5,
    "cavity_gap_mm": 4.0,
    "knife_rib_mm": 1.2,
    "knife_handle_lift_angle_degrees": 3.0,
    "utensil_handle_extension_mm": 4.0,
    "utensil_grab_bay_length_mm": 40.0,
    "utensil_grab_bay_center_y_mm": -42.0,
    "utensil_lead_in_mm": 2.0,
    "utensil_lead_in_depth_mm": 8.0,
    "utensil_handle_lift_mm": 4.0,
    "wall_thickness_mm": 1.0,
}
PRINT_NOTES = (
    "The fork and spoon modules store each group of eight in fitted silhouette pockets with a "
    "2 mm floor, tapered lead-ins, lifted handles, and a shared wall-to-wall grab bay. The dinner "
    "knife module stores eight knives side by side, blade-edge down, in stepped slots. The 4U "
    "steak-knife module adds eight individually fitted edge-down slots traced from calibrated "
    "broadside and edge-on photos. Its 222 mm profiles use the measured 106 mm handle and 116 mm "
    "blade, including the 27.5/21/16.5/24 mm broadside transitions. The annotated edge profile "
    "uses a 15.2 mm main handle, a smooth transition through an 11 mm waist, and an 18 mm upper "
    "edge bulb with approximately 16 mm width and 12 mm long parallel sides before it curves "
    "inward to the 6 mm blade entry. Both knife modules add 0.5 mm clearance per slot side "
    "and tilt the handles upward by 3 degrees for pickup. Each 6U module is split at 3U into front "
    "and back STL parts; place matching pairs together on adjacent Gridfinity cells and print with "
    "the bases down."
)

GRIDFINITY_HEIGHT_UNIT_MM = 7.0
MINIMUM_CAVITY_FLOOR_MM = 2.0
MINIMUM_DECK_RING_MM = 2.0
BOOLEAN_OVERLAP_MM = 0.2
STEAK_KNIFE_MIDDLE_EXTENSION_START_MM = 22.0
SPOON_CAVITY_OFFSETS_MM = ((-18.0, -20.0), (17.0, 20.0))
SPOON_CAP_START_FRACTION = 0.90
SPOON_CAP_ARC_INTERVALS = 8

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
    steak_knife_unit_width: int = 4,
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
    steak_knife_count: int = 8,
    steak_knife_length_mm: float = 222.0,
    steak_knife_handle_length_mm: float = 106.0,
    steak_knife_blade_length_mm: float = 116.0,
    steak_knife_blade_width_mm: float = 17.6,
    steak_knife_blade_thickness_mm: float = 1.0,
    steak_knife_handle_top_width_mm: float = 24.0,
    steak_knife_handle_narrow_width_mm: float = 16.5,
    steak_knife_handle_main_width_mm: float = 21.0,
    steak_knife_handle_bottom_width_mm: float = 27.5,
    steak_knife_handle_thickness_mm: float = 15.2,
    steak_knife_handle_neck_thickness_mm: float = 11.0,
    steak_knife_handle_tip_thickness_mm: float = 6.0,
    steak_knife_handle_cap_length_mm: float = 11.0,
    steak_knife_handle_cap_peak_offset_mm: float = 5.0,
    steak_knife_handle_neck_length_mm: float = 22.0,
    steak_knife_handle_edge_bulb_length_mm: float = 18.0,
    steak_knife_handle_edge_bulb_peak_offset_mm: float = 9.0,
    steak_knife_handle_edge_bulb_flat_length_mm: float = 12.0,
    steak_knife_slot_middle_extension_mm: float = 4.0,
    fit_clearance_mm: float = 1.0,
    vertical_clearance_mm: float = 1.0,
    knife_slot_clearance_mm: float = 0.5,
    cavity_gap_mm: float = 4.0,
    knife_rib_mm: float = 1.2,
    knife_handle_lift_angle_degrees: float = 3.0,
    utensil_handle_extension_mm: float = 4.0,
    utensil_grab_bay_length_mm: float = 40.0,
    utensil_grab_bay_center_y_mm: float = -42.0,
    utensil_lead_in_mm: float = 2.0,
    utensil_lead_in_depth_mm: float = 8.0,
    utensil_handle_lift_mm: float = 4.0,
    wall_thickness_mm: float = 1.0,
):
    """Build four fitted modules and return their eight print-bed-safe halves."""
    _validate_parameters(
        unit_depth=unit_depth,
        unit_height=unit_height,
        fork_unit_width=fork_unit_width,
        spoon_unit_width=spoon_unit_width,
        knife_unit_width=knife_unit_width,
        steak_knife_unit_width=steak_knife_unit_width,
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
        steak_knife_count=steak_knife_count,
        steak_knife_length_mm=steak_knife_length_mm,
        steak_knife_handle_length_mm=steak_knife_handle_length_mm,
        steak_knife_blade_length_mm=steak_knife_blade_length_mm,
        steak_knife_blade_width_mm=steak_knife_blade_width_mm,
        steak_knife_blade_thickness_mm=steak_knife_blade_thickness_mm,
        steak_knife_handle_top_width_mm=steak_knife_handle_top_width_mm,
        steak_knife_handle_narrow_width_mm=steak_knife_handle_narrow_width_mm,
        steak_knife_handle_main_width_mm=steak_knife_handle_main_width_mm,
        steak_knife_handle_bottom_width_mm=steak_knife_handle_bottom_width_mm,
        steak_knife_handle_thickness_mm=steak_knife_handle_thickness_mm,
        steak_knife_handle_neck_thickness_mm=steak_knife_handle_neck_thickness_mm,
        steak_knife_handle_tip_thickness_mm=steak_knife_handle_tip_thickness_mm,
        steak_knife_handle_cap_length_mm=steak_knife_handle_cap_length_mm,
        steak_knife_handle_cap_peak_offset_mm=steak_knife_handle_cap_peak_offset_mm,
        steak_knife_handle_neck_length_mm=steak_knife_handle_neck_length_mm,
        steak_knife_handle_edge_bulb_length_mm=steak_knife_handle_edge_bulb_length_mm,
        steak_knife_handle_edge_bulb_peak_offset_mm=steak_knife_handle_edge_bulb_peak_offset_mm,
        steak_knife_handle_edge_bulb_flat_length_mm=steak_knife_handle_edge_bulb_flat_length_mm,
        steak_knife_slot_middle_extension_mm=steak_knife_slot_middle_extension_mm,
        fit_clearance_mm=fit_clearance_mm,
        vertical_clearance_mm=vertical_clearance_mm,
        knife_slot_clearance_mm=knife_slot_clearance_mm,
        cavity_gap_mm=cavity_gap_mm,
        knife_rib_mm=knife_rib_mm,
        knife_handle_lift_angle_degrees=knife_handle_lift_angle_degrees,
        utensil_handle_extension_mm=utensil_handle_extension_mm,
        utensil_grab_bay_length_mm=utensil_grab_bay_length_mm,
        utensil_grab_bay_center_y_mm=utensil_grab_bay_center_y_mm,
        utensil_lead_in_mm=utensil_lead_in_mm,
        utensil_lead_in_depth_mm=utensil_lead_in_depth_mm,
        utensil_handle_lift_mm=utensil_handle_lift_mm,
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
        handle_extension_mm=utensil_handle_extension_mm,
        grab_bay_length_mm=utensil_grab_bay_length_mm,
        grab_bay_center_y_mm=utensil_grab_bay_center_y_mm,
        lead_in_mm=utensil_lead_in_mm,
        lead_in_depth_mm=utensil_lead_in_depth_mm,
        handle_lift_mm=utensil_handle_lift_mm,
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
        handle_extension_mm=utensil_handle_extension_mm,
        grab_bay_length_mm=utensil_grab_bay_length_mm,
        grab_bay_center_y_mm=utensil_grab_bay_center_y_mm,
        lead_in_mm=utensil_lead_in_mm,
        lead_in_depth_mm=utensil_lead_in_depth_mm,
        handle_lift_mm=utensil_handle_lift_mm,
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
        knife_handle_lift_angle_degrees=knife_handle_lift_angle_degrees,
        wall_thickness_mm=wall_thickness_mm,
    )
    steak_knife_physical_profile = _steak_knife_section_profile(
        knife_length_mm=steak_knife_length_mm,
        handle_length_mm=steak_knife_handle_length_mm,
        blade_length_mm=steak_knife_blade_length_mm,
        blade_width_mm=steak_knife_blade_width_mm,
        blade_thickness_mm=steak_knife_blade_thickness_mm,
        handle_top_width_mm=steak_knife_handle_top_width_mm,
        handle_narrow_width_mm=steak_knife_handle_narrow_width_mm,
        handle_main_width_mm=steak_knife_handle_main_width_mm,
        handle_bottom_width_mm=steak_knife_handle_bottom_width_mm,
        handle_thickness_mm=steak_knife_handle_thickness_mm,
        handle_neck_thickness_mm=steak_knife_handle_neck_thickness_mm,
        handle_tip_thickness_mm=steak_knife_handle_tip_thickness_mm,
        handle_cap_length_mm=steak_knife_handle_cap_length_mm,
        handle_cap_peak_offset_mm=steak_knife_handle_cap_peak_offset_mm,
        handle_neck_length_mm=steak_knife_handle_neck_length_mm,
        handle_edge_bulb_length_mm=steak_knife_handle_edge_bulb_length_mm,
        handle_edge_bulb_peak_offset_mm=steak_knife_handle_edge_bulb_peak_offset_mm,
        handle_edge_bulb_flat_length_mm=steak_knife_handle_edge_bulb_flat_length_mm,
    )
    steak_knife_slot_profile = _extend_steak_knife_profile_middle(
        steak_knife_physical_profile,
        extension_mm=steak_knife_slot_middle_extension_mm,
    )
    steak_knife_module = _build_knife_module(
        unit_width=steak_knife_unit_width,
        unit_depth=unit_depth,
        unit_height=unit_height,
        knife_count=steak_knife_count,
        knife_length_mm=steak_knife_length_mm + steak_knife_slot_middle_extension_mm,
        knife_handle_length_mm=(
            steak_knife_handle_length_mm + steak_knife_slot_middle_extension_mm
        ),
        knife_blade_length_mm=steak_knife_blade_length_mm,
        knife_blade_width_mm=steak_knife_blade_width_mm,
        knife_blade_thickness_mm=steak_knife_blade_thickness_mm,
        knife_handle_width_mm=steak_knife_handle_bottom_width_mm,
        knife_handle_thickness_mm=steak_knife_handle_thickness_mm,
        vertical_clearance_mm=vertical_clearance_mm,
        knife_slot_clearance_mm=knife_slot_clearance_mm,
        knife_rib_mm=knife_rib_mm,
        knife_handle_lift_angle_degrees=knife_handle_lift_angle_degrees,
        wall_thickness_mm=wall_thickness_mm,
        section_profile=steak_knife_slot_profile,
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
    parts.update(
        _split_module(
            "steak_knife_module",
            steak_knife_module,
            unit_width=steak_knife_unit_width,
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
    handle_extension_mm: float,
    grab_bay_length_mm: float,
    grab_bay_center_y_mm: float,
    lead_in_mm: float,
    lead_in_depth_mm: float,
    handle_lift_mm: float,
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
    pocket_bottom_z = deck_top_z - pocket_depth_mm
    cavities = []
    fitted_cavities = []
    for (center_x, center_y), (width_mm, length_mm, stack_height_mm, width_profile) in zip(
        cavity_centers, utensil_specs, strict=True
    ):
        _validate_cavity_floor(
            deck_top_z=deck_top_z,
            floor_top_z=floor_top_z,
            pocket_depth_mm=stack_height_mm + vertical_clearance_mm + handle_lift_mm,
        )
        fitted_cavity = _build_utensil_profile_cutter(
            center_x=center_x,
            center_y=center_y,
            bottom_z=pocket_bottom_z,
            top_z=deck_top_z + BOOLEAN_OVERLAP_MM,
            width_mm=width_mm,
            length_mm=length_mm,
            width_profile=width_profile,
            clearance_mm=fit_clearance_mm,
            handle_extension_mm=handle_extension_mm,
        )
        cavity = _build_utensil_cutter(
            center_x=center_x,
            center_y=center_y,
            bottom_z=pocket_bottom_z,
            top_z=deck_top_z + BOOLEAN_OVERLAP_MM,
            width_mm=width_mm,
            length_mm=length_mm,
            width_profile=width_profile,
            fit_clearance_mm=fit_clearance_mm,
            handle_extension_mm=handle_extension_mm,
            lead_in_mm=lead_in_mm,
            lead_in_depth_mm=lead_in_depth_mm,
            handle_lift_mm=handle_lift_mm,
        )
        fitted_bounds = fitted_cavity.val().BoundingBox()
        if (
            fitted_bounds.xmin < inner_x_min + MINIMUM_DECK_RING_MM
            or fitted_bounds.xmax > inner_x_max - MINIMUM_DECK_RING_MM
            or fitted_bounds.ymin < inner_y_min + MINIMUM_DECK_RING_MM
            or fitted_bounds.ymax > inner_y_max - MINIMUM_DECK_RING_MM
        ):
            raise ValueError("A utensil cavity does not leave the required surrounding deck ring.")
        lead_in_bounds = cavity.val().BoundingBox()
        if (
            lead_in_bounds.xmin < inner_x_min
            or lead_in_bounds.xmax > inner_x_max
            or lead_in_bounds.ymin < inner_y_min
            or lead_in_bounds.ymax > inner_y_max
        ):
            raise ValueError("A utensil lead-in intersects the module wall.")
        if any(
            fitted_cavity.val().distance(existing_cavity.val()) < cavity_gap_mm
            for existing_cavity in fitted_cavities
        ):
            raise ValueError("The fitted utensil cavities do not leave the required gap.")
        fitted_cavities.append(fitted_cavity)
        cavities.append(cavity)

    grab_bay = _build_unified_grab_bay_cutter(
        center_y=grab_bay_center_y_mm,
        bottom_z=pocket_bottom_z,
        top_z=deck_top_z + BOOLEAN_OVERLAP_MM,
        width_mm=inner_x_max - inner_x_min,
        length_mm=grab_bay_length_mm,
        lead_in_mm=lead_in_mm,
        lead_in_depth_mm=lead_in_depth_mm,
        handle_lift_mm=handle_lift_mm,
    )
    grab_bay_bounds = grab_bay.val().BoundingBox()
    if (
        grab_bay_bounds.xmin < inner_x_min - 1e-6
        or grab_bay_bounds.xmax > inner_x_max + 1e-6
        or grab_bay_bounds.ymin < inner_y_min
        or grab_bay_bounds.ymax > 0.0
    ):
        raise ValueError("The unified utensil grab bay must remain inside the lower module half.")
    if any(grab_bay.val().distance(cavity.val()) > 1e-6 for cavity in fitted_cavities):
        raise ValueError("The unified utensil grab bay must intersect every utensil handle pocket.")

    cutter = cavities[0]
    for cavity in cavities[1:]:
        cutter = cutter.union(cavity)
    cutter = cutter.union(grab_bay)

    fill = _build_block(
        x_min=inner_x_min,
        x_max=inner_x_max,
        y_min=inner_y_min,
        y_max=inner_y_max,
        z_min=floor_top_z - BOOLEAN_OVERLAP_MM,
        z_max=deck_top_z,
    )
    return box.union(fill).cut(cutter).clean()


def _steak_knife_section_profile(
    *,
    knife_length_mm: float,
    handle_length_mm: float,
    blade_length_mm: float,
    blade_width_mm: float,
    blade_thickness_mm: float,
    handle_top_width_mm: float,
    handle_narrow_width_mm: float,
    handle_main_width_mm: float,
    handle_bottom_width_mm: float,
    handle_thickness_mm: float,
    handle_neck_thickness_mm: float,
    handle_tip_thickness_mm: float,
    handle_cap_length_mm: float,
    handle_cap_peak_offset_mm: float,
    handle_neck_length_mm: float,
    handle_edge_bulb_length_mm: float,
    handle_edge_bulb_peak_offset_mm: float,
    handle_edge_bulb_flat_length_mm: float,
) -> tuple[tuple[float, float, float], ...]:
    """Return independent edge and broadside curves fitted to the physical handle traces."""
    handle_transition_mm = min(BOOLEAN_OVERLAP_MM, handle_length_mm * 0.01)
    blade_start_mm = handle_length_mm
    handle_end_station_mm = handle_length_mm - handle_transition_mm
    cap_start_mm = handle_length_mm - handle_cap_length_mm
    cap_peak_mm = handle_length_mm - handle_cap_peak_offset_mm
    neck_start_mm = cap_start_mm - handle_neck_length_mm
    neck_midpoint_mm = (neck_start_mm + cap_start_mm) / 2.0
    lower_neck_curve_mm = neck_start_mm - 0.50 * handle_neck_length_mm
    pre_neck_curve_mm = neck_start_mm - 0.23 * handle_neck_length_mm
    narrow_broadside_mm = neck_start_mm + 0.64 * handle_neck_length_mm
    early_cap_mm = cap_start_mm + 0.35 * (cap_peak_mm - cap_start_mm)
    late_cap_mm = cap_start_mm + 0.70 * (cap_peak_mm - cap_start_mm)
    early_tip_mm = cap_peak_mm + 0.35 * (handle_end_station_mm - cap_peak_mm)
    late_tip_mm = cap_peak_mm + 0.70 * (handle_end_station_mm - cap_peak_mm)
    edge_bulb_start_mm = handle_length_mm - handle_edge_bulb_length_mm
    edge_bulb_peak_mm = handle_length_mm - handle_edge_bulb_peak_offset_mm
    edge_bulb_half_flat_mm = handle_edge_bulb_flat_length_mm / 2.0
    edge_plateau_start_mm = edge_bulb_peak_mm - edge_bulb_half_flat_mm
    edge_plateau_end_mm = edge_bulb_peak_mm + edge_bulb_half_flat_mm

    edge_controls = (
        (0.0, 0.2),
        (1.5, 0.42 * handle_thickness_mm),
        (3.0, 0.72 * handle_thickness_mm),
        (5.0, 0.94 * handle_thickness_mm),
        (7.0, handle_thickness_mm),
        (lower_neck_curve_mm, handle_thickness_mm),
        (pre_neck_curve_mm, 0.90 * handle_thickness_mm),
        (neck_start_mm, 0.84 * handle_thickness_mm),
        (neck_start_mm + 0.23 * handle_neck_length_mm, 1.06 * handle_neck_thickness_mm),
        (neck_midpoint_mm, handle_neck_thickness_mm),
        (edge_bulb_start_mm, 0.92 * handle_thickness_mm),
        (edge_plateau_start_mm, 1.04 * handle_thickness_mm),
        (edge_plateau_end_mm, 1.04 * handle_thickness_mm),
        (handle_end_station_mm, handle_tip_thickness_mm),
    )
    broadside_controls = (
        (0.0, 0.0),
        (3.0, 0.31 * handle_bottom_width_mm),
        (6.0, 0.69 * handle_bottom_width_mm),
        (9.0, 0.92 * handle_bottom_width_mm),
        (12.0, handle_bottom_width_mm),
        (
            18.0,
            handle_main_width_mm + 0.40 * (handle_bottom_width_mm - handle_main_width_mm),
        ),
        (22.0, handle_main_width_mm),
        (lower_neck_curve_mm, handle_main_width_mm),
        (pre_neck_curve_mm, 0.99 * handle_main_width_mm),
        (neck_start_mm, 0.97 * handle_main_width_mm),
        (neck_start_mm + 0.23 * handle_neck_length_mm, 0.90 * handle_main_width_mm),
        (neck_midpoint_mm, 1.03 * handle_narrow_width_mm),
        (narrow_broadside_mm, handle_narrow_width_mm),
        (neck_start_mm + 0.77 * handle_neck_length_mm, 1.02 * handle_narrow_width_mm),
        (cap_start_mm, 0.80 * handle_top_width_mm),
        (early_cap_mm, 0.89 * handle_top_width_mm),
        (late_cap_mm, 0.97 * handle_top_width_mm),
        (cap_peak_mm, handle_top_width_mm),
        (early_tip_mm, handle_top_width_mm),
        (late_tip_mm, handle_top_width_mm),
        (handle_end_station_mm, handle_top_width_mm),
    )
    handle_distances = tuple(
        sorted({distance_mm for distance_mm, _ in (*edge_controls, *broadside_controls)})
    )
    handle_sections = tuple(
        (
            distance_mm,
            _interpolate_profile_value(edge_controls, distance_mm),
            _interpolate_profile_value(broadside_controls, distance_mm),
        )
        for distance_mm in handle_distances
    )
    return (
        *handle_sections,
        (blade_start_mm, blade_thickness_mm, blade_width_mm),
        (blade_start_mm + 0.22 * blade_length_mm, blade_thickness_mm, blade_width_mm),
        (blade_start_mm + 0.46 * blade_length_mm, blade_thickness_mm, 0.97 * blade_width_mm),
        (blade_start_mm + 0.68 * blade_length_mm, blade_thickness_mm, 0.85 * blade_width_mm),
        (blade_start_mm + 0.86 * blade_length_mm, blade_thickness_mm, 0.51 * blade_width_mm),
        (knife_length_mm, blade_thickness_mm, 0.0),
    )


def _extend_steak_knife_profile_middle(
    profile: Sequence[tuple[float, float, float]], *, extension_mm: float
) -> tuple[tuple[float, float, float], ...]:
    """Extend the straight middle handle section without changing either end profile."""
    return tuple(
        (
            distance_mm + extension_mm,
            thickness_mm,
            edge_depth_mm,
        )
        if distance_mm > STEAK_KNIFE_MIDDLE_EXTENSION_START_MM
        else (distance_mm, thickness_mm, edge_depth_mm)
        for distance_mm, thickness_mm, edge_depth_mm in profile
    )


def _interpolate_profile_value(
    control_points: Sequence[tuple[float, float]], distance_mm: float
) -> float:
    for (start_distance, start_value), (end_distance, end_value) in zip(
        control_points, control_points[1:], strict=False
    ):
        if distance_mm <= end_distance:
            span_fraction = (distance_mm - start_distance) / (end_distance - start_distance)
            return start_value + span_fraction * (end_value - start_value)
    return control_points[-1][1]


def _steak_knife_broadside_spine_offset(
    distance_mm: float, *, handle_bottom_width_mm: float
) -> float:
    """Return the traced spine offset that centers the pointed handle butt."""
    controls = (
        (0.0, -0.50 * handle_bottom_width_mm),
        (3.0, -0.38 * handle_bottom_width_mm),
        (6.0, -0.22 * handle_bottom_width_mm),
        (9.0, -0.08 * handle_bottom_width_mm),
        (12.0, 0.0),
    )
    if distance_mm >= controls[-1][0]:
        return 0.0
    return _interpolate_profile_value(controls, distance_mm)


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
    knife_handle_lift_angle_degrees: float,
    wall_thickness_mm: float,
    section_profile: Sequence[tuple[float, float, float]] | None = None,
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

    if section_profile is None:
        maximum_thickness_mm = knife_handle_thickness_mm
        maximum_edge_depth_mm = max(knife_handle_width_mm, knife_blade_width_mm)
    else:
        _validate_knife_section_profile(section_profile, knife_length_mm=knife_length_mm)
        maximum_thickness_mm = max(section[1] for section in section_profile)
        maximum_edge_depth_mm = max(section[2] for section in section_profile)

    maximum_slot_width = maximum_thickness_mm + 2.0 * knife_slot_clearance_mm
    slot_pitch = maximum_slot_width + knife_rib_mm
    slots_width = knife_count * maximum_slot_width + (knife_count - 1) * knife_rib_mm
    if slots_width + 2.0 * MINIMUM_DECK_RING_MM > inner_x_max - inner_x_min:
        raise ValueError("The knife slots do not leave a safe deck ring in the selected width.")
    cleared_length = knife_length_mm + 2.0 * knife_slot_clearance_mm
    if cleared_length + 2.0 * MINIMUM_DECK_RING_MM > inner_y_max - inner_y_min:
        raise ValueError("The knife slots do not leave a safe deck ring in the selected depth.")

    maximum_slot_depth = maximum_edge_depth_mm + vertical_clearance_mm
    _validate_cavity_floor(
        deck_top_z=deck_top_z,
        floor_top_z=floor_top_z,
        pocket_depth_mm=maximum_slot_depth,
    )
    first_center_x = -(knife_count - 1) * slot_pitch / 2.0
    handle_start_y = -knife_length_mm / 2.0 - knife_slot_clearance_mm
    transition_y = -knife_length_mm / 2.0 + knife_handle_length_mm
    blade_tip_y = knife_length_mm / 2.0
    blade_end_y = blade_tip_y + knife_slot_clearance_mm

    if section_profile is None:
        blade_depth = knife_blade_width_mm + vertical_clearance_mm
    else:
        blade_depth = section_profile[-1][2] + vertical_clearance_mm
    blade_pivot_z = deck_top_z - blade_depth

    cutter = None
    for slot_index in range(knife_count):
        center_x = first_center_x + slot_index * slot_pitch
        if section_profile is None:
            handle_slot_width = knife_handle_thickness_mm + 2.0 * knife_slot_clearance_mm
            blade_slot_width = knife_blade_thickness_mm + 2.0 * knife_slot_clearance_mm
            handle_depth = knife_handle_width_mm + vertical_clearance_mm
            blade_depth = knife_blade_width_mm + vertical_clearance_mm
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
        else:
            slot = _build_profiled_knife_slot(
                center_x=center_x,
                start_y=-knife_length_mm / 2.0,
                deck_top_z=deck_top_z,
                knife_length_mm=knife_length_mm,
                section_profile=section_profile,
                lateral_clearance_mm=knife_slot_clearance_mm,
                vertical_clearance_mm=vertical_clearance_mm,
            )
        slot = slot.rotate(
            (0.0, blade_tip_y, blade_pivot_z),
            (1.0, blade_tip_y, blade_pivot_z),
            -knife_handle_lift_angle_degrees,
        )
        slot_bounds = slot.val().BoundingBox()
        if (
            slot_bounds.ymin < inner_y_min + MINIMUM_DECK_RING_MM
            or slot_bounds.ymax > inner_y_max - MINIMUM_DECK_RING_MM
        ):
            raise ValueError(
                "The angled knife slots do not leave a safe deck ring at the selected angle."
            )
        cutter = slot if cutter is None else cutter.union(slot)

    fill = _build_block(
        x_min=inner_x_min,
        x_max=inner_x_max,
        y_min=inner_y_min,
        y_max=inner_y_max,
        z_min=floor_top_z - BOOLEAN_OVERLAP_MM,
        z_max=deck_top_z,
    )
    return box.union(fill).cut(cutter).clean()


def _validate_knife_section_profile(
    section_profile: Sequence[tuple[float, float, float]], *, knife_length_mm: float
) -> None:
    if len(section_profile) < 2:
        raise ValueError("section_profile must contain at least two stations.")
    distances = tuple(section[0] for section in section_profile)
    if abs(distances[0]) > 1e-6 or abs(distances[-1] - knife_length_mm) > 1e-6:
        raise ValueError("section_profile must span the complete knife length.")
    if any(end <= start for start, end in zip(distances, distances[1:], strict=False)):
        raise ValueError("section_profile station distances must increase.")
    if any(thickness <= 0.0 or edge_depth < 0.0 for _, thickness, edge_depth in section_profile):
        raise ValueError(
            "section_profile dimensions must be positive, except for a zero tip depth."
        )


def _build_profiled_knife_slot(
    *,
    center_x: float,
    start_y: float,
    deck_top_z: float,
    knife_length_mm: float,
    section_profile: Sequence[tuple[float, float, float]],
    lateral_clearance_mm: float,
    vertical_clearance_mm: float,
):
    import cadquery as cq

    extended_profile = list(section_profile)
    if lateral_clearance_mm > 0.0:
        extended_profile.insert(
            0,
            (-lateral_clearance_mm, section_profile[0][1], section_profile[0][2]),
        )
        extended_profile.append(
            (
                knife_length_mm + lateral_clearance_mm,
                section_profile[-1][1],
                section_profile[-1][2],
            )
        )

    wires = []
    top_z = deck_top_z + BOOLEAN_OVERLAP_MM
    for distance_mm, thickness_mm, edge_depth_mm in extended_profile:
        bottom_z = deck_top_z - edge_depth_mm - vertical_clearance_mm
        center_z = (bottom_z + top_z) / 2.0
        plane = cq.Plane(
            origin=(center_x, start_y + distance_mm, center_z),
            xDir=(1.0, 0.0, 0.0),
            normal=(0.0, 1.0, 0.0),
        )
        wires.append(
            cq.Workplane(plane)
            .rect(thickness_mm + 2.0 * lateral_clearance_mm, top_z - bottom_z)
            .val()
        )
    return cq.Workplane(obj=cq.Solid.makeLoft(wires, ruled=True))


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


def _utensil_outline_points(
    *,
    width_mm: float,
    length_mm: float,
    width_profile: tuple[tuple[float, float], ...],
    clearance_mm: float,
    handle_extension_mm: float,
) -> tuple[tuple[float, float], ...]:
    half_width = width_mm / 2.0
    object_start_y = -length_mm / 2.0
    object_end_y = length_mm / 2.0
    extended_start_y = object_start_y - handle_extension_mm
    cleared_start_y = extended_start_y - clearance_mm
    cleared_end_y = object_end_y + clearance_mm
    profile_closes_at_end = width_profile[-1][1] == 0.0
    sampled_profile = _monotonic_profile_samples(width_profile)
    if profile_closes_at_end:
        cap_width_ratio = min(
            width_profile,
            key=lambda point: abs(point[0] - SPOON_CAP_START_FRACTION),
        )[1]
        base_cap_radius = half_width * cap_width_ratio
        cap_center_fraction = 1.0 - base_cap_radius / length_mm
        sampled_profile = tuple(
            point for point in sampled_profile if point[0] <= cap_center_fraction
        )
    first_half_width = half_width * sampled_profile[0][1] + clearance_mm
    right_points = [
        (first_half_width, extended_start_y),
        *(
            (
                half_width * width_ratio + clearance_mm,
                object_start_y + length_mm * length_fraction,
            )
            for length_fraction, width_ratio in sampled_profile
        ),
    ]
    if profile_closes_at_end:
        cap_center_y = object_end_y - base_cap_radius
        cap_radius = base_cap_radius + clearance_mm
        right_points[-1] = (cap_radius, cap_center_y)
        right_points.extend(
            (
                cap_radius * cos(pi * arc_index / (2.0 * SPOON_CAP_ARC_INTERVALS)),
                cap_center_y + cap_radius * sin(pi * arc_index / (2.0 * SPOON_CAP_ARC_INTERVALS)),
            )
            for arc_index in range(1, SPOON_CAP_ARC_INTERVALS)
        )
    else:
        right_points[-1] = (right_points[-1][0], cleared_end_y)
    left_points = [(-x, y) for x, y in reversed(right_points)]
    return (
        (0.0, cleared_start_y),
        *right_points,
        (0.0, cleared_end_y),
        *left_points,
    )


def _build_utensil_profile_cutter(
    *,
    center_x: float,
    center_y: float,
    bottom_z: float,
    top_z: float,
    width_mm: float,
    length_mm: float,
    width_profile: tuple[tuple[float, float], ...],
    clearance_mm: float,
    handle_extension_mm: float,
):
    import cadquery as cq

    outline_points = _utensil_outline_points(
        width_mm=width_mm,
        length_mm=length_mm,
        width_profile=width_profile,
        clearance_mm=clearance_mm,
        handle_extension_mm=handle_extension_mm,
    )
    profile = (
        cq.Workplane("XY", origin=(center_x, center_y, bottom_z))
        .polyline(outline_points)
        .close()
        .extrude(top_z - bottom_z)
    )
    return profile.clean()


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
    handle_extension_mm: float = 4.0,
    lead_in_mm: float = 2.0,
    lead_in_depth_mm: float = 8.0,
    handle_lift_mm: float = 4.0,
):
    import cadquery as cq

    profile = _build_utensil_profile_cutter(
        center_x=center_x,
        center_y=center_y,
        bottom_z=bottom_z,
        top_z=top_z,
        width_mm=width_mm,
        length_mm=length_mm,
        width_profile=width_profile,
        clearance_mm=fit_clearance_mm,
        handle_extension_mm=handle_extension_mm,
    )
    object_start_y = -length_mm / 2.0
    lead_start_z = top_z - BOOLEAN_OVERLAP_MM - lead_in_depth_mm
    lower_outline = _utensil_outline_points(
        width_mm=width_mm,
        length_mm=length_mm,
        width_profile=width_profile,
        clearance_mm=fit_clearance_mm,
        handle_extension_mm=handle_extension_mm,
    )
    upper_outline = _utensil_outline_points(
        width_mm=width_mm,
        length_mm=length_mm,
        width_profile=width_profile,
        clearance_mm=fit_clearance_mm + lead_in_mm,
        handle_extension_mm=handle_extension_mm,
    )
    profile_lead_in = (
        cq.Workplane("XY", origin=(center_x, center_y, lead_start_z))
        .polyline(lower_outline)
        .close()
        .workplane(offset=top_z - lead_start_z)
        .polyline(upper_outline)
        .close()
        .loft(combine=True)
    )
    cutter = profile.union(profile_lead_in)

    handle_lift_end_y = object_start_y + 0.65 * length_mm
    wedge_half_width = width_mm / 2.0 + fit_clearance_mm + lead_in_mm + BOOLEAN_OVERLAP_MM
    lift_wedge = (
        cq.Workplane("YZ", origin=(center_x, center_y, 0.0))
        .polyline(
            (
                (
                    object_start_y - handle_extension_mm - fit_clearance_mm - lead_in_mm,
                    bottom_z - BOOLEAN_OVERLAP_MM,
                ),
                (
                    object_start_y - handle_extension_mm - fit_clearance_mm - lead_in_mm,
                    bottom_z + handle_lift_mm,
                ),
                (
                    object_start_y,
                    bottom_z + handle_lift_mm,
                ),
                (handle_lift_end_y, bottom_z - BOOLEAN_OVERLAP_MM),
            )
        )
        .close()
        .extrude(wedge_half_width, both=True)
    )
    return cutter.cut(lift_wedge).clean()


def _build_unified_grab_bay_cutter(
    *,
    center_y: float,
    bottom_z: float,
    top_z: float,
    width_mm: float,
    length_mm: float,
    lead_in_mm: float,
    lead_in_depth_mm: float,
    handle_lift_mm: float,
):
    import cadquery as cq

    lower_radius = length_mm / 2.0
    upper_radius = lower_radius + lead_in_mm
    lower_straight_width = width_mm - 2.0 * lower_radius
    upper_straight_width = width_mm - 2.0 * upper_radius
    if upper_straight_width <= 0.0:
        raise ValueError("The grab bay is too narrow for its rounded ends and lead-in.")

    bay_bottom_z = bottom_z + handle_lift_mm
    bay_height = top_z - bay_bottom_z
    lower_left_center_x = -lower_straight_width / 2.0
    lower_right_center_x = lower_straight_width / 2.0
    grab_bay = (
        cq.Workplane("XY", origin=(0.0, center_y, bay_bottom_z))
        .rect(lower_straight_width, length_mm)
        .extrude(bay_height)
        .union(
            cq.Workplane("XY", origin=(lower_left_center_x, center_y, bay_bottom_z))
            .circle(lower_radius)
            .extrude(bay_height)
        )
        .union(
            cq.Workplane("XY", origin=(lower_right_center_x, center_y, bay_bottom_z))
            .circle(lower_radius)
            .extrude(bay_height)
        )
    )

    lead_start_z = top_z - BOOLEAN_OVERLAP_MM - lead_in_depth_mm
    lead_height = top_z - lead_start_z
    upper_left_center_x = -upper_straight_width / 2.0
    upper_right_center_x = upper_straight_width / 2.0
    rectangle_lead_in = (
        cq.Workplane("XY", origin=(0.0, center_y, lead_start_z))
        .rect(lower_straight_width, length_mm)
        .workplane(offset=lead_height)
        .rect(upper_straight_width, length_mm + 2.0 * lead_in_mm)
        .loft(combine=True)
    )
    left_end_lead_in = (
        cq.Workplane("XY", origin=(lower_left_center_x, center_y, lead_start_z))
        .circle(lower_radius)
        .workplane(offset=lead_height)
        .center(upper_left_center_x - lower_left_center_x, 0.0)
        .circle(upper_radius)
        .loft(combine=True)
    )
    right_end_lead_in = (
        cq.Workplane("XY", origin=(lower_right_center_x, center_y, lead_start_z))
        .circle(lower_radius)
        .workplane(offset=lead_height)
        .center(upper_right_center_x - lower_right_center_x, 0.0)
        .circle(upper_radius)
        .loft(combine=True)
    )
    return (
        grab_bay.union(rectangle_lead_in).union(left_end_lead_in).union(right_end_lead_in).clean()
    )


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
        "steak_knife_unit_width",
        "steak_knife_count",
    )
    for name in integer_names:
        value = parameters[name]
        if isinstance(value, bool) or not isinstance(value, int) or value < 1:
            raise ValueError(f"{name} must be a positive integer.")

    nonnegative_names = (
        "fit_clearance_mm",
        "vertical_clearance_mm",
        "knife_slot_clearance_mm",
        "knife_handle_lift_angle_degrees",
    )
    for name, value in parameters.items():
        if (
            name in integer_names
            or name in nonnegative_names
            or name == "utensil_grab_bay_center_y_mm"
        ):
            continue
        if value <= 0:
            raise ValueError(f"{name} must be greater than zero.")
    for name in nonnegative_names:
        if parameters[name] < 0:
            raise ValueError(f"{name} must not be negative.")
    if parameters["knife_handle_lift_angle_degrees"] >= 90.0:
        raise ValueError("knife_handle_lift_angle_degrees must be less than 90 degrees.")

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

    steak_knife_length_mm = parameters["steak_knife_length_mm"]
    steak_component_length = (
        parameters["steak_knife_handle_length_mm"] + parameters["steak_knife_blade_length_mm"]
    )
    if abs(steak_component_length - steak_knife_length_mm) > 1e-6:
        raise ValueError(
            "steak knife handle and blade lengths must add up to steak_knife_length_mm."
        )

    steak_handle_widths = (
        parameters["steak_knife_handle_bottom_width_mm"],
        parameters["steak_knife_handle_top_width_mm"],
        parameters["steak_knife_handle_main_width_mm"],
        parameters["steak_knife_handle_narrow_width_mm"],
    )
    if any(
        wider <= narrower
        for wider, narrower in zip(steak_handle_widths, steak_handle_widths[1:], strict=False)
    ):
        raise ValueError(
            "steak knife handle widths must descend from bottom to top, main, and narrow widths."
        )
    if (
        parameters["steak_knife_handle_thickness_mm"]
        <= parameters["steak_knife_handle_neck_thickness_mm"]
    ):
        raise ValueError(
            "steak_knife_handle_thickness_mm must exceed steak_knife_handle_neck_thickness_mm."
        )
    if (
        parameters["steak_knife_handle_thickness_mm"]
        <= parameters["steak_knife_handle_tip_thickness_mm"]
    ):
        raise ValueError(
            "steak_knife_handle_thickness_mm must exceed steak_knife_handle_tip_thickness_mm."
        )

    handle_cap_length_mm = parameters["steak_knife_handle_cap_length_mm"]
    handle_cap_peak_offset_mm = parameters["steak_knife_handle_cap_peak_offset_mm"]
    handle_neck_length_mm = parameters["steak_knife_handle_neck_length_mm"]
    handle_length_mm = parameters["steak_knife_handle_length_mm"]
    if handle_cap_peak_offset_mm >= handle_cap_length_mm:
        raise ValueError(
            "steak_knife_handle_cap_peak_offset_mm must be less than "
            "steak_knife_handle_cap_length_mm."
        )
    if handle_cap_length_mm + handle_neck_length_mm >= handle_length_mm:
        raise ValueError("The steak knife neck and cap must fit inside the handle length.")

    edge_bulb_length_mm = parameters["steak_knife_handle_edge_bulb_length_mm"]
    edge_bulb_peak_offset_mm = parameters["steak_knife_handle_edge_bulb_peak_offset_mm"]
    if edge_bulb_peak_offset_mm >= edge_bulb_length_mm:
        raise ValueError(
            "steak_knife_handle_edge_bulb_peak_offset_mm must be less than "
            "steak_knife_handle_edge_bulb_length_mm."
        )
    if edge_bulb_length_mm >= handle_length_mm:
        raise ValueError("The steak knife edge bulb must fit inside the handle length.")

    edge_bulb_flat_length_mm = parameters["steak_knife_handle_edge_bulb_flat_length_mm"]
    edge_bulb_half_flat_mm = edge_bulb_flat_length_mm / 2.0
    if edge_bulb_half_flat_mm >= min(
        edge_bulb_peak_offset_mm,
        edge_bulb_length_mm - edge_bulb_peak_offset_mm,
    ):
        raise ValueError("The steak knife edge bulb flat must fit inside the bulb length.")
