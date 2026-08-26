"""Compact fitted Gridfinity storage for four nested small teaspoons."""

from __future__ import annotations

from print_models.models.gridfinity_silverware_set import _build_stacked_utensil_module

NAME = "gridfinity_teaspoon"
DESCRIPTION = (
    "A compact 1x4 Gridfinity box with one photo-traced pocket for four nested small teaspoons "
    "and a wall-to-wall stadium finger bay."
)
PARAMETERS = {
    "unit_width": 1,
    "unit_depth": 4,
    "unit_height": 6,
    "spoon_length_mm": 128.0,
    "spoon_bowl_width_mm": 30.5,
    "spoon_handle_length_mm": 99.0,
    "spoon_handle_end_width_mm": 3.8,
    "spoon_handle_middle_width_mm": 6.2,
    "spoon_handle_neck_width_mm": 4.0,
    "stack_bowl_height_mm": 22.0,
    "stack_neck_height_mm": 14.0,
    "stack_handle_end_height_mm": 29.0,
    "fit_clearance_mm": 1.0,
    "vertical_clearance_mm": 1.0,
    "handle_extension_mm": 4.0,
    "grab_bay_length_mm": 30.0,
    "grab_bay_center_y_mm": -31.0,
    "lead_in_mm": 2.0,
    "lead_in_depth_mm": 8.0,
    "wall_thickness_mm": 1.0,
}
PRINT_NOTES = (
    "Stores one bowl-up natural stack of four identical spoons. Each spoon measures 3.3 mm at "
    "the thin handle sections and 5.5 mm at the thick middle. The fitted silhouette is traced "
    "from the calibrated overhead photo and adds 1 mm clearance per side plus an 8 mm-deep "
    "tapered lead-in. The pocket has a flat 2 mm floor so the uneven stack rests in its measured "
    "natural posture; its 29 mm handle-end height sets the required 6U box height. A 30 mm-long "
    "wall-to-wall stadium bay crosses the lower handle for finger access. Print base-down."
)

# Width samples combine the supplied handle measurements with the calibrated overhead silhouette.
# Fractions run from the handle tip (0.0) to the bowl tip (1.0); widths are physical millimeters.
_HANDLE_WIDTH_SAMPLES = (
    (0.00, "end"),
    (0.05, "end"),
    (0.10, 0.18),
    (0.20, 0.75),
    (0.30, "middle"),
    (0.40, 0.98),
    (0.50, 0.52),
    (0.60, "neck"),
    (0.70, "neck"),
)
_BOWL_WIDTH_SAMPLES = (
    (0.74, 0.21),
    (0.76, 0.31),
    (0.77, 0.36),
    (0.78, 0.45),
    (0.79, 0.56),
    (0.80, 0.66),
    (0.82, 0.81),
    (0.84, 0.91),
    (0.86, 0.97),
    (0.88, 1.00),
    (0.90, 1.00),
    (1.00, 0.00),
)


def _teaspoon_width_profile(
    *,
    spoon_length_mm: float,
    handle_length_mm: float,
    bowl_width_mm: float,
    handle_end_width_mm: float,
    handle_middle_width_mm: float,
    handle_neck_width_mm: float,
) -> tuple[tuple[float, float], ...]:
    """Return the calibrated top-view width profile normalized to the bowl width."""
    handle_span_mm = handle_middle_width_mm - handle_end_width_mm
    handle_widths_mm = []
    for length_fraction, width_spec in _HANDLE_WIDTH_SAMPLES:
        if width_spec == "end":
            width_mm = handle_end_width_mm
        elif width_spec == "middle":
            width_mm = handle_middle_width_mm
        elif width_spec == "neck":
            width_mm = handle_neck_width_mm
        else:
            width_mm = handle_end_width_mm + width_spec * handle_span_mm
        handle_widths_mm.append((length_fraction, width_mm))

    reference_handle_fraction = 99.0 / 128.0
    handle_fraction = handle_length_mm / spoon_length_mm
    bowl_widths = tuple(
        (
            handle_fraction
            + (length_fraction - reference_handle_fraction)
            / (1.0 - reference_handle_fraction)
            * (1.0 - handle_fraction),
            width_ratio,
        )
        for length_fraction, width_ratio in _BOWL_WIDTH_SAMPLES
    )
    return (
        *(
            (length_fraction, width_mm / bowl_width_mm)
            for length_fraction, width_mm in handle_widths_mm
        ),
        *bowl_widths,
    )


