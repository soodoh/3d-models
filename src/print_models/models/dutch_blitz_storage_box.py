"""Compact parametric Dutch Blitz card storage box with four shared-rib pockets."""

from __future__ import annotations

from collections.abc import Mapping
from importlib.resources import files
from pathlib import Path

from print_models.dovetail import trapezoidal_panel

NAME = "dutch_blitz_storage_box"
DESCRIPTION = (
    "Compact four-deck Dutch Blitz storage box with shared ribs, sliding locking lid, "
    "and engraved branding."
)

# Pocket measurements taken from Steve's Dutch Blitz Card Holder Insert (Printables 177150).
# Its STL measures 84.0 x 122.8 x 28.8 mm. The 2.0 mm floor leaves 82.0 mm of held card
# length, while each pocket provides 58.4 mm of card width and 12.6 mm per deck.
_SOURCE_CARD_LENGTH = 82.0
_SOURCE_CARD_POCKET_WIDTH = 58.4
_SOURCE_DECK_POCKET_THICKNESS = 12.6

PARAMETERS = {
    "part": "all",
    "card_length": _SOURCE_CARD_LENGTH,
    "card_width": _SOURCE_CARD_POCKET_WIDTH,
    "deck_thickness": _SOURCE_DECK_POCKET_THICKNESS,
    "card_length_clearance": 2.0,
    "wall_thickness": 4.0,
    "bottom_thickness": 4.0,
    "corner_radius": 1.0,
    "lid_fit_clearance": 2.1,
    "lid_depth_fit_clearance": 2.089892,
    "lid_thickness": 3.076608,
    "lid_edge_chamfer": 0.8,
    "logo_size": 32.0,
    "logo_width": 50.0,
    "logo_depth": 0.8,
    "side_logo_size": 40.0,
    "side_logo_width": 52.0,
    "side_logo_depth": 0.8,
    "slogan_size": 10.0,
    "slogan_depth": 0.8,
    "handle_slot": True,
    "handle_slot_depth": 2.0,
    "click_feature": True,
    "divider_count": 4,
    "divider_thickness": 1.6,
    "divider_height": 70.4,
}
PRINT_NOTES = (
    "Print the container upright and the lid flat. Card-pocket width and deck thickness are "
    "measured from Printables model 177150. Tune lid_fit_clearance by printer/material; "
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
    card_length: float = _SOURCE_CARD_LENGTH,
    card_width: float = _SOURCE_CARD_POCKET_WIDTH,
    deck_thickness: float = _SOURCE_DECK_POCKET_THICKNESS,
    card_length_clearance: float = 2.0,
    wall_thickness: float = 4.0,
    bottom_thickness: float = 4.0,
    corner_radius: float = 1.0,
    lid_fit_clearance: float = 2.1,
    lid_depth_fit_clearance: float = 2.089892,
    lid_thickness: float = 3.076608,
    lid_edge_chamfer: float = 0.8,
    logo_size: float = 32.0,
    logo_width: float = 50.0,
    logo_depth: float = 0.8,
    side_logo_size: float = 40.0,
    side_logo_width: float = 52.0,
    side_logo_depth: float = 0.8,
    slogan_size: float = 10.0,
    slogan_depth: float = 0.8,
    handle_slot: bool = True,
    handle_slot_depth: float = 2.0,
    click_feature: bool = True,
    divider_count: int = 4,
    divider_thickness: float = 1.6,
    divider_height: float = 70.4,
) -> Mapping[str, object]:
    """Build one or both compact parametric parts."""
    import cadquery as cq

    normalized_part = _normalize_part(part)
    _validate_dimensions(
        card_length=card_length,
        card_width=card_width,
        deck_thickness=deck_thickness,
        card_length_clearance=card_length_clearance,
        wall_thickness=wall_thickness,
        bottom_thickness=bottom_thickness,
        corner_radius=corner_radius,
        lid_fit_clearance=lid_fit_clearance,
        lid_depth_fit_clearance=lid_depth_fit_clearance,
        lid_thickness=lid_thickness,
        divider_count=divider_count,
        divider_thickness=divider_thickness,
        divider_height=divider_height,
    )

    interior_width = divider_count * deck_thickness + (divider_count - 1) * divider_thickness
    outer_width = interior_width + 2.0 * wall_thickness
    outer_depth = card_width + 2.0 * wall_thickness
    outer_height = bottom_thickness + card_length + card_length_clearance + lid_thickness

    results: dict[str, object] = {}
    if normalized_part in {"all", "container"}:
        results["container"] = _build_container(
            cq=cq,
            outer_width=outer_width,
            outer_depth=outer_depth,
            outer_height=outer_height,
            interior_width=interior_width,
            card_width=card_width,
            deck_thickness=deck_thickness,
            wall_thickness=wall_thickness,
            bottom_thickness=bottom_thickness,
            corner_radius=corner_radius,
            divider_count=divider_count,
            divider_thickness=divider_thickness,
            divider_height=divider_height,
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
            wall_thickness=wall_thickness,
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


def _validate_dimensions(
    *,
    card_length: float,
    card_width: float,
    deck_thickness: float,
    card_length_clearance: float,
    wall_thickness: float,
    bottom_thickness: float,
    corner_radius: float,
    lid_fit_clearance: float,
    lid_depth_fit_clearance: float,
    lid_thickness: float,
    divider_count: int,
    divider_thickness: float,
    divider_height: float,
) -> None:
    positive_dimensions = {
        "card_length": card_length,
        "card_width": card_width,
        "deck_thickness": deck_thickness,
        "wall_thickness": wall_thickness,
        "bottom_thickness": bottom_thickness,
        "lid_thickness": lid_thickness,
        "divider_thickness": divider_thickness,
        "divider_height": divider_height,
    }
    for name, value in positive_dimensions.items():
        if value <= 0:
            raise ValueError(f"{name} must be positive")

    non_negative_dimensions = {
        "card_length_clearance": card_length_clearance,
        "corner_radius": corner_radius,
        "lid_fit_clearance": lid_fit_clearance,
        "lid_depth_fit_clearance": lid_depth_fit_clearance,
    }
    for name, value in non_negative_dimensions.items():
        if value < 0:
            raise ValueError(f"{name} must not be negative")

    if isinstance(divider_count, bool) or not isinstance(divider_count, int) or divider_count < 1:
        raise ValueError("divider_count must be a positive integer")
    if wall_thickness < 3.0:
        raise ValueError("wall_thickness must be at least 3.0 mm for the sliding lid tracks")

    lid_bottom = bottom_thickness + card_length + card_length_clearance
    if not bottom_thickness < divider_height < lid_bottom:
        raise ValueError("divider_height must be above the floor and below the lid")


def _build_container(
    *,
    cq,
    outer_width: float,
    outer_depth: float,
    outer_height: float,
    interior_width: float,
    card_width: float,
    deck_thickness: float,
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
    divider_thickness: float,
    divider_height: float,
):
    body = _rounded_prism(cq, outer_width, outer_depth, outer_height, corner_radius)
    body = body.cut(
        _upper_opening_cut(
            cq=cq,
            width=interior_width,
            depth=card_width,
            z_min=bottom_thickness,
            z_max=outer_height + 1.0,
        )
    )

    rib_height = divider_height - bottom_thickness
    first_rib_x = -interior_width / 2.0 + deck_thickness + divider_thickness / 2.0
    for index in range(divider_count - 1):
        center_x = first_rib_x + index * (deck_thickness + divider_thickness)
        rib = (
            cq.Workplane("XY")
            .box(divider_thickness, card_width, rib_height)
            .translate((center_x, 0.0, bottom_thickness + rib_height / 2.0))
        )
        body = body.union(rib)

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
            _front_dovetail_track_cuts(
                cq=cq,
                outer_width=outer_width,
                outer_depth=outer_depth,
                wall_thickness=wall_thickness,
                outer_height=outer_height,
                track_z=track_z,
            )
        )
        body = body.cut(
            _front_lid_track_cut(
                cq=cq,
                outer_width=outer_width,
                outer_depth=outer_depth,
                wall_thickness=wall_thickness,
                outer_height=outer_height,
                track_z=track_z,
            )
        )
        body = body.union(
            _top_click_features(
                cq=cq,
                outer_width=outer_width,
                outer_depth=outer_depth,
                wall_thickness=wall_thickness,
                track_z=track_z,
            )
        )

    return body.clean()


