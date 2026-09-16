"""Peg-lock clip for the OXO Classic Swipe scoop trigger."""

from __future__ import annotations

import math

NAME = "oxo_ice_cream_scoop_trigger_keeper"
DESCRIPTION = (
    "PETG peg-lock clip for holding the OXO Classic Swipe ice-cream scoop trigger closed "
    "through an existing gear slot."
)
PARAMETERS = {
    "handle_span_mm": 34.0,
    "peg_drop_mm": 13.0,
    "trigger_leg_drop_mm": 17.0,
    "body_thickness_mm": 4.2,
    "body_width_mm": 3.62,
    "peg_length_mm": 5.0,
    "peg_major_mm": 4.2,
    "peg_minor_mm": 2.2,
    "peg_angle_degrees": 45.0,
    "trigger_lip_mm": 2.0,
}
PRINT_NOTES = (
    "Sized from the best-fitting former small prototype for OXO model 11295100. Squeeze and "
    "hold the trigger, insert the capsule peg through a 4.6 x 2.6 mm gear slot, wrap the "
    "bridge behind the handle, and seat the 17 mm leg over the trigger. Print in PETG "
    "broadside down in the exported orientation. The 5 mm peg is a horizontal cantilever; use "
    "0.12-0.16 mm layers and add build-plate support beneath only the peg if its underside "
    "sags. The peg is 4.2 x 2.2 mm with 0.2 mm nominal clearance per side and projects "
    "straight from the flat terminal face in the same direction as the bracket leg. Its "
    "footprint is rotated 45 degrees. Adjust peg_angle_degrees if the chosen gear slot is not "
    "aligned with that axis. Do not force the peg or strongly load the scoop mechanism."
)

DEFAULT_HANDLE_SPAN_MM = 34.0
DEFAULT_PEG_DROP_MM = 13.0
DEFAULT_TRIGGER_LEG_DROP_MM = 17.0
DEFAULT_BODY_THICKNESS_MM = 4.2
DEFAULT_BODY_WIDTH_MM = 3.62
DEFAULT_PEG_LENGTH_MM = 5.0
DEFAULT_PEG_MAJOR_MM = 4.2
DEFAULT_PEG_MINOR_MM = 2.2
DEFAULT_PEG_ANGLE_DEGREES = 45.0
DEFAULT_TRIGGER_LIP_MM = 2.0
MINIMUM_BODY_THICKNESS_MM = 1.2
MINIMUM_BODY_WIDTH_MM = 2.0
PEG_JOIN_OVERLAP_MM = 0.05
TRIGGER_LIP_RAMP_MM = 2.5


def build(
    handle_span_mm: float = DEFAULT_HANDLE_SPAN_MM,
    peg_drop_mm: float = DEFAULT_PEG_DROP_MM,
    trigger_leg_drop_mm: float = DEFAULT_TRIGGER_LEG_DROP_MM,
    body_thickness_mm: float = DEFAULT_BODY_THICKNESS_MM,
    body_width_mm: float = DEFAULT_BODY_WIDTH_MM,
    peg_length_mm: float = DEFAULT_PEG_LENGTH_MM,
    peg_major_mm: float = DEFAULT_PEG_MAJOR_MM,
    peg_minor_mm: float = DEFAULT_PEG_MINOR_MM,
    peg_angle_degrees: float = DEFAULT_PEG_ANGLE_DEGREES,
    trigger_lip_mm: float = DEFAULT_TRIGGER_LIP_MM,
):
    """Build the single fitted peg-lock clip."""
    import cadquery as cq

    _validate_parameters(
        handle_span_mm=handle_span_mm,
        peg_drop_mm=peg_drop_mm,
        trigger_leg_drop_mm=trigger_leg_drop_mm,
        body_thickness_mm=body_thickness_mm,
        body_width_mm=body_width_mm,
        peg_length_mm=peg_length_mm,
        peg_major_mm=peg_major_mm,
        peg_minor_mm=peg_minor_mm,
        peg_angle_degrees=peg_angle_degrees,
        trigger_lip_mm=trigger_lip_mm,
    )

    bridge = (
        cq.Workplane("XY")
        .box(
            handle_span_mm + 2.0 * body_thickness_mm,
            body_thickness_mm,
            body_width_mm,
        )
        .translate((handle_span_mm / 2.0, body_thickness_mm / 2.0, body_width_mm / 2.0))
    )
    peg_leg = (
        cq.Workplane("XY")
        .box(body_thickness_mm, peg_drop_mm, body_width_mm)
        .translate(
            (
                -body_thickness_mm / 2.0,
                -peg_drop_mm / 2.0,
                body_width_mm / 2.0,
            )
        )
    )
    trigger_leg = (
        cq.Workplane("XY")
        .box(body_thickness_mm, trigger_leg_drop_mm, body_width_mm)
        .translate(
            (
                handle_span_mm + body_thickness_mm / 2.0,
                -trigger_leg_drop_mm / 2.0,
                body_width_mm / 2.0,
            )
        )
    )
    trigger_lip = (
        cq.Workplane("XY")
        .moveTo(handle_span_mm, -trigger_leg_drop_mm)
        .lineTo(handle_span_mm - trigger_lip_mm, -trigger_leg_drop_mm)
        .lineTo(handle_span_mm, -trigger_leg_drop_mm + TRIGGER_LIP_RAMP_MM)
        .close()
        .extrude(body_width_mm)
    )
    peg = (
        cq.Workplane(
            "XZ",
            origin=(
                -body_thickness_mm / 2.0,
                -peg_drop_mm + PEG_JOIN_OVERLAP_MM,
                body_width_mm / 2.0,
            ),
        )
        .slot2D(peg_major_mm, peg_minor_mm, angle=peg_angle_degrees)
        .extrude(peg_length_mm + PEG_JOIN_OVERLAP_MM)
    )

    # Keep the terminal faces square so the peg base and enlarged trigger lip meet their legs
    # without notches at either junction.
    frame = bridge.union(peg_leg).union(trigger_leg).clean()
    assembly = frame.union(trigger_lip).union(peg).clean()

    # Lay the broad face on the bed for layer continuity through both legs and the bridge.
    return assembly.translate((0.0, 0.0, -assembly.val().BoundingBox().zmin)).clean()


