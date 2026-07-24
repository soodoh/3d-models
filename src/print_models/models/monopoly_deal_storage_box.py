"""Parametric CadQuery recreation of a Monopoly Deal sliding deck box."""

from __future__ import annotations

from collections.abc import Mapping
from importlib.resources import files

from print_models.dovetail import trapezoidal_panel
from print_models.dxf import extrude_dxf_regions, union_dxf_regions

NAME = "monopoly_deal_storage_box"
_MONOPOLY_DEAL_LOGO_REGIONS = (
    (0, (1, 13)),
    (2, ()),
    (3, ()),
    (4, (9,)),
    (5, (10,)),
    (6, (11, 12)),
    (7, ()),
    (8, ()),
    (14, ()),
    (15, ()),
)
DESCRIPTION = "CadQuery rebuild of a Monopoly Deal deck box body and sliding lid."
PARAMETERS = {
    "part": "all",
    "outer_width": 98.362904,
    "outer_depth": 64.0,
    "body_bottom_z": -2.0,
    "body_height": 41.0,
    "wall_thickness": 3.0,
    "bottom_thickness": 2.0,
    "corner_radius": 1.55,
    "body_center_x": -0.103886,
    "body_center_y": -0.356632,
    "lid_width": 95.362904,
    "lid_depth": 61.820216,
    "lid_bottom_z": 35.000004,
    "lid_base_thickness": 4.30,
    "lid_relief_height": 1.23,
    "lid_right_gap": 3.0,
    "lid_edge_chamfer": 0.8,
    "side_groove_depth": 0.65,
    "side_groove_height": 1.25,
    "logo_raise": True,
}
PRINT_NOTES = (
    "The body and lid are modeled in the same assembled coordinate frame as the source STLs. "
    "Use part=container or part=lid to export individual printable parts. "
    "The Monopoly Deal lid logo outline is extracted from Printables model 697154 by GWiz "
    "under CC-BY-NC-SA 4.0."
)

_PART_ALIASES = {
    "all": "all",
    "body": "container",
    "box": "container",
    "base": "container",
    "container": "container",
    "lid": "lid",
}


def build(
    part: str = "all",
    outer_width: float = 98.362904,
    outer_depth: float = 64.0,
    body_bottom_z: float = -2.0,
    body_height: float = 41.0,
    wall_thickness: float = 3.0,
    bottom_thickness: float = 2.0,
    corner_radius: float = 1.55,
    body_center_x: float = -0.103886,
    body_center_y: float = -0.356632,
    lid_width: float = 95.362904,
    lid_depth: float = 61.820216,
    lid_bottom_z: float = 35.000004,
    lid_base_thickness: float = 4.30,
    lid_relief_height: float = 1.23,
    lid_right_gap: float = 3.0,
    lid_edge_chamfer: float = 0.8,
    side_groove_depth: float = 0.65,
    side_groove_height: float = 1.25,
    logo_raise: bool = True,
) -> Mapping[str, object]:
    """Build one or both Monopoly Deal deck box parts."""
    import cadquery as cq

    normalized_part = _normalize_part(part)
    body_top_z = body_bottom_z + body_height
    results: dict[str, object] = {}

    if normalized_part in {"all", "container"}:
        results["container"] = _build_container(
            cq=cq,
            outer_width=outer_width,
            outer_depth=outer_depth,
            body_bottom_z=body_bottom_z,
            body_top_z=body_top_z,
            wall_thickness=wall_thickness,
            bottom_thickness=bottom_thickness,
            corner_radius=corner_radius,
            center_x=body_center_x,
            center_y=body_center_y,
            side_groove_depth=side_groove_depth,
            side_groove_height=side_groove_height,
            lid_thickness=lid_base_thickness,
        )

    if normalized_part in {"all", "lid"}:
        lid_center_x = body_center_x - lid_right_gap / 2.0
        results["lid"] = _build_lid(
            cq=cq,
            width=lid_width,
            depth=lid_depth,
            bottom_z=lid_bottom_z,
            base_thickness=lid_base_thickness,
            relief_height=lid_relief_height,
            edge_chamfer=lid_edge_chamfer,
            center_x=lid_center_x,
            center_y=body_center_y,
            logo_raise=logo_raise,
        )

    return results


def _normalize_part(part: str) -> str:
    normalized = part.strip().lower()

    try:
        return _PART_ALIASES[normalized]
    except KeyError as error:
        choices = ", ".join(sorted(_PART_ALIASES))
        raise ValueError(f"part must be one of: {choices}") from error


