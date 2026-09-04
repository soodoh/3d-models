"""Solid split fit gauge for the measured OXO Classic Swipe scoop cradle."""

from __future__ import annotations

from print_models.models.gridfinity_oxo_ice_cream_scoop import (
    PARAMETERS as HOLDER_PARAMETERS,
)
from print_models.models.gridfinity_oxo_ice_cream_scoop import (
    _build_scoop_envelope,
    _build_vertical_release_cutter,
    _orient_scoop_envelope,
)

NAME = "gridfinity_oxo_ice_cream_scoop_fit_test"
DESCRIPTION = (
    "Full-object solid fit gauge, split into handle and bowl halves, for validating the measured "
    "OXO Classic Swipe scoop before printing the Gridfinity holder."
)
PARAMETERS = {
    "fit_clearance_mm": HOLDER_PARAMETERS["fit_clearance_mm"],
    "roll_angle_degrees": HOLDER_PARAMETERS["roll_angle_degrees"],
    "cavity_bottom_z_mm": 9.0,
    "test_height_mm": 42.0,
    "test_width_mm": 83.5,
    "split_y_mm": 0.0,
}
PRINT_NOTES = (
    "The CAD parts are intentionally solid; slice both with 15% grid infill, three perimeters, "
    "and five top and bottom layers. Print their flat bases on the bed without supports or "
    "scaling. Butt the halves together at the center seam and secure the undersides with tape if "
    "needed. Insert the scoop metal-lever side upward at the modeled 47 degree roll. It should "
    "seat with light hand pressure and lift vertically without catching. The test uses the same "
    "1 mm fitted clearance and vertical-release cutter as the full holder."
)

SPLIT_BOX_MARGIN_MM = 1.0


def _measured_fitted_cutter(
    *, fit_clearance_mm: float, roll_angle_degrees: float, cavity_bottom_z_mm: float
):
    measured_keys = (
        "overall_length_mm",
        "guard_face_from_handle_tip_mm",
        "bowl_near_edge_from_handle_tip_mm",
        "handle_width_mm",
        "handle_depth_mm",
        "guard_width_mm",
        "guard_depth_mm",
        "guard_upper_reach_mm",
        "bowl_diameter_mm",
        "bowl_depth_mm",
        "mechanism_span_mm",
        "mechanism_depth_mm",
    )
    scoop = _build_scoop_envelope(
        **{parameter: HOLDER_PARAMETERS[parameter] for parameter in measured_keys},
        clearance_mm=fit_clearance_mm,
    )
    return _orient_scoop_envelope(
        scoop=scoop,
        roll_angle_degrees=roll_angle_degrees,
        cavity_bottom_z=cavity_bottom_z_mm,
    )


def _split_test_body(
    body,
    *,
    test_width_mm: float,
    test_length_mm: float,
    test_height_mm: float,
    split_y_mm: float,
):
    import cadquery as cq

    test_min_y = -test_length_mm / 2.0
    test_max_y = test_length_mm / 2.0
    if not test_min_y < split_y_mm < test_max_y:
        raise ValueError("split_y_mm must lie inside the test length.")

    margin_mm = SPLIT_BOX_MARGIN_MM
    box_width_mm = test_width_mm + 2.0 * margin_mm
    box_height_mm = test_height_mm + 2.0 * margin_mm
    handle_box = cq.Solid.makeBox(
        box_width_mm,
        split_y_mm - test_min_y + margin_mm,
        box_height_mm,
        cq.Vector(-test_width_mm / 2.0 - margin_mm, test_min_y - margin_mm, -margin_mm),
    )
    bowl_box = cq.Solid.makeBox(
        box_width_mm,
        test_max_y - split_y_mm + margin_mm,
        box_height_mm,
        cq.Vector(-test_width_mm / 2.0 - margin_mm, split_y_mm, -margin_mm),
    )
    return {
        "solid_handle_half": cq.Workplane(obj=body.val().intersect(handle_box)),
        "solid_bowl_half": cq.Workplane(obj=body.val().intersect(bowl_box)),
    }


def build(
    fit_clearance_mm: float = 1.0,
    roll_angle_degrees: float = 47.0,
    cavity_bottom_z_mm: float = 9.0,
    test_height_mm: float = 42.0,
    test_width_mm: float = 83.5,
    split_y_mm: float = 0.0,
):
    """Build the solid measured-scoop test body and split it at the holder center seam."""
    import cadquery as cq

    if test_height_mm <= 0.0 or test_width_mm <= 0.0:
        raise ValueError("Fit-test dimensions must be positive.")
    if fit_clearance_mm < 0.0:
        raise ValueError("fit_clearance_mm cannot be negative.")
    if cavity_bottom_z_mm <= 0.0:
        raise ValueError("cavity_bottom_z_mm must be positive.")
    if test_height_mm <= cavity_bottom_z_mm:
        raise ValueError("The test body must extend above the cavity bottom.")

    fitted_cutter = _measured_fitted_cutter(
        fit_clearance_mm=fit_clearance_mm,
        roll_angle_degrees=roll_angle_degrees,
        cavity_bottom_z_mm=cavity_bottom_z_mm,
    )
    release_cutter = _build_vertical_release_cutter(
        fitted_cutter=fitted_cutter,
        deck_top_z=test_height_mm,
    )
    test_length_mm = HOLDER_PARAMETERS["overall_length_mm"] + 2.0 * fit_clearance_mm
    body = (
        cq.Workplane("XY")
        .box(test_width_mm, test_length_mm, test_height_mm, centered=(True, True, False))
        .cut(release_cutter)
        .clean()
    )
    return _split_test_body(
        body,
        test_width_mm=test_width_mm,
        test_length_mm=test_length_mm,
        test_height_mm=test_height_mm,
        split_y_mm=split_y_mm,
    )
