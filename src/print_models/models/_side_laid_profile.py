"""Shared smooth-profile cutter helpers for side-laid rotational objects."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import cadquery as cq

Point2D = tuple[float, float]


def build_smooth_revolved_cutter(
    *,
    axis_z: float,
    profile_points: tuple[Point2D, ...],
    fit_clearance_mm: float,
) -> cq.Workplane:
    """Revolve a smooth axial-radius profile with radial and end clearance."""
    import cadquery as cq

    cutter_profile_points = tuple(
        (axial_position, radius + fit_clearance_mm) for axial_position, radius in profile_points
    )
    profile_tangents = monotone_profile_tangents(cutter_profile_points)
    profile_parameters = tuple(axial_position for axial_position, _ in cutter_profile_points)
    object_start_x = cutter_profile_points[0][0]
    object_end_x = cutter_profile_points[-1][0]
    cutter_start_x = object_start_x - fit_clearance_mm
    cutter_end_x = object_end_x + fit_clearance_mm
    bottom_radius = cutter_profile_points[0][1]
    top_radius = cutter_profile_points[-1][1]

    profile = (
        cq.Workplane("XZ")
        .moveTo(cutter_start_x, 0.0)
        .lineTo(cutter_start_x, bottom_radius)
        .lineTo(object_start_x, bottom_radius)
        .spline(
            cutter_profile_points[1:],
            tangents=profile_tangents,
            parameters=profile_parameters,
            scale=False,
            includeCurrent=True,
        )
        .lineTo(cutter_end_x, top_radius)
        .lineTo(cutter_end_x, 0.0)
        .close()
    )
    return profile.revolve(360.0, (0.0, 0.0), (1.0, 0.0)).translate((0.0, 0.0, axis_z))


def monotone_profile_tangents(
    profile_points: tuple[Point2D, ...],
) -> tuple[Point2D, ...]:
    """Return spline tangents that preserve profile extrema without introducing seams."""
    axial_spans = tuple(
        end[0] - start[0] for start, end in zip(profile_points, profile_points[1:], strict=False)
    )
    secant_slopes = tuple(
        (end[1] - start[1]) / axial_span
        for start, end, axial_span in zip(
            profile_points, profile_points[1:], axial_spans, strict=False
        )
    )
    tangent_slopes = [0.0] * len(profile_points)

    for point_index in range(1, len(profile_points) - 1):
        previous_slope = secant_slopes[point_index - 1]
        next_slope = secant_slopes[point_index]
        if previous_slope * next_slope <= 0.0:
            continue
        previous_span = axial_spans[point_index - 1]
        next_span = axial_spans[point_index]
        previous_weight = 2.0 * next_span + previous_span
        next_weight = next_span + 2.0 * previous_span
        tangent_slopes[point_index] = (previous_weight + next_weight) / (
            previous_weight / previous_slope + next_weight / next_slope
        )

    final_span = axial_spans[-1]
    previous_span = axial_spans[-2]
    final_secant = secant_slopes[-1]
    previous_secant = secant_slopes[-2]
    final_tangent = (
        (2.0 * final_span + previous_span) * final_secant - final_span * previous_secant
    ) / (final_span + previous_span)
    if final_tangent * final_secant <= 0.0:
        final_tangent = 0.0
    elif previous_secant * final_secant < 0.0 and abs(final_tangent) > abs(3.0 * final_secant):
        final_tangent = 3.0 * final_secant
    tangent_slopes[-1] = final_tangent

    return tuple((1.0, tangent_slope) for tangent_slope in tangent_slopes)
