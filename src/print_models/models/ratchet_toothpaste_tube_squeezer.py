"""Parametric recreation of ScrapyCoco's upgraded ratchet tube squeezer."""

from __future__ import annotations

import math
from collections.abc import Mapping

NAME = "ratchet_toothpaste_tube_squeezer"
DESCRIPTION = (
    "Five-part upgraded ratcheting toothpaste tube squeezer with adjustable tube width "
    "and slot gap."
)
PARAMETERS = {
    "tube_width_mm": 55.0,
    "gap_mm": 1.0,
}
PRINT_NOTES = (
    "Parametric recreation modified from ScrapyCoco's 'Upgraded Ratchet Toothpaste Tube "
    "Squeezer' (https://www.printables.com/model/365365), a remix of Luke's 3D model "
    "265248 (https://www.printables.com/model/265248). Licensed CC BY-NC 4.0: "
    "https://creativecommons.org/licenses/by-nc/4.0/. Print the shaft, ratchet, and nut in "
    "PETG. The shaft is oriented broad-side-down for printing. gap_mm controls both the shaft "
    "slot and body throat."
)

DEFAULT_TUBE_WIDTH_MM = 55.0
MINIMUM_TUBE_WIDTH_MM = 13.0
MINIMUM_GAP_MM = 0.05
SHAFT_DEPTH_MM = 6.0
SHAFT_RADIUS_MM = 3.933
BODY_OUTER_RADIUS_MM = 13.0
BODY_INNER_RADIUS_MM = 11.0
BODY_BORE_RADIUS_MM = 4.5
THREAD_PITCH_MM = 1.25
THREAD_LENGTH_MM = 10.0
THREAD_ROOT_RADIUS_MM = 3.0
THREAD_MAJOR_RADIUS_MM = 3.791
THREAD_CREST_HALF_DEGREES = 30.0
NUT_THREAD_ROOT_RADIUS_MM = 3.324
NUT_THREAD_MAJOR_RADIUS_MM = 4.275
NUT_THREAD_CREST_HALF_DEGREES = 35.0
NUT_HEIGHT_MM = 12.0
THREAD_PROFILE_SAMPLES = 16
THREAD_SECTION_DEGREES = 30.0


def build(
    tube_width_mm: float = DEFAULT_TUBE_WIDTH_MM,
    gap_mm: float = 1.0,
) -> Mapping[str, object]:
    """Build the body, shaft, handle, ratchet, and nut as separate printable parts."""
    _validate_parameters(tube_width_mm=tube_width_mm, gap_mm=gap_mm)

    return {
        "body": _build_body(tube_width_mm=tube_width_mm, gap_mm=gap_mm),
        "shaft": _build_shaft(tube_width_mm=tube_width_mm, gap_mm=gap_mm),
        "handle": _build_handle(),
        "ratchet": _build_ratchet(),
        "nut": _build_nut(),
    }


def _build_shaft(*, tube_width_mm: float, gap_mm: float):
    import cadquery as cq

    flange_height = 1.5
    shank_length = tube_width_mm + 22.5
    thread_start = flange_height + shank_length

    flange_points = (
        (-7.5, -1.5),
        (-6.0, -3.0),
        (6.0, -3.0),
        (7.5, -1.5),
        (7.5, 1.5),
        (6.0, 3.0),
        (-6.0, 3.0),
        (-7.5, 1.5),
    )
    flange = cq.Workplane("XY").polyline(flange_points).close().extrude(flange_height)

    shank_blank = cq.Workplane("XY").circle(SHAFT_RADIUS_MM).extrude(shank_length)
    shank_clip = (
        cq.Workplane("XY")
        .box(SHAFT_RADIUS_MM * 2.0 + 2.0, SHAFT_DEPTH_MM, shank_length)
        .translate((0.0, 0.0, shank_length / 2.0))
    )
    shaft = flange.union(shank_blank.intersect(shank_clip).translate((0.0, 0.0, flange_height)))

    slot_length = tube_width_mm + 9.0
    slot = (
        cq.Workplane("XY")
        .box(gap_mm, SHAFT_DEPTH_MM + 2.0, slot_length)
        .translate((0.03125, 0.0, 10.75 + slot_length / 2.0))
    )
    shaft = shaft.cut(slot)

    threaded_end = _threaded_end(
        cq,
        root_radius=THREAD_ROOT_RADIUS_MM,
        major_radius=THREAD_MAJOR_RADIUS_MM,
        height=THREAD_LENGTH_MM,
    ).translate((0.0, 0.0, thread_start))
    thread_clip = (
        cq.Workplane("XY")
        .box(THREAD_MAJOR_RADIUS_MM * 2.0 + 1.0, SHAFT_DEPTH_MM, THREAD_LENGTH_MM)
        .translate((0.0, 0.0, thread_start + THREAD_LENGTH_MM / 2.0))
    )
    shaft = shaft.union(threaded_end.intersect(thread_clip)).clean()

    # Put the broad clipped face on the print bed instead of exporting the shaft upright.
    oriented_shaft = shaft.rotate((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), -90.0)
    return oriented_shaft.translate((0.0, 0.0, -oriented_shaft.val().BoundingBox().zmin)).clean()