def _build_container(
    *,
    cq,
    outer_width: float,
    outer_depth: float,
    body_bottom_z: float,
    body_top_z: float,
    wall_thickness: float,
    bottom_thickness: float,
    corner_radius: float,
    center_x: float,
    center_y: float,
    side_groove_depth: float,
    side_groove_height: float,
    lid_thickness: float,
):
    body_height = body_top_z - body_bottom_z
    inner_width = outer_width - wall_thickness * 2.0
    inner_depth = outer_depth - wall_thickness * 2.0
    inner_bottom_z = body_bottom_z + bottom_thickness
    track_floor_z = body_top_z - lid_thickness - 0.2
    inner_height = body_top_z - inner_bottom_z + 0.6

    body = _rounded_prism(cq, outer_width, outer_depth, body_height, corner_radius).translate(
        (center_x, center_y, body_bottom_z)
    )
    body = body.cut(
        _rounded_prism(cq, inner_width, inner_depth, inner_height, 0.35).translate(
            (center_x, center_y, inner_bottom_z)
        )
    )

    bottom_groove_center_z = 7.75
    top_groove_center_z = body_top_z - (bottom_groove_center_z - body_bottom_z)
    for groove_center_z in (bottom_groove_center_z, top_groove_center_z):
        body = _cut_outer_groove(
            cq=cq,
            body=body,
            outer_width=outer_width,
            outer_depth=outer_depth,
            corner_radius=corner_radius,
            center_x=center_x,
            center_y=center_y,
            center_z=groove_center_z,
            depth=side_groove_depth,
            height=side_groove_height,
        )
    body = body.cut(
        _dutch_style_side_dovetail_track_cuts(
            cq=cq,
            outer_width=outer_width,
            inner_depth=inner_depth,
            wall_thickness=wall_thickness,
            center_x=center_x,
            center_y=center_y,
            track_z=track_floor_z,
            body_top_z=body_top_z,
        )
    )
    body = body.cut(
        _dutch_style_right_lid_track_cut(
            cq=cq,
            outer_width=outer_width,
            inner_depth=inner_depth,
            body_top_z=body_top_z,
            center_x=center_x,
            center_y=center_y,
            track_z=track_floor_z,
        )
    )
    body = body.union(
        _dutch_style_top_click_features(
            cq=cq,
            outer_width=outer_width,
            inner_depth=inner_depth,
            center_x=center_x,
            center_y=center_y,
            track_z=track_floor_z,
        )
    )

    try:
        body = body.edges("|Z").fillet(min(corner_radius, 1.55))
    except Exception:
        pass

    return body.clean()


def _build_lid(
    *,
    cq,
    width: float,
    depth: float,
    bottom_z: float,
    base_thickness: float,
    relief_height: float,
    edge_chamfer: float,
    center_x: float,
    center_y: float,
    logo_raise: bool,
):
    lid = _lid_dovetail_blank(cq, width, depth, base_thickness).translate(
        (center_x, center_y, bottom_z)
    )

    if edge_chamfer > 0:
        try:
            lid = lid.edges("|Y").chamfer(min(edge_chamfer, base_thickness / 3.0))
        except Exception:
            pass

    lid = _cut_lid_click_notches(
        cq=cq,
        lid=lid,
        width=width,
        bottom_z=bottom_z,
        center_x=center_x,
        center_y=center_y,
    )

    panel = _raised_lid_border(
        cq=cq,
        width=width - 6.0,
        depth=depth - 6.0,
        height=relief_height,
        z=bottom_z + base_thickness,
    ).translate((center_x - 1.1, center_y, 0.0))
    lid = lid.union(panel)

    if logo_raise:
        logo = _monopoly_deal_logo(
            cq=cq,
            z=bottom_z + base_thickness - 0.05,
            height=relief_height + 0.05,
        ).translate((center_x, center_y, 0.0))
        lid = union_dxf_regions(cq, base=lid, regions=logo)

    return lid.clean()


def _rounded_prism(cq, width: float, depth: float, height: float, radius: float):
    prism = cq.Workplane("XY").rect(width, depth).extrude(height)

    if radius > 0:
        try:
            prism = prism.edges("|Z").fillet(radius)
        except Exception:
            pass

    return prism


def _lid_dovetail_blank(cq, width: float, bottom_depth: float, height: float):
    return trapezoidal_panel(
        cq,
        length=width,
        bottom_width=bottom_depth,
        height=height,
        side_inset=2.154108,
        extrusion_axis="x",
    )


def _cut_lid_click_notches(
    *,
    cq,
    lid,
    width: float,
    bottom_z: float,
    center_x: float,
    center_y: float,
):
    groove_center_x = center_x + width / 2.0 - 2.0
    center_groove = (
        cq.Workplane("XY", origin=(0.0, 0.0, bottom_z))
        .center(groove_center_x, center_y)
        .slot2D(10.2, 2.0, angle=90.0)
        .extrude(0.8)
    )
    return lid.cut(center_groove)


def _cut_outer_groove(
    *,
    cq,
    body,
    outer_width: float,
    outer_depth: float,
    corner_radius: float,
    center_x: float,
    center_y: float,
    center_z: float,
    depth: float,
    height: float,
):
    clearance = 0.25
    groove_bottom_z = center_z - height / 2.0
    outer = _rounded_prism(
        cq,
        outer_width + clearance * 2.0,
        outer_depth + clearance * 2.0,
        height,
        corner_radius + clearance,
    ).translate((center_x, center_y, groove_bottom_z))
    inner = _rounded_prism(
        cq,
        outer_width - depth * 2.0,
        outer_depth - depth * 2.0,
        height + 0.2,
        max(corner_radius - depth, 0.1),
    ).translate((center_x, center_y, groove_bottom_z - 0.1))
    return body.cut(outer.cut(inner))


