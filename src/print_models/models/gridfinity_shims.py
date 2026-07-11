"""Parametric thin shims for snugging Gridfinity baseplates or bins in drawers."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence

NAME = "gridfinity_shims"
DESCRIPTION = "Simple rectangular Gridfinity drawer/baseplate shims in one or more widths."
PARAMETERS = {
    "length_mm": 84.0,
    "widths_mm": "1,1.5,2",
    "height_mm": 5.0,
    "chamfer_mm": 0.0,
}
PRINT_NOTES = (
    "widths_mm is a comma-separated list, so one export can produce a shim pack. "
    "Defaults match the earlier 84 mm long, 5 mm tall shims in 1, 1.5, and 2 mm widths."
)


def build(
    length_mm: float = 84.0,
    widths_mm: str | Sequence[float] = "1,1.5,2",
    height_mm: float = 5.0,
    chamfer_mm: float = 0.0,
) -> Mapping[str, object]:
    """Build one shim per requested width."""
    _validate_positive("length_mm", length_mm)
    _validate_positive("height_mm", height_mm)
    _validate_non_negative("chamfer_mm", chamfer_mm)

    widths = _parse_widths(widths_mm)
    results = {}
    for width_mm in widths:
        _validate_positive("widths_mm", width_mm)
        if chamfer_mm >= min(width_mm, height_mm) / 2.0:
            raise ValueError(
                f"chamfer_mm must be less than half the smaller shim dimension for "
                f"width {width_mm:g} mm."
            )

        shim = _build_shim(
            length_mm=length_mm,
            width_mm=width_mm,
            height_mm=height_mm,
            chamfer_mm=chamfer_mm,
        )
        name = (
            f"{_format_dimension(length_mm)}x"
            f"{_format_dimension(width_mm)}x"
            f"{_format_dimension(height_mm)}mm"
        )
        results[name] = shim

    return results


def _build_shim(
    *,
    length_mm: float,
    width_mm: float,
    height_mm: float,
    chamfer_mm: float,
):
    import cadquery as cq

    shim = cq.Workplane("XY").rect(length_mm, width_mm).extrude(height_mm)
    if chamfer_mm > 0:
        shim = shim.edges("|Z").chamfer(chamfer_mm)
    return shim


def _parse_widths(raw_widths: str | Sequence[float]) -> tuple[float, ...]:
    if isinstance(raw_widths, str):
        stripped_widths = raw_widths.strip()
        if not stripped_widths:
            raise ValueError("widths_mm must include at least one width.")

        widths = []
        for raw_width in stripped_widths.split(","):
            stripped_width = raw_width.strip()
            if not stripped_width:
                raise ValueError("widths_mm contains an empty width.")
            widths.append(float(stripped_width))
        return tuple(widths)

    if isinstance(raw_widths, Iterable):
        widths = tuple(float(width) for width in raw_widths)
        if not widths:
            raise ValueError("widths_mm must include at least one width.")
        return widths

    raise ValueError("widths_mm must be a comma-separated string or a sequence.")


def _format_dimension(value: float) -> str:
    return f"{value:g}".replace(".", "p")


def _validate_positive(name: str, value: float) -> None:
    if value <= 0:
        raise ValueError(f"{name} must be positive.")


def _validate_non_negative(name: str, value: float) -> None:
    if value < 0:
        raise ValueError(f"{name} cannot be negative.")