def _build_body(*, tube_width_mm: float, gap_mm: float):
    import cadquery as cq

    main_height = tube_width_mm + 7.55
    upper_transition_height = 3.0
    upper_transition_start = main_height - upper_transition_height

    outer = cq.Workplane("XY").circle(BODY_OUTER_RADIUS_MM).extrude(main_height)
    cavity = (
        cq.Workplane("XY")
        .circle(BODY_INNER_RADIUS_MM)
        .extrude(main_height - 3.0)
        .translate((0.0, 0.0, 3.0))
    )
    bore = cq.Workplane("XY").circle(BODY_BORE_RADIUS_MM).extrude(main_height)
    body = outer.cut(cavity).cut(bore)

    wide_opening = _sector_prism(
        cq,
        radius=BODY_OUTER_RADIUS_MM + 1.0,
        start_degrees=-180.0,
        end_degrees=-60.0,
        height=upper_transition_start - 3.0,
    ).translate((0.0, 0.0, 3.0))
    upper_opening = _sector_span_loft(
        cq,
        radius=BODY_OUTER_RADIUS_MM + 1.0,
        center_degrees=-120.0,
        sections=((0.0, 120.0), (upper_transition_height, 94.0)),
    ).translate((0.0, 0.0, upper_transition_start))
    body = body.cut(wide_opening.union(upper_opening))

    narrow_slot = (
        cq.Workplane("XY")
        .box(4.0, gap_mm, main_height - 3.0)
        .translate((12.5, 0.0, 3.0 + (main_height - 3.0) / 2.0))
        .rotate((0.0, 0.0, 0.0), (0.0, 0.0, 1.0), 60.0)
    )
    body = body.cut(narrow_slot)

    shoulder_height = 6.5
    shoulder = _annular_loft(
        cq,
        height=shoulder_height,
        outer_bottom=BODY_OUTER_RADIUS_MM,
        outer_top=6.5,
        inner_bottom=BODY_INNER_RADIUS_MM,
        inner_top=BODY_BORE_RADIUS_MM,
    ).translate((0.0, 0.0, main_height))
    neck = _annular_loft(
        cq,
        height=2.0,
        outer_bottom=6.5,
        outer_top=5.9,
        inner_bottom=BODY_BORE_RADIUS_MM,
        inner_top=BODY_BORE_RADIUS_MM,
    ).translate((0.0, 0.0, main_height + shoulder_height))
    body = body.union(shoulder).union(neck)

    shoulder_opening = _sector_span_loft(
        cq,
        radius=BODY_OUTER_RADIUS_MM + 1.0,
        center_degrees=-120.0,
        sections=(
            (0.0, 94.0),
            (1.25, 85.0),
            (2.5, 74.0),
            (3.75, 61.5),
            (4.75, 49.0),
            (5.55, 38.0),
            (shoulder_height - 0.05, 0.5),
        ),
    ).translate((0.0, 0.0, main_height))
    body = body.cut(shoulder_opening)

    teeth = _internal_ratchet_teeth(cq)
    boss_clearance = cq.Workplane("XY").circle(6.5).extrude(2.0)
    return body.cut(teeth.cut(boss_clearance)).clean()