def _dutch_style_side_dovetail_track_cuts(
    *,
    cq,
    outer_width: float,
    inner_depth: float,
    wall_thickness: float,
    center_x: float,
    center_y: float,
    track_z: float,
    body_top_z: float,
):
    groove_bottom_z = track_z - 0.5
    groove_inner_y = center_y + inner_depth / 2.0
    groove_outer_y = groove_inner_y + 2.294306
    positive_profile = [
        (groove_inner_y, groove_bottom_z),
        (groove_inner_y + 0.007, groove_bottom_z + 0.077),
        (groove_inner_y + 0.030, groove_bottom_z + 0.171),
        (groove_inner_y + 0.067, groove_bottom_z + 0.250),
        (groove_inner_y + 0.117, groove_bottom_z + 0.322),
        (groove_inner_y + 0.179, groove_bottom_z + 0.383),
        (groove_inner_y + 0.250, groove_bottom_z + 0.433),
        (groove_inner_y + 0.329, groove_bottom_z + 0.470),
        (groove_inner_y + 0.414, groove_bottom_z + 0.493),
        (groove_inner_y + 0.500, track_z),
        (groove_outer_y, track_z),
        (groove_inner_y, body_top_z + 0.4),
    ]
    negative_profile = [(2.0 * center_y - y, z) for y, z in positive_profile]
    track_length = outer_width - wall_thickness
    track_center_x = center_x + wall_thickness / 2.0
    positive_cut = (
        cq.Workplane("YZ")
        .polyline(positive_profile)
        .close()
        .extrude(track_length / 2.0, both=True)
        .translate((track_center_x, 0.0, 0.0))
    )
    negative_cut = (
        cq.Workplane("YZ")
        .polyline(negative_profile)
        .close()
        .extrude(track_length / 2.0, both=True)
        .translate((track_center_x, 0.0, 0.0))
    )
    return positive_cut.union(negative_cut)


def _dutch_style_right_lid_track_cut(
    *,
    cq,
    outer_width: float,
    inner_depth: float,
    body_top_z: float,
    center_x: float,
    center_y: float,
    track_z: float,
):
    cut_width = 6.72
    cut_depth = inner_depth + 1.0
    cut_height = body_top_z - track_z + 0.5
    return (
        cq.Workplane("XY")
        .box(cut_width, cut_depth, cut_height)
        .translate((center_x + outer_width / 2.0 - 2.0, center_y, track_z + cut_height / 2.0))
    )


def _dutch_style_top_click_features(
    *,
    cq,
    outer_width: float,
    inner_depth: float,
    center_x: float,
    center_y: float,
    track_z: float,
):
    track_center_x = center_x + outer_width / 2.0 - 2.0
    groove_inner_y = center_y + inner_depth / 2.0
    groove_outer_y = groove_inner_y + 2.294306
    side_strip_depth = groove_outer_y - (groove_inner_y + 0.5)
    side_strip_center_offset = inner_depth / 2.0 + 0.5 + side_strip_depth / 2.0
    positive_side_strip = (
        cq.Workplane("XY")
        .box(outer_width, side_strip_depth, 0.2)
        .translate((center_x, center_y + side_strip_center_offset, track_z - 0.1))
    )
    negative_side_strip = (
        cq.Workplane("XY")
        .box(outer_width, side_strip_depth, 0.2)
        .translate((center_x, center_y - side_strip_center_offset, track_z - 0.1))
    )
    track_floor = positive_side_strip.union(negative_side_strip)

    center_lug = (
        cq.Workplane("XY", origin=(0.0, 0.0, track_z))
        .center(track_center_x, center_y)
        .slot2D(10.0, 2.0, angle=90.0)
        .extrude(0.6)
    )
    try:
        center_lug = center_lug.edges(">Z").fillet(0.5)
    except Exception:
        pass

    return track_floor.union(center_lug)


def _raised_lid_border(cq, width: float, depth: float, height: float, z: float):
    border = 1.05
    outer = _rounded_prism(cq, width, depth, height, 0.75).translate((0.0, 0.0, z))
    inner = _rounded_prism(
        cq, width - border * 2.0, depth - border * 2.0, height + 0.2, 0.45
    ).translate((0.0, 0.0, z - 0.1))
    return outer.cut(inner)


def _monopoly_deal_logo(cq, *, z: float, height: float):
    dxf_path = files("print_models.assets.logos").joinpath(
        "monopoly_deal_lid_logo_from_printables_697154.dxf"
    )
    logo = extrude_dxf_regions(
        cq,
        path=dxf_path,
        height=height,
        regions=_MONOPOLY_DEAL_LOGO_REGIONS,
    )
    return logo.translate((0.0, 0.0, z))
