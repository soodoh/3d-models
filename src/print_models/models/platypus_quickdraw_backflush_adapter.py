"""Bottle-coupled backflush adapter for the Platypus QuickDraw clean outlet."""

from __future__ import annotations

import math
from collections.abc import Mapping

from print_models.helical_thread import twisted_thread

NAME = "platypus_quickdraw_backflush_adapter"
DESCRIPTION = "Threaded QuickDraw clean-side adapter for backflushing from a standard 28 mm bottle."
PARAMETERS = {
    "body_outer_diameter_mm": 38.0,
    "body_height_mm": 26.0,
    "flow_bore_diameter_mm": 10.0,
    "bottle_thread_minor_diameter_mm": 25.5,
    "bottle_thread_major_diameter_mm": 27.6,
    "bottle_thread_pitch_mm": 3.2,
    "bottle_thread_length_mm": 12.0,
    "bottle_fit_adjustment_mm": 0.0,
    "filter_thread_minor_diameter_mm": 31.7,
    "filter_thread_major_diameter_mm": 33.4,
    "filter_thread_pitch_mm": 1.5,
    "filter_thread_length_mm": 6.5,
    "filter_lead_in_mm": 5.5,
    "filter_fit_adjustment_mm": 0.0,
    "gasket_outer_diameter_mm": 24.8,
    "gasket_inner_diameter_mm": 10.2,
    "gasket_thickness_mm": 1.0,
}
PRINT_NOTES = (
    "Print the adapter upright with the 28 mm bottle opening on the bed, using PETG and "
    "fine 0.12-0.16 mm layers. Print the bottle_gasket separately in flexible TPU/TPE at "
    "100% infill and press it against the shoulder at the back of the bottle-thread socket. "
    "Remove the QuickDraw ConnectCap, screw this adapter onto the exposed CLEAN outlet, then "
    "screw in a dedicated clean 28 mm bottle. Squeeze clean water toward the DIRTY outlet. "
    "The interfaces are nominal; positive fit adjustments loosen them and negative values "
    "tighten them. Tune in 0.2 mm steps if needed. "
    "Leak-test before use, keep the adapter clean, and follow Platypus cleaning guidance. "
    "Geometry was independently parameterized using dimensions observed from Ben Friesen's "
    "CC BY-NC-SA QuickDraw accessories model 391570 on Printables; retain that attribution "
    "and license for redistributed derivatives."
)

BOTTLE_THREAD_CREST_HALF_DEGREES = 65.0
FILTER_THREAD_CREST_HALF_DEGREES = 8.0
THREAD_PROFILE_SAMPLES = 24
THREAD_SECTION_DEGREES = 30.0
MINIMUM_WALL_THICKNESS_MM = 1.5
MINIMUM_SHOULDER_THICKNESS_MM = 1.0
OUTER_EDGE_CHAMFER_MM = 0.8
FILTER_ENTRY_CHAMFER_MM = 0.8
BOTTLE_ENTRY_CHAMFER_MM = 0.8