def _build_handle():
    import cadquery as cq

    outer = _lobed_loft(
        cq,
        lobes=35,
        shape_exponent=0.85,
        sections=(
            (0.0, 12.0, 12.0, 0.0),
            (1.0, 13.0, 13.0, 0.0),
            (2.0, 13.0, 13.65, 0.0),
            (4.0, 13.0, 13.34, 6.0),
            (5.0, 13.0, 13.36, 10.0),
            (7.0, 13.0, 13.68, 18.0),
            (7.8, 13.0, 13.0, 20.0),
        ),
    )

    cavity = cq.Workplane("XY").circle(12.0).extrude(5.0).translate((0.0, 0.0, 2.8))
    handle = outer.cut(cavity)

    boss = cq.Workplane("XY").circle(6.75).extrude(2.7).translate((0.0, 0.0, 2.8))
    handle = handle.union(boss)

    socket_points = (
        (-6.15, -3.175),
        (6.15, -3.175),
        (7.75, -1.575),
        (7.75, 1.575),
        (6.15, 3.175),
        (-6.15, 3.175),
        (-7.75, 1.575),
        (-7.75, -1.575),
    )
    lower_socket = cq.Workplane("XY").polyline(socket_points).close().extrude(1.8)
    upper_socket = cq.Workplane("XY").rect(8.5, 6.35).extrude(3.7).translate((0.0, 0.0, 1.8))
    return handle.cut(lower_socket.union(upper_socket)).clean()


def _build_nut():
    import cadquery as cq

    nut_height = NUT_HEIGHT_MM
    nut = _lobed_loft(
        cq,
        lobes=23,
        shape_exponent=0.5,
        sections=(
            (0.0, 6.5, 6.7, 0.0),
            (0.5, 6.5, 7.2, 0.0),
            (nut_height - 0.5, 6.5, 7.2, 0.0),
            (nut_height, 6.5, 6.7, 0.0),
        ),
    )
    threaded_bore = _threaded_bore(
        cq,
        root_radius=NUT_THREAD_ROOT_RADIUS_MM,
        major_radius=NUT_THREAD_MAJOR_RADIUS_MM,
        height=10.1,
    )
    lead_in = _circular_loft(cq, sections=((0.0, 4.45), (0.6, 4.1)))
    nut = nut.cut(threaded_bore.union(lead_in)).clean()
    return nut.rotate((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), 180.0).translate((0.0, 0.0, nut_height))


def _build_ratchet():
    import cadquery as cq

    ratchet = _ratchet_outer_profile(cq).extrude(4.0)
    upper_relief = _circular_loft(cq, sections=((0.0, 6.75), (2.0, 8.25))).translate(
        (0.0, 0.0, 2.0)
    )
    bore_blank = cq.Workplane("XY").circle(4.175).extrude(4.0)
    bore_clip = cq.Workplane("XY").box(10.0, 6.35, 4.0).translate((0.0, 0.0, 2.0))
    return ratchet.cut(upper_relief).cut(bore_blank.intersect(bore_clip)).clean()


def _ratchet_outer_profile(cq):
    root_end = (-4.973801338, -4.563310229)
    transition_center = (-13.715633994, -12.583673662)
    transition_end = (-7.946461825, -2.217260577)
    segment_points = (
        ("line", (-6.0, -9.25)),
        ("line", (-6.0, -8.25)),
        ("line", (0.0, -8.25)),
        ("arc", (0.75, -7.5), (0.0, -6.75)),
        (
            "arc",
            _arc_midpoint((0.0, 0.0), 6.75, -90.0, _point_angle(root_end)),
            root_end,
        ),
        (
            "arc",
            _arc_midpoint(
                transition_center,
                11.863636364,
                _point_angle(root_end, transition_center),
                _point_angle(transition_end, transition_center),
            ),
            transition_end,
        ),
        (
            "arc",
            _arc_midpoint(
                (-6.7125, 0.0),
                2.5375,
                _point_angle(transition_end, (-6.7125, 0.0)),
                -180.0,
            ),
            (-9.25, 0.0),
        ),
    )

    profile = cq.Workplane("XY").moveTo(0.0, -9.25)
    for rotation in (0.0, -90.0, -180.0, -270.0):
        for operation in segment_points:
            if operation[0] == "line":
                profile = profile.lineTo(*_rotate_point(operation[1], rotation))
            else:
                profile = profile.threePointArc(
                    _rotate_point(operation[1], rotation),
                    _rotate_point(operation[2], rotation),
                )
    return profile.close()


