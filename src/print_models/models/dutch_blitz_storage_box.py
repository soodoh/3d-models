"""Parametric CadQuery rebuild of the Dutch Blitz card storage box."""

from __future__ import annotations

from collections.abc import Mapping
from importlib.resources import files
from pathlib import Path

from print_models.dovetail import trapezoidal_panel

NAME = "dutch_blitz_storage_box"
DESCRIPTION = (
    "Parametric CadQuery Dutch Blitz card storage box with editable lid fit and logo sizing."
)
PARAMETERS = {
    "part": "all",
    "outer_width": 123.0,
    "outer_depth": 66.0,
    "outer_height": 92.0,
    "wall_thickness": 4.0,
    "bottom_thickness": 4.0,
    "corner_radius": 1.0,
    "lid_fit_clearance": 2.1,
    "lid_depth_fit_clearance": 2.089892,
    "lid_thickness": 3.076608,
    "lid_edge_chamfer": 0.8,
    "logo_size": 40.66,
    "logo_width": 63.95,
    "logo_depth": 0.8,
    "side_logo_size": 58.0,
    "side_logo_width": 95.0,
    "side_logo_depth": 0.8,
    "slogan_size": 10.0,
    "slogan_depth": 0.8,
    "handle_slot": True,
    "handle_slot_depth": 2.0,
    "click_feature": True,
    "divider_count": 4,
    "divider_depth": 52.0,
    "divider_height": 70.4,
    "divider_bottom_width": 12.5,
    "divider_pitch": 25.5,
}
PRINT_NOTES = (
    "Print the container upright and the lid flat. Tune lid_fit_clearance by printer/material; "
    "increase it for a looser sliding fit or decrease it for a tighter lid."
)

_PART_ALIASES = {
    "all": "all",
    "box": "container",
    "base": "container",
    "container": "container",
    "lid": "lid",
}


def build(
    part: str = "all",
    outer_width: float = 123.0,
    outer_depth: float = 66.0,
    outer_height: float = 92.0,
    wall_thickness: float = 4.0,
    bottom_thickness: float = 4.0,
    corner_radius: float = 1.0,
    lid_fit_clearance: float = 2.1,
    lid_depth_fit_clearance: float = 2.089892,
    lid_thickness: float = 3.076608,
    lid_edge_chamfer: float = 0.8,
    logo_size: float = 40.66,
    logo_width: float = 63.95,
    logo_depth: float = 0.8,
    side_logo_size: float = 58.0,
    side_logo_width: float = 95.0,
    side_logo_depth: float = 0.8,
    slogan_size: float = 10.0,
    slogan_depth: float = 0.8,
    handle_slot: bool = True,
    handle_slot_depth: float = 2.0,
    click_feature: bool = True,
    divider_count: int = 4,
    divider_depth: float = 52.0,
    divider_height: float = 70.4,
    divider_bottom_width: float = 12.5,
    divider_pitch: float = 25.5,
) -> Mapping[str, object]:
    """Build one or both parametric parts."""
    import cadquery as cq

    normalized_part = _normalize_part(part)
    results: dict[str, object] = {}

    if normalized_part in {"all", "container"}:
        results["container"] = _build_container(
            cq=cq,
            outer_width=outer_width,
            outer_depth=outer_depth,
            outer_height=outer_height,
            wall_thickness=wall_thickness,
            bottom_thickness=bottom_thickness,
            corner_radius=corner_radius,
            divider_count=divider_count,
            divider_depth=divider_depth,
            divider_height=divider_height,
            divider_bottom_width=divider_bottom_width,
            divider_pitch=divider_pitch,
            click_feature=click_feature,
            lid_thickness=lid_thickness,
            side_logo_size=side_logo_size,
            side_logo_width=side_logo_width,
            side_logo_depth=side_logo_depth,
            slogan_size=slogan_size,
            slogan_depth=slogan_depth,
        )

    if normalized_part in {"all", "lid"}:
        results["lid"] = _build_lid(
            cq=cq,
            outer_width=outer_width,
            outer_depth=outer_depth,
            lid_fit_clearance=lid_fit_clearance,
            lid_depth_fit_clearance=lid_depth_fit_clearance,
            lid_thickness=lid_thickness,
            lid_edge_chamfer=lid_edge_chamfer,
            logo_size=logo_size,
            logo_width=logo_width,
            logo_depth=logo_depth,
            handle_slot=handle_slot,
            handle_slot_depth=handle_slot_depth,
            click_feature=click_feature,
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
    outer_height: float,
    wall_thickness: float,
    bottom_thickness: float,
    corner_radius: float,
    click_feature: bool,
    lid_thickness: float,
    side_logo_size: float,
    side_logo_width: float,
    side_logo_depth: float,
    slogan_size: float,
    slogan_depth: float,
    divider_count: int,
    divider_depth: float,
    divider_height: float,
    divider_bottom_width: float,
    divider_pitch: float,
):
    body = _rounded_prism(cq, outer_width, outer_depth, outer_height, corner_radius)
    body = body.cut(
        _upper_opening_cut(
            cq=cq,
            width=outer_width - 8.0,
            depth=outer_depth - 8.0,
            z_min=divider_height,
            z_max=outer_height + 1.0,
        )
    )

    slot_start = -divider_pitch * (divider_count - 1) / 2.0
    for index in range(divider_count):
        center = slot_start + index * divider_pitch
        body = body.cut(
            _card_slot_cut(
                cq=cq,
                center=center,
                bottom_width=divider_bottom_width,
                bottom_depth=divider_depth,
                z_min=bottom_thickness,
                z_max=divider_height,
            )
        )

    if side_logo_depth > 0 and side_logo_size > 0:
        body = _engrave_container_side_logos(
            cq=cq,
            body=body,
            outer_depth=outer_depth,
            outer_height=outer_height,
            height=side_logo_size,
            width=side_logo_width,
            depth=side_logo_depth,
        )

    if slogan_depth > 0 and slogan_size > 0:
        body = _engrave_container_short_side_slogans(
            cq=cq,
            body=body,
            outer_width=outer_width,
            outer_height=outer_height,
            size=slogan_size,
            depth=slogan_depth,
        )

    if click_feature:
        track_z = outer_height - lid_thickness - 0.2
        body = body.cut(
            _side_dovetail_track_cuts(
                cq=cq,
                outer_width=outer_width,
                wall_thickness=wall_thickness,
                outer_height=outer_height,
                track_z=track_z,
            )
        )
        body = body.cut(
            _right_lid_track_cut(
                cq=cq,
                outer_width=outer_width,
                outer_depth=outer_depth,
                outer_height=outer_height,
                track_z=track_z,
            )
        )
        body = body.union(
            _top_click_features(
                cq=cq,
                outer_width=outer_width,
                outer_depth=outer_depth,
                track_z=track_z,
            )
        )

    return body.clean()


