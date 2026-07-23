"""Shared CadQuery primitives for sliding dovetail panels."""

from __future__ import annotations


def trapezoidal_panel(
    cq,
    *,
    length: float,
    bottom_width: float,
    height: float,
    side_inset: float,
    extrusion_axis: str,
    front_inset: float = 0.0,
):
    """Build a panel whose top narrows at the sides and optionally at the front."""
    top_width = bottom_width - side_inset * 2.0
    top_length = length - front_inset
    if length <= 0 or bottom_width <= 0 or height <= 0:
        raise ValueError("Dovetail panel dimensions must be positive.")
    if side_inset < 0 or top_width <= 0:
        raise ValueError("Dovetail panel side inset leaves no printable top width.")
    if front_inset < 0 or top_length <= 0:
        raise ValueError("Dovetail panel front inset leaves no printable top length.")
    if extrusion_axis not in {"x", "y"}:
        raise ValueError("extrusion_axis must be 'x' or 'y'.")

    # Preserve the original prism path exactly for existing callers.
    if front_inset == 0:
        profile = [
            (-bottom_width / 2.0, 0.0),
            (bottom_width / 2.0, 0.0),
            (top_width / 2.0, height),
            (-top_width / 2.0, height),
        ]
        workplane = cq.Workplane("YZ" if extrusion_axis == "x" else "XZ")
        return workplane.polyline(profile).close().extrude(length / 2.0, both=True)

    if extrusion_axis == "x":
        return (
            cq.Workplane("XY")
            .rect(length, bottom_width)
            .workplane(offset=height)
            .center(front_inset / 2.0, 0.0)
            .rect(top_length, top_width)
            .loft(combine=True)
        )
    return (
        cq.Workplane("XY")
        .rect(bottom_width, length)
        .workplane(offset=height)
        .center(0.0, front_inset / 2.0)
        .rect(top_width, top_length)
        .loft(combine=True)
    )
