"""Parametric CadQuery recreation of the Five Crowns sliding deck box."""

from __future__ import annotations

from collections.abc import Mapping
from importlib.resources import files
from pathlib import Path

NAME = "five_crowns_storage_box"
DESCRIPTION = (
    "CadQuery rebuild of the Printables Five Crowns deck box body and sliding lid."
)
PARAMETERS = {
    "part": "all",
    "outer_width": 98.362904,
    "outer_depth": 64.0,
    "body_bottom_z": -2.0,
    "body_height": 48.0,
    "wall_thickness": 3.0,
    "bottom_thickness": 2.0,
    "corner_radius": 1.55,
    "body_center_x": -0.103886,
    "body_center_y": -0.356632,
    "lid_width": 95.362904,
    "lid_depth": 59.753345,
    "lid_bottom_z": 42.000004,
    "lid_base_thickness": 4.30,
    "lid_relief_height": 1.23,
    "lid_corner_radius": 1.15,
    "lid_right_gap": 3.0,
    "lid_edge_chamfer": 0.8,
    "side_groove_depth": 0.65,
    "side_groove_height": 1.25,
    "logo_raise": True,
}
PRINT_NOTES = (
    "The body and lid are modeled in the same assembled coordinate frame as the source STLs. "
    "Use part=container or part=lid to export individual printable parts."
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
    body_height: float = 48.0,
    wall_thickness: float = 3.0,
    bottom_thickness: float = 2.0,
    corner_radius: float = 1.55,
    body_center_x: float = -0.103886,
    body_center_y: float = -0.356632,
    lid_width: float = 95.362904,
    lid_depth: float = 59.753345,
    lid_bottom_z: float = 42.000004,
    lid_base_thickness: float = 4.30,
    lid_relief_height: float = 1.23,
    lid_corner_radius: float = 1.15,
    lid_right_gap: float = 3.0,
    lid_edge_chamfer: float = 0.8,
    side_groove_depth: float = 0.65,
    side_groove_height: float = 1.25,
    logo_raise: bool = True,
) -> Mapping[str, object]:
    """Build one or both Five Crowns deck box parts."""
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
            corner_radius=lid_corner_radius,
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

    body = _rounded_prism(
        cq, outer_width, outer_depth, body_height, corner_radius
    ).translate((center_x, center_y, body_bottom_z))
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
            outer_depth=outer_depth,
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
            outer_depth=outer_depth,
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
            outer_depth=outer_depth,
            body_bottom_z=body_bottom_z,
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
    corner_radius: float,
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
        depth=depth,
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
        logo = _five_crowns_logo(
            cq=cq,
            z=bottom_z + base_thickness,
            height=relief_height,
        ).translate((center_x, center_y, 0.0))
        lid = lid.union(logo)

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
    # Same trapezoidal YZ profile used by the Dutch Blitz lid: the bottom is wider
    # than the top so it slides into matching dovetail tracks in the container.
    side_inset = 2.154108
    top_depth = bottom_depth - side_inset * 2.0
    profile = [
        (-bottom_depth / 2.0, 0.0),
        (bottom_depth / 2.0, 0.0),
        (top_depth / 2.0, height),
        (-top_depth / 2.0, height),
    ]
    return cq.Workplane("YZ").polyline(profile).close().extrude(width / 2.0, both=True)


def _cut_lid_click_notches(
    *,
    cq,
    lid,
    width: float,
    depth: float,
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
    outer_depth: float,
    center_x: float,
    center_y: float,
    track_z: float,
    body_top_z: float,
):
    groove_bottom_z = track_z - 0.5
    groove_outer_y = center_y + outer_depth / 2.0 - 1.705694
    groove_inner_y = center_y + outer_depth / 2.0 - 4.0
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
    track_length = outer_width - 4.0
    track_center_x = center_x + 2.0
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
    outer_depth: float,
    body_top_z: float,
    center_x: float,
    center_y: float,
    track_z: float,
):
    cut_width = 6.72
    cut_depth = outer_depth - 7.0
    cut_height = body_top_z - track_z + 0.5
    return (
        cq.Workplane("XY")
        .box(cut_width, cut_depth, cut_height)
        .translate(
            (center_x + outer_width / 2.0 - 2.0, center_y, track_z + cut_height / 2.0)
        )
    )


def _dutch_style_top_click_features(
    *,
    cq,
    outer_width: float,
    outer_depth: float,
    body_bottom_z: float,
    center_x: float,
    center_y: float,
    track_z: float,
):
    track_center_x = center_x + outer_width / 2.0 - 2.0
    frame_outer_width = outer_width - 4.0
    frame_outer_depth = outer_depth - 3.411388
    frame_inner_width = outer_width - 10.725808
    frame_inner_depth = outer_depth - 7.0
    frame_center_x = center_x + 2.0
    inner_center_x = center_x
    frame_outer = (
        cq.Workplane("XY")
        .box(frame_outer_width, frame_outer_depth, 0.2)
        .translate((frame_center_x, center_y, track_z - 0.1))
    )
    frame_inner = (
        cq.Workplane("XY")
        .box(frame_inner_width, frame_inner_depth, 0.4)
        .translate((inner_center_x, center_y, track_z - 0.1))
    )
    track_floor = frame_outer.cut(frame_inner)

    back_support_outer_x = frame_center_x - frame_outer_width / 2.0
    back_support_inner_x = inner_center_x - frame_inner_width / 2.0
    back_support_width = back_support_inner_x - back_support_outer_x
    back_support_center_x = back_support_outer_x + back_support_width / 2.0
    back_support_height = track_z - body_bottom_z
    back_support = (
        cq.Workplane("XY")
        .box(
            back_support_width,
            frame_outer_depth,
            back_support_height,
        )
        .translate(
            (back_support_center_x, center_y, body_bottom_z + back_support_height / 2.0)
        )
    )

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

    return track_floor.union(back_support).union(center_lug)