def _capsule_projected_size(
    *, major_mm: float, minor_mm: float, angle_degrees: float
) -> tuple[float, float]:
    """Return the axis-aligned width and height of a rotated capsule."""
    centerline_mm = major_mm - minor_mm
    angle_radians = math.radians(angle_degrees)
    return (
        minor_mm + centerline_mm * abs(math.cos(angle_radians)),
        minor_mm + centerline_mm * abs(math.sin(angle_radians)),
    )


def _validate_parameters(
    *,
    handle_span_mm: float,
    peg_drop_mm: float,
    trigger_leg_drop_mm: float,
    body_thickness_mm: float,
    body_width_mm: float,
    peg_length_mm: float,
    peg_major_mm: float,
    peg_minor_mm: float,
    peg_angle_degrees: float,
    trigger_lip_mm: float,
) -> None:
    parameters = {
        "handle_span_mm": handle_span_mm,
        "peg_drop_mm": peg_drop_mm,
        "trigger_leg_drop_mm": trigger_leg_drop_mm,
        "body_thickness_mm": body_thickness_mm,
        "body_width_mm": body_width_mm,
        "peg_length_mm": peg_length_mm,
        "peg_major_mm": peg_major_mm,
        "peg_minor_mm": peg_minor_mm,
        "peg_angle_degrees": peg_angle_degrees,
        "trigger_lip_mm": trigger_lip_mm,
    }
    for name, value in parameters.items():
        if not math.isfinite(value):
            raise ValueError(f"{name} must be finite")

    if handle_span_mm <= 0.0:
        raise ValueError("handle_span_mm must be positive")
    projected_peg_width_mm, projected_peg_depth_mm = _capsule_projected_size(
        major_mm=peg_major_mm,
        minor_mm=peg_minor_mm,
        angle_degrees=peg_angle_degrees,
    )
    if peg_drop_mm <= 0.0:
        raise ValueError("peg_drop_mm must be positive")
    if trigger_leg_drop_mm <= TRIGGER_LIP_RAMP_MM:
        raise ValueError("trigger_leg_drop_mm is too short for the retaining lip")
    if body_thickness_mm < MINIMUM_BODY_THICKNESS_MM:
        raise ValueError(f"body_thickness_mm must be at least {MINIMUM_BODY_THICKNESS_MM}")
    if body_thickness_mm < projected_peg_width_mm:
        raise ValueError("body_thickness_mm must support the full rotated peg width")
    if body_width_mm < MINIMUM_BODY_WIDTH_MM:
        raise ValueError(f"body_width_mm must be at least {MINIMUM_BODY_WIDTH_MM}")
    if body_width_mm < projected_peg_depth_mm:
        raise ValueError("body_width_mm must support the full rotated peg depth")
    if peg_length_mm <= 0.0:
        raise ValueError("peg_length_mm must be positive")
    if peg_minor_mm <= 0.0 or peg_major_mm <= peg_minor_mm:
        raise ValueError("peg_major_mm must be greater than a positive peg_minor_mm")
    if trigger_lip_mm <= 0.0 or trigger_lip_mm >= body_thickness_mm:
        raise ValueError("trigger_lip_mm must be positive and smaller than body_thickness_mm")