def _internal_ratchet_teeth(cq):
    points = []
    for index in range(20):
        base_degrees = index * 18.0
        for radius, offset_degrees in (
            (10.0, 1.456743),
            (11.145117, 5.833821),
            (10.0, 18.0),
        ):
            angle = math.radians(base_degrees + offset_degrees)
            points.append((radius * math.cos(angle), radius * math.sin(angle)))
    return cq.Workplane("XY").polyline(points).close().extrude(2.0)


def _threaded_end(cq, *, root_radius: float, major_radius: float, height: float):
    return _twisted_thread(
        cq,
        root_radius=root_radius,
        major_radius=major_radius,
        crest_half_degrees=THREAD_CREST_HALF_DEGREES,
        height=height,
    )


def _threaded_bore(cq, *, root_radius: float, major_radius: float, height: float):
    return _twisted_thread(
        cq,
        root_radius=root_radius,
        major_radius=major_radius,
        crest_half_degrees=NUT_THREAD_CREST_HALF_DEGREES,
        height=height,
    )


def _twisted_thread(
    cq,
    *,
    root_radius: float,
    major_radius: float,
    crest_half_degrees: float,
    height: float,
):
    axial_step = THREAD_PITCH_MM * THREAD_SECTION_DEGREES / 360.0
    section_count = math.ceil(height / axial_step)
    section_heights = tuple(height * index / section_count for index in range(section_count + 1))

    workplane = (
        cq.Workplane("XY")
        .polyline(
            _thread_profile_points(root_radius, major_radius, crest_half_degrees, phase_degrees=0.0)
        )
        .close()
    )
    previous_height = 0.0
    for section_height in section_heights[1:]:
        # Positive phase creates a conventional right-hand helix: viewed from the free end,
        # clockwise nut rotation advances the nut toward the shaft base.
        phase_degrees = 360.0 * section_height / THREAD_PITCH_MM
        workplane = (
            workplane.workplane(offset=section_height - previous_height)
            .polyline(
                _thread_profile_points(
                    root_radius,
                    major_radius,
                    crest_half_degrees,
                    phase_degrees=phase_degrees,
                )
            )
            .close()
        )
        previous_height = section_height
    return workplane.loft(combine=True, ruled=True)


def _thread_profile_points(
    root_radius: float,
    major_radius: float,
    crest_half_degrees: float,
    *,
    phase_degrees: float,
) -> tuple[tuple[float, float], ...]:
    points = []
    for index in range(THREAD_PROFILE_SAMPLES):
        local_angle_degrees = -180.0 + 360.0 * index / THREAD_PROFILE_SAMPLES
        absolute_angle = abs(local_angle_degrees)
        if absolute_angle <= crest_half_degrees:
            radius = major_radius
        else:
            radius = major_radius - (major_radius - root_radius) * (
                (absolute_angle - crest_half_degrees) / (180.0 - crest_half_degrees)
            )
        angle = math.radians(local_angle_degrees + phase_degrees)
        points.append((radius * math.cos(angle), radius * math.sin(angle)))
    return tuple(points)


def _lobed_loft(
    cq,
    *,
    lobes: int,
    shape_exponent: float,
    sections: tuple[tuple[float, float, float, float], ...],
):
    first_height, first_base, first_peak, first_phase = sections[0]
    workplane = (
        cq.Workplane("XY")
        .polyline(_lobed_points(first_base, first_peak, lobes, first_phase, shape_exponent))
        .close()
    )
    previous_height = first_height
    for height, base_radius, peak_radius, phase_degrees in sections[1:]:
        workplane = (
            workplane.workplane(offset=height - previous_height)
            .polyline(_lobed_points(base_radius, peak_radius, lobes, phase_degrees, shape_exponent))
            .close()
        )
        previous_height = height
    return workplane.loft(combine=True, ruled=True)


def _lobed_points(
    base_radius: float,
    peak_radius: float,
    lobes: int,
    phase_degrees: float,
    shape_exponent: float,
) -> tuple[tuple[float, float], ...]:
    points = []
    sample_count = lobes * 4
    phase = math.radians(phase_degrees)
    for index in range(sample_count):
        angle = index * 2.0 * math.pi / sample_count
        amplitude = ((1.0 + math.cos(lobes * (angle - phase))) / 2.0) ** shape_exponent
        radius = base_radius + (peak_radius - base_radius) * amplitude
        points.append((radius * math.cos(angle), radius * math.sin(angle)))
    return tuple(points)