def build(
    body_outer_diameter_mm: float = 38.0,
    body_height_mm: float = 26.0,
    flow_bore_diameter_mm: float = 10.0,
    bottle_thread_minor_diameter_mm: float = 25.5,
    bottle_thread_major_diameter_mm: float = 27.6,
    bottle_thread_pitch_mm: float = 3.2,
    bottle_thread_length_mm: float = 12.0,
    bottle_fit_adjustment_mm: float = 0.0,
    filter_thread_minor_diameter_mm: float = 31.7,
    filter_thread_major_diameter_mm: float = 33.4,
    filter_thread_pitch_mm: float = 1.5,
    filter_thread_length_mm: float = 6.5,
    filter_lead_in_mm: float = 5.5,
    filter_fit_adjustment_mm: float = 0.0,
    gasket_outer_diameter_mm: float = 24.8,
    gasket_inner_diameter_mm: float = 10.2,
    gasket_thickness_mm: float = 1.0,
) -> Mapping[str, object]:
    """Build the rigid adapter body and its printable bottle-neck gasket."""
    import cadquery as cq

    bottle_minor_diameter_mm = bottle_thread_minor_diameter_mm + bottle_fit_adjustment_mm
    bottle_major_diameter_mm = bottle_thread_major_diameter_mm + bottle_fit_adjustment_mm
    filter_minor_diameter_mm = filter_thread_minor_diameter_mm + filter_fit_adjustment_mm
    filter_major_diameter_mm = filter_thread_major_diameter_mm + filter_fit_adjustment_mm
    filter_thread_start_mm = body_height_mm - filter_lead_in_mm - filter_thread_length_mm

    _validate_dimensions(
        body_outer_diameter_mm=body_outer_diameter_mm,
        body_height_mm=body_height_mm,
        flow_bore_diameter_mm=flow_bore_diameter_mm,
        bottle_minor_diameter_mm=bottle_minor_diameter_mm,
        bottle_major_diameter_mm=bottle_major_diameter_mm,
        bottle_thread_pitch_mm=bottle_thread_pitch_mm,
        bottle_thread_length_mm=bottle_thread_length_mm,
        filter_minor_diameter_mm=filter_minor_diameter_mm,
        filter_major_diameter_mm=filter_major_diameter_mm,
        filter_thread_pitch_mm=filter_thread_pitch_mm,
        filter_thread_length_mm=filter_thread_length_mm,
        filter_lead_in_mm=filter_lead_in_mm,
        filter_thread_start_mm=filter_thread_start_mm,
        gasket_outer_diameter_mm=gasket_outer_diameter_mm,
        gasket_inner_diameter_mm=gasket_inner_diameter_mm,
        gasket_thickness_mm=gasket_thickness_mm,
    )

    body = (
        cq.Workplane("XY")
        .circle(body_outer_diameter_mm / 2.0)
        .extrude(body_height_mm)
        .edges("%Circle")
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
    body = body.cut(bottle_thread_cutter.union(bottle_entry))

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
    body = body.cut(filter_thread_cutter.union(filter_lead_in).union(filter_entry))

    flow_bore = cq.Workplane("XY").circle(flow_bore_diameter_mm / 2.0).extrude(body_height_mm)
    body = body.cut(flow_bore).clean()

    gasket = (
        cq.Workplane("XY")
        .circle(gasket_outer_diameter_mm / 2.0)
        .circle(gasket_inner_diameter_mm / 2.0)
        .extrude(gasket_thickness_mm)
    )

    return {"body": body, "bottle_gasket": gasket}


def _validate_dimensions(
    *,
    body_outer_diameter_mm: float,
    body_height_mm: float,
    flow_bore_diameter_mm: float,
    bottle_minor_diameter_mm: float,
    bottle_major_diameter_mm: float,
    bottle_thread_pitch_mm: float,
    bottle_thread_length_mm: float,
    filter_minor_diameter_mm: float,
    filter_major_diameter_mm: float,
    filter_thread_pitch_mm: float,
    filter_thread_length_mm: float,
    filter_lead_in_mm: float,
    filter_thread_start_mm: float,
    gasket_outer_diameter_mm: float,
    gasket_inner_diameter_mm: float,
    gasket_thickness_mm: float,
) -> None:
    dimensions = {
        "body_outer_diameter_mm": body_outer_diameter_mm,
        "body_height_mm": body_height_mm,
        "flow_bore_diameter_mm": flow_bore_diameter_mm,
        "bottle thread minor diameter": bottle_minor_diameter_mm,
        "bottle thread major diameter": bottle_major_diameter_mm,
        "bottle_thread_pitch_mm": bottle_thread_pitch_mm,
        "bottle_thread_length_mm": bottle_thread_length_mm,
        "filter thread minor diameter": filter_minor_diameter_mm,
        "filter thread major diameter": filter_major_diameter_mm,
        "filter_thread_pitch_mm": filter_thread_pitch_mm,
        "filter_thread_length_mm": filter_thread_length_mm,
        "filter_lead_in_mm": filter_lead_in_mm,
        "gasket_outer_diameter_mm": gasket_outer_diameter_mm,
        "gasket_inner_diameter_mm": gasket_inner_diameter_mm,
        "gasket_thickness_mm": gasket_thickness_mm,
    }
    for name, value in dimensions.items():
        _validate_positive(name, value)

    if bottle_major_diameter_mm <= bottle_minor_diameter_mm:
        raise ValueError("Bottle thread major diameter must exceed its minor diameter.")
    if filter_major_diameter_mm <= filter_minor_diameter_mm:
        raise ValueError("Filter thread major diameter must exceed its minor diameter.")
    if flow_bore_diameter_mm >= bottle_minor_diameter_mm:
        raise ValueError("flow_bore_diameter_mm must fit inside the bottle thread.")
    if body_outer_diameter_mm - filter_major_diameter_mm < 2 * MINIMUM_WALL_THICKNESS_MM:
        raise ValueError("The filter thread must leave at least a 1.5 mm body wall.")
    if filter_thread_start_mm - bottle_thread_length_mm < MINIMUM_SHOULDER_THICKNESS_MM:
        raise ValueError("The two sockets must leave at least a 1 mm sealing shoulder.")
    if gasket_outer_diameter_mm >= bottle_minor_diameter_mm:
        raise ValueError("gasket_outer_diameter_mm must fit through the bottle-thread opening.")
    if gasket_inner_diameter_mm < flow_bore_diameter_mm:
        raise ValueError("gasket_inner_diameter_mm must not restrict the flow bore.")
    if gasket_inner_diameter_mm >= gasket_outer_diameter_mm:
        raise ValueError("gasket_inner_diameter_mm must be smaller than its outer diameter.")


def _validate_positive(name: str, value: float) -> None:
    if not math.isfinite(value) or value <= 0:
        raise ValueError(f"{name} must be finite and positive.")
