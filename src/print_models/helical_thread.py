"""Reusable lofted helical-thread geometry for printable CadQuery models."""

from __future__ import annotations

import math


def twisted_thread(
    cq,
    *,
    pitch_mm: float,
    root_radius_mm: float,
    major_radius_mm: float,
    crest_half_degrees: float,
    height_mm: float,
    profile_samples: int = 16,
    section_degrees: float = 30.0,
    right_hand: bool = True,
):
    """Build a solid helical thread from a rotating radial profile.

    The result includes the core through ``root_radius_mm``. Union it with a shaft for an
    external thread, or subtract it from a body to form a matching internal thread.
    """
    _validate_parameters(
        pitch_mm=pitch_mm,
        root_radius_mm=root_radius_mm,
        major_radius_mm=major_radius_mm,
        crest_half_degrees=crest_half_degrees,
        height_mm=height_mm,
        profile_samples=profile_samples,
        section_degrees=section_degrees,
    )

    axial_step_mm = pitch_mm * section_degrees / 360.0
    section_count = math.ceil(height_mm / axial_step_mm)
    section_heights = tuple(height_mm * index / section_count for index in range(section_count + 1))
    handedness = 1.0 if right_hand else -1.0

    workplane = (
        cq.Workplane("XY")
        .polyline(
            _thread_profile_points(
                root_radius_mm,
                major_radius_mm,
                crest_half_degrees,
                phase_degrees=0.0,
                profile_samples=profile_samples,
            )
        )
        .close()
    )
    previous_height_mm = 0.0
    for section_height_mm in section_heights[1:]:
        phase_degrees = handedness * 360.0 * section_height_mm / pitch_mm
        workplane = (
            workplane.workplane(offset=section_height_mm - previous_height_mm)
            .polyline(
                _thread_profile_points(
                    root_radius_mm,
                    major_radius_mm,
                    crest_half_degrees,
                    phase_degrees=phase_degrees,
                    profile_samples=profile_samples,
                )
            )
            .close()
        )
        previous_height_mm = section_height_mm

    return workplane.loft(combine=True, ruled=True)


def _thread_profile_points(
    root_radius_mm: float,
    major_radius_mm: float,
    crest_half_degrees: float,
    *,
    phase_degrees: float,
    profile_samples: int,
) -> tuple[tuple[float, float], ...]:
    points = []
    for index in range(profile_samples):
        local_angle_degrees = -180.0 + 360.0 * index / profile_samples
        absolute_angle_degrees = abs(local_angle_degrees)
        if absolute_angle_degrees <= crest_half_degrees:
            radius_mm = major_radius_mm
        else:
            radius_mm = major_radius_mm - (major_radius_mm - root_radius_mm) * (
                (absolute_angle_degrees - crest_half_degrees) / (180.0 - crest_half_degrees)
            )
        angle_radians = math.radians(local_angle_degrees + phase_degrees)
        points.append((radius_mm * math.cos(angle_radians), radius_mm * math.sin(angle_radians)))
    return tuple(points)


def _validate_parameters(
    *,
    pitch_mm: float,
    root_radius_mm: float,
    major_radius_mm: float,
    crest_half_degrees: float,
    height_mm: float,
    profile_samples: int,
    section_degrees: float,
) -> None:
    for name, value in (
        ("pitch_mm", pitch_mm),
        ("root_radius_mm", root_radius_mm),
        ("major_radius_mm", major_radius_mm),
        ("height_mm", height_mm),
        ("section_degrees", section_degrees),
    ):
        if not math.isfinite(value) or value <= 0:
            raise ValueError(f"{name} must be finite and positive.")
    if major_radius_mm <= root_radius_mm:
        raise ValueError("major_radius_mm must be greater than root_radius_mm.")
    if not math.isfinite(crest_half_degrees) or not 0 <= crest_half_degrees < 180:
        raise ValueError("crest_half_degrees must be finite and in the range [0, 180).")
    if profile_samples < 8:
        raise ValueError("profile_samples must be at least 8.")
    if section_degrees > 90:
        raise ValueError("section_degrees must not exceed 90 degrees.")