def build(
    unit_width: int = 1,
    unit_depth: int = 4,
    unit_height: int = 6,
    spoon_length_mm: float = 128.0,
    spoon_bowl_width_mm: float = 30.5,
    spoon_handle_length_mm: float = 99.0,
    spoon_handle_end_width_mm: float = 3.8,
    spoon_handle_middle_width_mm: float = 6.2,
    spoon_handle_neck_width_mm: float = 4.0,
    stack_bowl_height_mm: float = 22.0,
    stack_neck_height_mm: float = 14.0,
    stack_handle_end_height_mm: float = 29.0,
    fit_clearance_mm: float = 1.0,
    vertical_clearance_mm: float = 1.0,
    handle_extension_mm: float = 4.0,
    grab_bay_length_mm: float = 30.0,
    grab_bay_center_y_mm: float = -31.0,
    lead_in_mm: float = 2.0,
    lead_in_depth_mm: float = 8.0,
    wall_thickness_mm: float = 1.0,
):
    """Build a single fitted Gridfinity box for a natural stack of four teaspoons."""
    parameters = locals()
    _validate_parameters(**parameters)

    width_profile = _teaspoon_width_profile(
        spoon_length_mm=spoon_length_mm,
        handle_length_mm=spoon_handle_length_mm,
        bowl_width_mm=spoon_bowl_width_mm,
        handle_end_width_mm=spoon_handle_end_width_mm,
        handle_middle_width_mm=spoon_handle_middle_width_mm,
        handle_neck_width_mm=spoon_handle_neck_width_mm,
    )
    stack_height_mm = max(
        stack_bowl_height_mm,
        stack_neck_height_mm,
        stack_handle_end_height_mm,
    )

    return _build_stacked_utensil_module(
        unit_width=unit_width,
        unit_depth=unit_depth,
        unit_height=unit_height,
        utensil_specs=((spoon_bowl_width_mm, spoon_length_mm, stack_height_mm, width_profile),),
        fit_clearance_mm=fit_clearance_mm,
        vertical_clearance_mm=vertical_clearance_mm,
        cavity_gap_mm=4.0,
        handle_extension_mm=handle_extension_mm,
        grab_bay_length_mm=grab_bay_length_mm,
        grab_bay_center_y_mm=grab_bay_center_y_mm,
        lead_in_mm=lead_in_mm,
        lead_in_depth_mm=lead_in_depth_mm,
        handle_lift_mm=0.0,
        wall_thickness_mm=wall_thickness_mm,
    )


def _validate_parameters(**parameters) -> None:
    for name in ("unit_width", "unit_depth", "unit_height"):
        value = parameters[name]
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            raise ValueError(f"{name} must be a positive integer.")

    positive_names = (
        "spoon_length_mm",
        "spoon_bowl_width_mm",
        "spoon_handle_length_mm",
        "spoon_handle_end_width_mm",
        "spoon_handle_middle_width_mm",
        "spoon_handle_neck_width_mm",
        "stack_bowl_height_mm",
        "stack_neck_height_mm",
        "stack_handle_end_height_mm",
        "grab_bay_length_mm",
        "lead_in_depth_mm",
        "wall_thickness_mm",
    )
    for name in positive_names:
        if parameters[name] <= 0.0:
            raise ValueError(f"{name} must be positive.")

    for name in ("fit_clearance_mm", "vertical_clearance_mm", "handle_extension_mm", "lead_in_mm"):
        if parameters[name] < 0.0:
            raise ValueError(f"{name} must not be negative.")

    if parameters["spoon_handle_length_mm"] >= parameters["spoon_length_mm"]:
        raise ValueError("spoon_handle_length_mm must be shorter than spoon_length_mm.")
    if parameters["spoon_bowl_width_mm"] <= parameters["spoon_handle_middle_width_mm"]:
        raise ValueError("spoon_bowl_width_mm must exceed the thickest handle width.")
    if parameters["spoon_handle_middle_width_mm"] <= max(
        parameters["spoon_handle_end_width_mm"],
        parameters["spoon_handle_neck_width_mm"],
    ):
        raise ValueError("spoon_handle_middle_width_mm must exceed both thin handle widths.")
    if parameters["grab_bay_center_y_mm"] + parameters["grab_bay_length_mm"] / 2.0 > 0.0:
        raise ValueError("The grab bay must remain in the handle-side half of the box.")
