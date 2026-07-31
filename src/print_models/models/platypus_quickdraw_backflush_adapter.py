"""Bottle-coupled backflush adapter for the Platypus QuickDraw clean outlet."""

from __future__ import annotations

import math

from print_models.helical_thread import twisted_thread

NAME = "platypus_quickdraw_backflush_adapter"
DESCRIPTION = "Standard 28 mm female bottle socket to female QuickDraw clean-output adapter."
PARAMETERS = {
    "body_outer_diameter_mm": 38.0,
    "body_height_mm": 26.0,
    "bottle_thread_minor_diameter_mm": 25.5,
    "bottle_thread_major_diameter_mm": 27.6,
    "bottle_thread_pitch_mm": 3.2,
    "bottle_thread_length_mm": 12.0,
    "bottle_fit_adjustment_mm": 0.0,
    "filter_thread_minor_diameter_mm": 31.7,
    "filter_thread_major_diameter_mm": 33.4,
    "filter_thread_pitch_mm": 1.5,
    "filter_thread_length_mm": 6.5,
    "filter_fit_adjustment_mm": 0.0,
}
PRINT_NOTES = (
    "Print upright in PETG with the 28 mm bottle opening on the bed and use fine 0.12-0.16 mm "
    "layers. Both ends are female: the 28 mm end accepts a standard clean-water bottle and the "
    "larger end screws over the exposed QuickDraw CLEAN outlet after removing the ConnectCap. "
    "The two sockets join through a full-width, self-supporting 45-degree internal transition; "
    "there is no narrow divider, bridge, or separate gasket part. Positive fit adjustments make "
    "either interface looser; tune in 0.2 mm steps and leak-test before use. Geometry was "
    "independently parameterized using dimensions observed from Ben Friesen's CC BY-NC-SA "
    "QuickDraw accessories model 391570 on Printables; retain that attribution and license for "
    "redistributed derivatives."
)

BOTTLE_THREAD_CREST_HALF_DEGREES = 65.0
FILTER_THREAD_CREST_HALF_DEGREES = 8.0
THREAD_PROFILE_SAMPLES = 24
THREAD_SECTION_DEGREES = 30.0
MINIMUM_WALL_THICKNESS_MM = 1.5
OUTER_EDGE_CHAMFER_MM = 0.8
BOTTLE_ENTRY_CHAMFER_MM = 0.8
FILTER_ENTRY_CHAMFER_MM = 0.8