def _sector_span_loft(
    cq,
    *,
    radius: float,
    center_degrees: float,
    sections: tuple[tuple[float, float], ...],
):
    workplane = (
        cq.Workplane("XY")
        .polyline(_fixed_sector_points(radius, center_degrees, sections[0][1]))
        .close()
    )
    previous_height = sections[0][0]
    for section_height, span_degrees in sections[1:]:
        workplane = (
            workplane.workplane(offset=section_height - previous_height)
            .polyline(_fixed_sector_points(radius, center_degrees, span_degrees))
            .close()
        )
        previous_height = section_height
    return workplane.loft(combine=True, ruled=False)


def _fixed_sector_points(
    radius: float, center_degrees: float, span_degrees: float
) -> tuple[tuple[float, float], ...]:
    points = [(0.0, 0.0)]
    for index in range(21):
        angle = math.radians(center_degrees - span_degrees / 2.0 + span_degrees * index / 20.0)
        points.append((radius * math.cos(angle), radius * math.sin(angle)))
    return tuple(points)


def _point_angle(point: tuple[float, float], center: tuple[float, float] = (0.0, 0.0)) -> float:
    return math.degrees(math.atan2(point[1] - center[1], point[0] - center[0]))


def _arc_midpoint(
    center: tuple[float, float], radius: float, start_degrees: float, end_degrees: float
) -> tuple[float, float]:
    middle_degrees = (start_degrees + end_degrees) / 2.0
    angle = math.radians(middle_degrees)
    return (center[0] + radius * math.cos(angle), center[1] + radius * math.sin(angle))


def _rotate_point(point: tuple[float, float], degrees: float) -> tuple[float, float]:
    angle = math.radians(degrees)
    return (
        point[0] * math.cos(angle) - point[1] * math.sin(angle),
        point[0] * math.sin(angle) + point[1] * math.cos(angle),
    )


def _sector_points(radius: float, start_degrees: float, end_degrees: float):
    steps = max(2, math.ceil(abs(end_degrees - start_degrees) / 5.0))
    points = [(0.0, 0.0)]
    for index in range(steps + 1):
        angle = math.radians(start_degrees + (end_degrees - start_degrees) * index / steps)
        points.append((radius * math.cos(angle), radius * math.sin(angle)))
    return tuple(points)


def _sector_prism(cq, *, radius: float, start_degrees: float, end_degrees: float, height: float):
    return (
        cq.Workplane("XY")
        .polyline(_sector_points(radius, start_degrees, end_degrees))
        .close()
        .extrude(height)
    )


def _circular_loft(cq, *, sections: tuple[tuple[float, float], ...]):
    workplane = cq.Workplane("XY").circle(sections[0][1])
    previous_height = sections[0][0]
    for height, radius in sections[1:]:
        workplane = workplane.workplane(offset=height - previous_height).circle(radius)
        previous_height = height
    return workplane.loft(combine=True, ruled=True)


def _annular_loft(
    cq,
    *,
    height: float,
    outer_bottom: float,
    outer_top: float,
    inner_bottom: float,
    inner_top: float,
):
    outer = _circular_loft(cq, sections=((0.0, outer_bottom), (height, outer_top)))
    inner = _circular_loft(cq, sections=((0.0, inner_bottom), (height, inner_top)))
    return outer.cut(inner)


def _validate_parameters(*, tube_width_mm: float, gap_mm: float) -> None:
    if not math.isfinite(tube_width_mm):
        raise ValueError("tube_width_mm must be finite.")
    if not math.isfinite(gap_mm):
        raise ValueError("gap_mm must be finite.")
    if tube_width_mm < MINIMUM_TUBE_WIDTH_MM:
        raise ValueError(f"tube_width_mm must be at least {MINIMUM_TUBE_WIDTH_MM:g} mm.")
    if gap_mm < MINIMUM_GAP_MM:
        raise ValueError(f"gap_mm must be at least {MINIMUM_GAP_MM:g} mm.")
    if gap_mm >= 7.0:
        raise ValueError("gap_mm must be less than 7 mm to leave printable shaft arms.")