def _build_lid(
    *,
    cq,
    outer_width: float,
    outer_depth: float,
    wall_thickness: float,
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
            lid = lid.edges("|X").chamfer(min(lid_edge_chamfer, lid_thickness / 3.0))
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
        slot_center_y = -lid_depth / 2.0 + 7.0
        lid = (
            lid.faces(">Z")
            .workplane()
            .center(0.0, slot_center_y)
            .slot2D(25.0, 5.0)
            .cutBlind(-min(handle_slot_depth, lid_thickness - 0.4))
        )

    if click_feature:
        groove_center_y = -lid_depth / 2.0 + wall_thickness / 2.0
        groove = cq.Workplane("XY").center(0.0, groove_center_y).slot2D(10.2, 2.0).extrude(0.8)
        lid = lid.cut(groove)

    return lid.clean()


def _lid_dovetail_blank(cq, width: float, bottom_depth: float, height: float):
    return trapezoidal_panel(
        cq,
        length=bottom_depth,
        bottom_width=width,
        height=height,
        side_inset=2.154108,
        extrusion_axis="y",
    )


def _rounded_prism(cq, width: float, depth: float, height: float, radius: float):
    prism = cq.Workplane("XY").rect(width, depth).extrude(height)

    if radius > 0:
        prism = prism.edges("|Z").fillet(radius)

    return prism


def _upper_opening_cut(cq, width: float, depth: float, z_min: float, z_max: float):
    height = z_max - z_min
    return cq.Workplane("XY").rect(width, depth).extrude(height).translate((0.0, 0.0, z_min))


def _front_dovetail_track_cuts(
    *,
    cq,
    outer_width: float,
    outer_depth: float,
    wall_thickness: float,
    outer_height: float,
    track_z: float,
):
    groove_bottom_z = track_z - 0.5
    groove_inner_x = outer_width / 2.0 - wall_thickness
    groove_outer_x = outer_width / 2.0 - 1.705694
    positive_profile = [
        (groove_inner_x, groove_bottom_z),
        (groove_inner_x + 0.007, groove_bottom_z + 0.077),
        (groove_inner_x + 0.03, groove_bottom_z + 0.171),
        (groove_inner_x + 0.067, groove_bottom_z + 0.25),
        (groove_inner_x + 0.117, groove_bottom_z + 0.322),
        (groove_inner_x + 0.179, groove_bottom_z + 0.383),
        (groove_inner_x + 0.25, groove_bottom_z + 0.433),
        (groove_inner_x + 0.329, groove_bottom_z + 0.47),
        (groove_inner_x + 0.414, groove_bottom_z + 0.493),
        (groove_inner_x + 0.5, track_z),
        (groove_outer_x, track_z),
        (groove_inner_x, outer_height),
    ]
    negative_profile = [(-x, z) for x, z in positive_profile]
    track_length = outer_depth - wall_thickness
    track_center_y = -wall_thickness / 2.0
    positive_cut = (
        cq.Workplane("XZ")
        .polyline(positive_profile)
        .close()
        .extrude(track_length / 2.0, both=True)
        .translate((0.0, track_center_y, 0.0))
    )
    negative_cut = (
        cq.Workplane("XZ")
        .polyline(negative_profile)
        .close()
        .extrude(track_length / 2.0, both=True)
        .translate((0.0, track_center_y, 0.0))
    )
    return positive_cut.union(negative_cut)


def _front_lid_track_cut(
    *,
    cq,
    outer_width: float,
    outer_depth: float,
    wall_thickness: float,
    outer_height: float,
    track_z: float,
):
    cut_width = outer_width - (2.0 * wall_thickness - 1.0)
    cut_depth = wall_thickness + 2.72
    cut_height = outer_height - track_z + 0.5
    return (
        cq.Workplane("XY")
        .box(cut_width, cut_depth, cut_height)
        .translate(
            (
                0.0,
                -outer_depth / 2.0 + wall_thickness / 2.0,
                track_z + cut_height / 2.0,
            )
        )
    )


def _top_click_features(
    *,
    cq,
    outer_width: float,
    outer_depth: float,
    wall_thickness: float,
    track_z: float,
):
    track_center_y = -outer_depth / 2.0 + wall_thickness / 2.0
    frame_outer_width = outer_width - 3.411388
    frame_inner_width = outer_width - (2.0 * wall_thickness - 1.0)
    side_strip_width = (frame_outer_width - frame_inner_width) / 2.0
    side_strip_center_offset = frame_inner_width / 2.0 + side_strip_width / 2.0
    positive_side_strip = (
        cq.Workplane("XY")
        .box(side_strip_width, outer_depth, 0.2)
        .translate((side_strip_center_offset, 0.0, track_z - 0.1))
    )
    negative_side_strip = (
        cq.Workplane("XY")
        .box(side_strip_width, outer_depth, 0.2)
        .translate((-side_strip_center_offset, 0.0, track_z - 0.1))
    )
    track_floor = positive_side_strip.union(negative_side_strip)

    lug = (
        cq.Workplane("XY", origin=(0.0, 0.0, track_z))
        .center(0.0, track_center_y)
        .slot2D(10.0, 2.0)
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
    dxf_path = files("print_models.assets.logos").joinpath("dutch_blitz_title_from_124738.dxf")
    workplane = cq.importers.importDXF(str(dxf_path))
    shape = workplane.wires().toPending().extrude(depth).val()
    logo_aspect = 1.133492252681764
    x_scale = width / logo_aspect
    return shape.transformGeometry(cq.Matrix([[x_scale, 0, 0, 0], [0, height, 0, 0], [0, 0, 1, 0]]))


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
    lines = [line.strip() for line in text.replace("/", "\n").splitlines() if line.strip()]
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
        return Path(str(files("print_models.assets.fonts").joinpath("Fraunces144pt-Black.otf")))

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