def _add_top_lid_lip(
    *,
    cq,
    body,
    outer_width: float,
    outer_depth: float,
    center_x: float,
    center_y: float,
    z: float,
):
    lip_height = 0.32
    outer = _rounded_prism(
        cq, outer_width - 1.8, outer_depth - 1.8, lip_height, 1.0
    ).translate((center_x, center_y, z))
    inner = _rounded_prism(
        cq, outer_width - 5.0, outer_depth - 5.0, lip_height + 0.2, 0.6
    ).translate((center_x, center_y, z - 0.1))
    return body.union(outer.cut(inner))


def _raised_lid_border(cq, width: float, depth: float, height: float, z: float):
    border = 1.05
    outer = _rounded_prism(cq, width, depth, height, 0.75).translate((0.0, 0.0, z))
    inner = _rounded_prism(
        cq, width - border * 2.0, depth - border * 2.0, height + 0.2, 0.45
    ).translate((0.0, 0.0, z - 0.1))
    return outer.cut(inner)


def _five_crowns_logo(cq, *, z: float, height: float):
    dxf_path = files("print_models.assets.logos").joinpath(
        "five_crowns_lid_logo_from_source_section.dxf"
    )
    logo = cq.importers.importDXF(str(dxf_path)).wires().toPending().extrude(height)
    return logo.translate((0.0, 0.0, z))


def _logo_background(cq, *, z: float, height: float):
    # Hand-fit outline matching the raised Five Crowns emblem from the baseline lid.
    points = [
        (-38.2, 8.3),
        (-33.5, 7.8),
        (-27.0, 10.0),
        (-23.2, 14.2),
        (-21.2, 18.2),
        (-16.8, 15.2),
        (-10.5, 13.7),
        (-5.0, 15.2),
        (-1.5, 23.8),
        (2.4, 15.6),
        (8.5, 13.8),
        (14.4, 15.2),
        (18.0, 18.2),
        (20.0, 13.2),
        (25.0, 9.6),
        (31.0, 8.0),
        (36.5, 8.6),
        (31.0, -11.8),
        (32.6, -15.0),
        (35.0, -16.4),
        (33.2, -18.8),
        (28.2, -19.4),
        (15.0, -17.8),
        (0.0, -16.3),
        (-15.2, -17.7),
        (-28.8, -19.3),
        (-34.0, -18.8),
        (-35.2, -16.5),
        (-32.4, -14.7),
        (-31.2, -11.2),
    ]
    background = (
        cq.Workplane("XY")
        .polyline(points)
        .close()
        .extrude(height)
        .translate((0.0, 0.0, z))
    )
    try:
        background = background.edges(">Z").fillet(0.45)
    except Exception:
        pass
    return background


def _crown(cq, *, z: float, height: float, width: float, depth: float):
    half_width = width / 2.0
    bottom = -depth / 2.0
    points = [
        (-half_width, bottom),
        (-half_width * 0.74, bottom + 3.1),
        (-half_width * 0.62, bottom + 12.5),
        (-half_width * 0.38, bottom + 10.0),
        (0.0, depth / 2.0),
        (half_width * 0.38, bottom + 10.0),
        (half_width * 0.62, bottom + 12.5),
        (half_width * 0.74, bottom + 3.1),
        (half_width, bottom),
        (half_width * 0.88, bottom - 3.5),
        (0.0, bottom - 0.4),
        (-half_width * 0.88, bottom - 3.5),
    ]
    crown = (
        cq.Workplane("XY")
        .polyline(points)
        .close()
        .extrude(height)
        .translate((0.0, 0.0, z))
    )
    try:
        crown = crown.edges(">Z").fillet(0.45)
    except Exception:
        pass
    return crown


def _ribbon(cq, *, z: float, height: float, width: float, depth: float):
    half_width = width / 2.0
    half_depth = depth / 2.0
    points = [
        (-half_width, 0.0),
        (-half_width + 4.0, half_depth),
        (-8.0, half_depth * 0.55),
        (0.0, half_depth * 0.4),
        (8.0, half_depth * 0.55),
        (half_width - 4.0, half_depth),
        (half_width, 0.0),
        (half_width - 5.4, -half_depth),
        (8.0, -half_depth * 0.75),
        (0.0, -half_depth * 0.55),
        (-8.0, -half_depth * 0.75),
        (-half_width + 5.4, -half_depth),
    ]
    ribbon = (
        cq.Workplane("XY")
        .polyline(points)
        .close()
        .extrude(height)
        .translate((0.0, 0.0, z))
    )
    try:
        ribbon = ribbon.edges(">Z").fillet(0.6)
    except Exception:
        pass
    return ribbon


def _text_shape(cq, *, text: str, size: float, distance: float, z: float, y: float):
    workplane = cq.Workplane("XY", origin=(0.0, y, z))
    return workplane.text(text, size, distance, combine=True, **_text_options())


def _text_options() -> dict[str, str]:
    font_path = _logo_font_path()
    return {"font": "Fraunces", "kind": "regular", "fontPath": str(font_path)}


def _logo_font_path() -> Path:
    return Path(
        str(files("print_models.assets.fonts").joinpath("Fraunces144pt-Black.ttf"))
    )