def _build_lid(
    *,
    cq,
    outer_width: float,
    outer_depth: float,
    lid_fit_clearance: float,
    lid_depth_fit_clearance: float,
    lid_thickness: float,
    lid_edge_chamfer: float,
    logo_size: float,
    logo_width: float,
    logo_depth: float,
    handle_slot: bool,
    handle_slot_depth: float,
    click_feature: bool,
):
    lid_width = outer_width - lid_fit_clearance * 2.0
    lid_depth = outer_depth - lid_depth_fit_clearance * 2.0
    lid = _lid_dovetail_blank(cq, lid_width, lid_depth, lid_thickness)

    if lid_edge_chamfer > 0:
        try:
            lid = lid.edges("|Y").chamfer(min(lid_edge_chamfer, lid_thickness / 3.0))
        except Exception:
            pass

    if logo_depth > 0 and logo_size > 0:
        lid = _engrave_lid_text(
            cq=cq,
            lid=lid,
            lid_thickness=lid_thickness,
            size=logo_size,
            width=logo_width,
            depth=logo_depth,
        )

    if handle_slot and handle_slot_depth > 0:
        slot_center_x = lid_width / 2.0 - 7.5
        lid = (
            lid.faces(">Z")
            .workplane()
            .center(slot_center_x, 0.0)
            .slot2D(25.0, 5.0, angle=90.0)
            .cutBlind(-min(handle_slot_depth, lid_thickness - 0.4))
        )

    if click_feature:
        groove_center_x = lid_width / 2.0 - 2.0
        groove = (
            cq.Workplane("XY")
            .center(groove_center_x, 0.0)
            .slot2D(10.2, 2.0, angle=90.0)
            .extrude(0.8)
        )
        lid = lid.cut(groove)

    return lid.clean()


def _lid_dovetail_blank(cq, width: float, bottom_depth: float, height: float):
    return trapezoidal_panel(
        cq,
        length=width,
        bottom_width=bottom_depth,
        height=height,
        side_inset=2.154108,
        extrusion_axis="x",
    )


def _rounded_prism(cq, width: float, depth: float, height: float, radius: float):
    prism = cq.Workplane("XY").rect(width, depth).extrude(height)

    if radius > 0:
        prism = prism.edges("|Z").fillet(radius)

    return prism


def _upper_opening_cut(cq, width: float, depth: float, z_min: float, z_max: float):
    height = z_max - z_min
    return (
        cq.Workplane("XY")
        .rect(width, depth)
        .extrude(height)
        .translate((0.0, 0.0, z_min))
    )