def build(
    body_outer_diameter_mm: float = 38.0,
    body_height_mm: float = 26.0,
    bottle_thread_minor_diameter_mm: float = 25.5,
    bottle_thread_major_diameter_mm: float = 27.6,
    bottle_thread_pitch_mm: float = 3.2,
    bottle_thread_length_mm: float = 12.0,
    bottle_fit_adjustment_mm: float = 0.0,
    filter_thread_minor_diameter_mm: float = 31.7,
    filter_thread_major_diameter_mm: float = 33.4,
    filter_thread_pitch_mm: float = 1.5,
    filter_thread_length_mm: float = 6.5,
    filter_fit_adjustment_mm: float = 0.0,
):
    """Build the support-free female-to-female backflush adapter."""
    import cadquery as cq

    bottle_minor_diameter_mm = bottle_thread_minor_diameter_mm + bottle_fit_adjustment_mm
    bottle_major_diameter_mm = bottle_thread_major_diameter_mm + bottle_fit_adjustment_mm
    filter_minor_diameter_mm = filter_thread_minor_diameter_mm + filter_fit_adjustment_mm
    filter_major_diameter_mm = filter_thread_major_diameter_mm + filter_fit_adjustment_mm
    transition_height_mm = (filter_minor_diameter_mm - bottle_minor_diameter_mm) / 2.0
    filter_thread_start_mm = bottle_thread_length_mm + transition_height_mm
    filter_lead_in_mm = body_height_mm - filter_thread_start_mm - filter_thread_length_mm

    _validate_dimensions(
        body_outer_diameter_mm=body_outer_diameter_mm,
        body_height_mm=body_height_mm,
        bottle_minor_diameter_mm=bottle_minor_diameter_mm,
        bottle_major_diameter_mm=bottle_major_diameter_mm,
        bottle_thread_pitch_mm=bottle_thread_pitch_mm,
        bottle_thread_length_mm=bottle_thread_length_mm,
        filter_minor_diameter_mm=filter_minor_diameter_mm,
        filter_major_diameter_mm=filter_major_diameter_mm,
        filter_thread_pitch_mm=filter_thread_pitch_mm,
        filter_thread_length_mm=filter_thread_length_mm,
        transition_height_mm=transition_height_mm,
        filter_lead_in_mm=filter_lead_in_mm,
    )

    body = (
        cq.Workplane("XY")
        .circle(body_outer_diameter_mm / 2.0)
        .extrude(body_height_mm)
        .edges("<Z")
        .chamfer(OUTER_EDGE_CHAMFER_MM)
    )

    bottle_thread_cutter = twisted_thread(
        cq,
        pitch_mm=bottle_thread_pitch_mm,
        root_radius_mm=bottle_minor_diameter_mm / 2.0,
        major_radius_mm=bottle_major_diameter_mm / 2.0,
        crest_half_degrees=BOTTLE_THREAD_CREST_HALF_DEGREES,
        height_mm=bottle_thread_length_mm,
        profile_samples=THREAD_PROFILE_SAMPLES,
        section_degrees=THREAD_SECTION_DEGREES,
    )
    bottle_entry = (
        cq.Workplane("XY")
        .circle(bottle_major_diameter_mm / 2.0 + BOTTLE_ENTRY_CHAMFER_MM)
        .workplane(offset=BOTTLE_ENTRY_CHAMFER_MM)
        .circle(bottle_major_diameter_mm / 2.0)
        .loft(combine=True)
    )
    transition = (
        cq.Workplane("XY", origin=(0.0, 0.0, bottle_thread_length_mm))
        .circle(bottle_minor_diameter_mm / 2.0)
        .workplane(offset=transition_height_mm)
        .circle(filter_minor_diameter_mm / 2.0)
        .loft(combine=True)
    )

    filter_thread_cutter = twisted_thread(
        cq,
        pitch_mm=filter_thread_pitch_mm,
        root_radius_mm=filter_minor_diameter_mm / 2.0,
        major_radius_mm=filter_major_diameter_mm / 2.0,
        crest_half_degrees=FILTER_THREAD_CREST_HALF_DEGREES,
        height_mm=filter_thread_length_mm,
        profile_samples=THREAD_PROFILE_SAMPLES,
        section_degrees=THREAD_SECTION_DEGREES,
    ).translate((0.0, 0.0, filter_thread_start_mm))
    filter_lead_in_start_mm = body_height_mm - filter_lead_in_mm
    filter_lead_in = (
        cq.Workplane("XY", origin=(0.0, 0.0, filter_lead_in_start_mm))
        .circle(filter_major_diameter_mm / 2.0)
        .extrude(filter_lead_in_mm - FILTER_ENTRY_CHAMFER_MM)
    )
    filter_entry = (
        cq.Workplane(
            "XY",
            origin=(0.0, 0.0, body_height_mm - FILTER_ENTRY_CHAMFER_MM),
        )
        .circle(filter_major_diameter_mm / 2.0)
        .workplane(offset=FILTER_ENTRY_CHAMFER_MM)
        .circle(filter_major_diameter_mm / 2.0 + FILTER_ENTRY_CHAMFER_MM)
        .loft(combine=True)
    )

    cavity = (
        bottle_thread_cutter.union(bottle_entry)
        .union(transition)
        .union(filter_thread_cutter)
        .union(filter_lead_in)
        .union(filter_entry)
    )
    return body.cut(cavity).clean()


def _validate_dimensions(
    *,
    body_outer_diameter_mm: float,
    body_height_mm: float,
    bottle_minor_diameter_mm: float,
    bottle_major_diameter_mm: float,
    bottle_thread_pitch_mm: float,
    bottle_thread_length_mm: float,
    filter_minor_diameter_mm: float,
    filter_major_diameter_mm: float,
    filter_thread_pitch_mm: float,
    filter_thread_length_mm: float,
    transition_height_mm: float,
    filter_lead_in_mm: float,
) -> None:
    dimensions = {
        "body_outer_diameter_mm": body_outer_diameter_mm,
        "body_height_mm": body_height_mm,
        "bottle thread minor diameter": bottle_minor_diameter_mm,
        "bottle thread major diameter": bottle_major_diameter_mm,
        "bottle_thread_pitch_mm": bottle_thread_pitch_mm,
        "bottle_thread_length_mm": bottle_thread_length_mm,
        "filter thread minor diameter": filter_minor_diameter_mm,
        "filter thread major diameter": filter_major_diameter_mm,
        "filter_thread_pitch_mm": filter_thread_pitch_mm,
        "filter_thread_length_mm": filter_thread_length_mm,
        "transition height": transition_height_mm,
        "filter lead-in length": filter_lead_in_mm,
    }
    for name, value in dimensions.items():
        _validate_positive(name, value)

    if bottle_major_diameter_mm <= bottle_minor_diameter_mm:
        raise ValueError("Bottle thread major diameter must exceed its minor diameter.")
    if filter_major_diameter_mm <= filter_minor_diameter_mm:
        raise ValueError("Filter thread major diameter must exceed its minor diameter.")
    if filter_minor_diameter_mm <= bottle_minor_diameter_mm:
        raise ValueError("Filter thread opening must be larger than the bottle opening.")
    if body_outer_diameter_mm - filter_major_diameter_mm < 2 * MINIMUM_WALL_THICKNESS_MM:
        raise ValueError("The filter thread must leave at least a 1.5 mm body wall.")
    if filter_lead_in_mm <= FILTER_ENTRY_CHAMFER_MM:
        raise ValueError("The sockets and transition must fit within body_height_mm.")


def _validate_positive(name: str, value: float) -> None:
    if not math.isfinite(value) or value <= 0:
        raise ValueError(f"{name} must be finite and positive.")