def _card_slot_cut(
    *,
    cq,
    center: float,
    bottom_width: float,
    bottom_depth: float,
    z_min: float,
    z_max: float,
):
    transition_height = 3.0
    upper_depth = bottom_depth + 6.0
    upper_z_min = z_min + transition_height
    cap_radius = 5.0
    shoulder_z = z_max - cap_radius
    bottom_left = center - bottom_width / 2.0
    bottom_right = center + bottom_width / 2.0
    top_left = bottom_left - cap_radius
    top_right = bottom_right + cap_radius
    arc_offset = cap_radius * 0.2929
    right_arc_midpoint = (bottom_right + arc_offset, z_max - arc_offset)
    left_arc_midpoint = (bottom_left - arc_offset, z_max - arc_offset)
    lower = (
        cq.Workplane("XY")
        .center(center, 0.0)
        .rect(bottom_width, bottom_depth)
        .workplane(offset=transition_height)
        .rect(bottom_width, upper_depth)
        .loft()
        .translate((0.0, 0.0, z_min))
    )
    upper_profile = (
        cq.Workplane("XZ")
        .moveTo(bottom_left, upper_z_min)
        .lineTo(bottom_right, upper_z_min)
        .lineTo(bottom_right, shoulder_z)
        .threePointArc(right_arc_midpoint, (top_right, z_max))
        .lineTo(top_left, z_max)
        .threePointArc(left_arc_midpoint, (bottom_left, shoulder_z))
        .close()
    )
    upper = upper_profile.extrude(upper_depth / 2.0, both=True)
    return lower.union(upper)


def _side_dovetail_track_cuts(
    *,
    cq,
    outer_width: float,
    wall_thickness: float,
    outer_height: float,
    track_z: float,
):
    groove_bottom_z = track_z - 0.5
    groove_outer_y = 31.294306
    groove_inner_y = 29.0
    positive_profile = [
        (groove_inner_y, groove_bottom_z),
        (29.007, groove_bottom_z + 0.077),
        (29.03, groove_bottom_z + 0.171),
        (29.067, groove_bottom_z + 0.25),
        (29.117, groove_bottom_z + 0.322),
        (29.179, groove_bottom_z + 0.383),
        (29.25, groove_bottom_z + 0.433),
        (29.329, groove_bottom_z + 0.47),
        (29.414, groove_bottom_z + 0.493),
        (29.5, track_z),
        (groove_outer_y, track_z),
        (groove_inner_y, outer_height),
    ]
    negative_profile = [(-y, z) for y, z in positive_profile]
    track_length = outer_width - wall_thickness
    track_center_x = wall_thickness / 2.0
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


def _right_lid_track_cut(
    *,
    cq,
    outer_width: float,
    outer_depth: float,
    outer_height: float,
    track_z: float,
):
    cut_width = 6.72
    cut_depth = outer_depth - 7.0
    cut_height = outer_height - track_z + 0.5
    return (
        cq.Workplane("XY")
        .box(cut_width, cut_depth, cut_height)
        .translate((outer_width / 2.0 - 2.0, 0.0, track_z + cut_height / 2.0))
    )


def _top_click_features(*, cq, outer_width: float, outer_depth: float, track_z: float):
    track_center_x = outer_width / 2.0 - 2.0
    frame_outer_depth = outer_depth - 3.411388
    frame_inner_depth = outer_depth - 7.0
    side_strip_depth = (frame_outer_depth - frame_inner_depth) / 2.0
    side_strip_center_offset = frame_inner_depth / 2.0 + side_strip_depth / 2.0
    positive_side_strip = (
        cq.Workplane("XY")
        .box(outer_width, side_strip_depth, 0.2)
        .translate((0.0, side_strip_center_offset, track_z - 0.1))
    )
    negative_side_strip = (
        cq.Workplane("XY")
        .box(outer_width, side_strip_depth, 0.2)
        .translate((0.0, -side_strip_center_offset, track_z - 0.1))
    )
    track_floor = positive_side_strip.union(negative_side_strip)

    lug = (
        cq.Workplane("XY", origin=(0.0, 0.0, track_z))
        .center(track_center_x, 0.0)
        .slot2D(10.0, 2.0, angle=90.0)
        .extrude(0.6)
    )
    try:
        lug = lug.edges(">Z").fillet(0.5)
    except Exception:
        pass

    return track_floor.union(lug)


def _engrave_container_side_logos(
    *,
    cq,
    body,
    outer_depth: float,
    outer_height: float,
    height: float,
    width: float,
    depth: float,
):
    z_center = outer_height / 2.0
    front = _side_logo_cutter(
        cq=cq,
        y=outer_depth / 2.0,
        z_center=z_center,
        height=height,
        width=width,
        depth=depth,
        front=True,
    )
    back = _side_logo_cutter(
        cq=cq,
        y=-outer_depth / 2.0,
        z_center=z_center,
        height=height,
        width=width,
        depth=depth,
        front=False,
    )
    return body.cut(front).cut(back)


def _side_logo_cutter(
    *,
    cq,
    y: float,
    z_center: float,
    height: float,
    width: float,
    depth: float,
    front: bool,
):
    overshoot = 0.05
    shape = _title_logo_shape(cq, height=height, width=width, depth=depth + overshoot)
    if front:
        shape = shape.mirror("YZ")
        angle = 90.0
        y_offset = overshoot
    else:
        shape = shape.mirror("XZ")
        angle = -90.0
        y_offset = -overshoot
    shape = shape.rotate((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), angle)
    shape = shape.translate((0.0, y + y_offset, z_center))
    return cq.Workplane("XY").add(shape)


def _title_logo_shape(cq, *, height: float, width: float, depth: float):
    dxf_path = files("print_models.assets.logos").joinpath(
        "dutch_blitz_title_from_124738.dxf"
    )
    workplane = cq.importers.importDXF(str(dxf_path))
    shape = workplane.wires().toPending().extrude(depth).val()
    logo_aspect = 1.133492252681764
    x_scale = width / logo_aspect
    return shape.transformGeometry(
        cq.Matrix([[x_scale, 0, 0, 0], [0, height, 0, 0], [0, 0, 1, 0]])
    )


def _engrave_container_short_side_slogans(
    *,
    cq,
    body,
    outer_width: float,
    outer_height: float,
    size: float,
    depth: float,
):
    z_center = outer_height / 2.0
    right = _short_side_slogan_cutter(
        cq=cq,
        x=outer_width / 2.0,
        z_center=z_center,
        size=size,
        depth=depth,
        right=True,
    )
    left = _short_side_slogan_cutter(
        cq=cq,
        x=-outer_width / 2.0,
        z_center=z_center,
        size=size,
        depth=depth,
        right=False,
    )
    return body.cut(right).cut(left)


def _short_side_slogan_cutter(
    *,
    cq,
    x: float,
    z_center: float,
    size: float,
    depth: float,
    right: bool,
):
    distance = -depth if right else depth
    cutter = _text_block(
        cq=cq,
        plane="YZ",
        origin=(x, 0.0, z_center),
        text="A Vonderful\nGoot Game!",
        size=size,
        distance=distance,
        font="Fraunces",
        kind="bold",
        line_spacing_factor=0.85,
    )
    if right:
        return cutter
    return cutter.mirror("XZ")


def _text_block(
    cq,
    plane: str,
    origin: tuple[float, float, float],
    text: str,
    size: float,
    distance: float,
    font: str,
    kind: str,
    line_spacing_factor: float,
):
    lines = [
        line.strip() for line in text.replace("/", "\n").splitlines() if line.strip()
    ]
    if not lines:
        return cq.Workplane(plane, origin=origin)

    line_spacing = size * line_spacing_factor
    total_height = line_spacing * (len(lines) - 1)
    result = None
    text_options = _text_options(font, kind)

    for index, line in enumerate(lines):
        y_offset = total_height / 2.0 - index * line_spacing
        if plane == "XY":
            workplane_origin = (origin[0], origin[1] + y_offset, origin[2])
        else:
            workplane_origin = origin
        workplane = cq.Workplane(plane, origin=workplane_origin)
        if plane in {"XZ", "YZ"}:
            workplane = workplane.center(0.0, y_offset)
        text_shape = workplane.text(line, size, distance, combine=False, **text_options)
        result = text_shape if result is None else result.union(text_shape)

    return result


def _text_options(font: str, kind: str) -> dict[str, str]:
    font_path = _logo_font_path(font)
    options = {"font": font, "kind": kind}
    if font_path is not None:
        options["fontPath"] = str(font_path)
    return options


def _logo_font_path(font: str) -> Path | None:
    if font == "Fraunces":
        return Path(
            str(files("print_models.assets.fonts").joinpath("Fraunces144pt-Black.otf"))
        )

    return None


def _engrave_lid_text(
    *,
    cq,
    lid,
    lid_thickness: float,
    size: float,
    width: float,
    depth: float,
):
    cutter_shape = _title_logo_shape(cq, height=size, width=width, depth=depth)
    cutter_shape = cutter_shape.translate((0.0, 0.0, lid_thickness - depth))
    cutter = cq.Workplane("XY").add(cutter_shape)
    return lid.cut(cutter)
