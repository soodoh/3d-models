"""Validate the parametric Dutch Blitz rebuild against the reference Printables meshes."""

from __future__ import annotations

import io
import json
import struct
import tempfile
from importlib.resources import files
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile

import numpy as np

from print_models.models.dutch_blitz_card_storage_box_parametric import build

REFERENCE_PACKAGE = "print_models.assets.dutch_blitz_card_storage_box"
REFERENCES = {
    "container": "DutchBlitzCardBox.3mf",
    "lid": "DutchBlitzCardBoxLid.3mf",
}
SURFACE_SAMPLE_COUNT = 10_000
CANDIDATE_TRIANGLES = 512
SECTION_SAMPLE_STEPS = 16


def main() -> None:
    with tempfile.TemporaryDirectory() as directory:
        output_dir = Path(directory)
        generated = build()
        report = {}

        for part, reference_name in REFERENCES.items():
            output_path = output_dir / f"{part}.stl"
            generated[part].export(str(output_path))
            reference_triangles = _read_3mf_triangles(_reference_bytes(reference_name))
            generated_triangles = _read_binary_stl_triangles(output_path)
            report[part] = _compare_meshes(part, reference_triangles, generated_triangles)

    print(json.dumps(report, indent=2, sort_keys=True))


def _reference_bytes(name: str) -> bytes:
    return files(REFERENCE_PACKAGE).joinpath(name).read_bytes()


def _read_3mf_triangles(source_bytes: bytes) -> np.ndarray:
    with ZipFile(io.BytesIO(source_bytes)) as archive:
        root = ET.fromstring(archive.read("3D/3dmodel.model"))

    namespace = {"m": "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"}
    vertices = np.array(
        [
            (
                float(vertex.attrib["x"]),
                float(vertex.attrib["y"]),
                float(vertex.attrib["z"]),
            )
            for vertex in root.findall(".//m:vertices/m:vertex", namespace)
        ]
    )
    triangles = np.array(
        [
            (
                int(triangle.attrib["v1"]),
                int(triangle.attrib["v2"]),
                int(triangle.attrib["v3"]),
            )
            for triangle in root.findall(".//m:triangles/m:triangle", namespace)
        ]
    )
    return vertices[triangles]


def _read_binary_stl_triangles(path: Path) -> np.ndarray:
    data = path.read_bytes()
    triangle_count = struct.unpack("<I", data[80:84])[0]
    triangles = []

    for index in range(triangle_count):
        offset = 84 + index * 50 + 12
        vertices = []
        for vertex_index in range(3):
            start = offset + vertex_index * 12
            vertices.append(struct.unpack("<3f", data[start : start + 12]))
        triangles.append(vertices)

    return np.array(triangles)


def _compare_meshes(part: str, reference: np.ndarray, generated: np.ndarray) -> dict[str, object]:
    reference_vertices = reference.reshape(-1, 3)
    generated_vertices = generated.reshape(-1, 3)
    reference_size = np.ptp(reference_vertices, axis=0)
    generated_size = np.ptp(generated_vertices, axis=0)
    reference_area, reference_volume = _mesh_area_and_volume(reference)
    generated_area, generated_volume = _mesh_area_and_volume(generated)
    result: dict[str, object] = {
        "reference_bbox_size_mm": _round_vector(reference_size),
        "generated_bbox_size_mm": _round_vector(generated_size),
        "bbox_size_delta_mm": _round_vector(generated_size - reference_size),
        "reference_triangles": int(len(reference)),
        "generated_triangles": int(len(generated)),
        "surface_area_mm2": {
            "reference": round(reference_area, 3),
            "generated": round(generated_area, 3),
            "delta": round(generated_area - reference_area, 3),
        },
        "volume_mm3": {
            "reference": round(reference_volume, 3),
            "generated": round(generated_volume, 3),
            "delta": round(generated_volume - reference_volume, 3),
        },
        "feature_checks": _feature_checks(part, reference, generated),
    }

    try:
        from scipy.spatial import cKDTree
    except ImportError:
        return result

    reference_aligned = _align_for_shape_check(reference)
    generated_aligned = _align_for_shape_check(generated)
    reference_sample = _sample_surface(reference_aligned, seed=1)
    generated_sample = _sample_surface(generated_aligned, seed=2)
    generated_to_reference = _point_to_mesh_distances(generated_sample, reference_aligned)
    reference_to_generated = _point_to_mesh_distances(reference_sample, generated_aligned)
    result["sampled_point_to_triangle_distance_mm"] = {
        "generated_to_reference": _distance_stats(generated_to_reference),
        "reference_to_generated": _distance_stats(reference_to_generated),
        "samples_per_mesh": SURFACE_SAMPLE_COUNT,
        "candidate_triangles_per_sample": CANDIDATE_TRIANGLES,
        "note": "Sampled points measured to nearby triangle surfaces, not just sampled vertices.",
    }
    result["multi_section_distance_mm"] = _multi_section_checks(part, reference, generated)
    return result


def _feature_checks(part: str, reference: np.ndarray, generated: np.ndarray) -> dict[str, object]:
    if part == "lid":
        return {
            "side_dovetail_profile_x0": _compare_section_profile(
                reference,
                generated,
                section_axis=0,
                section_value=0.0,
                use_local_z=True,
                point_filter=lambda points: (points[:, 0] > 28.0) & (points[:, 1] > 0.0),
            ),
            "top_handle_floor": _compare_horizontal_feature(reference, generated, 1.076608, "+Z"),
            "text_floor": _compare_horizontal_feature(reference, generated, 2.676608, "+Z"),
            "bottom_click_groove_ceiling": _compare_horizontal_feature(
                reference, generated, 0.8, "-Z"
            ),
        }

    reference_x_faces = _major_vertical_x_faces(reference)
    generated_x_faces = _major_vertical_x_faces(generated)
    return {
        "back_stop_profile_x_minus_60": _compare_section_profile(
            reference,
            generated,
            section_axis=0,
            section_value=-60.0,
            point_filter=lambda points: (points[:, 0] > 25.0) & (points[:, 1] > 88.0),
        ),
        "side_dovetail_profile_x0": _compare_section_profile(
            reference,
            generated,
            section_axis=0,
            section_value=0.0,
            point_filter=lambda points: (points[:, 0] > 25.0) & (points[:, 1] > 88.0),
        ),
        "mid_length_section_y0": _compare_section_profile(
            reference,
            generated,
            section_axis=1,
            section_value=0.0,
            point_filter=lambda points: points[:, 1] > 0.0,
        ),
        "interior_floor_section_z4": _compare_section_profile(
            reference,
            generated,
            section_axis=2,
            section_value=4.0,
            point_filter=lambda points: np.full(len(points), True),
        ),
        "divider_top_section_z70_4": _compare_section_profile(
            reference,
            generated,
            section_axis=2,
            section_value=70.4,
            point_filter=lambda points: np.full(len(points), True),
        ),
        "right_lid_track_floor": _compare_absolute_horizontal_feature(
            reference, generated, 88.723392, "+Z", x_range=(57.0, 62.0)
        ),
        "click_lug_top": _compare_absolute_horizontal_feature(
            reference, generated, 89.323392, "+Z"
        ),
        "divider_straight_face_x_mm": {
            "reference": reference_x_faces,
            "generated": generated_x_faces,
        },
        "slot_straight_opening_mm": {
            "reference": _slot_openings(reference_x_faces),
            "generated": _slot_openings(generated_x_faces),
        },
    }


def _mesh_area_and_volume(triangles: np.ndarray) -> tuple[float, float]:
    cross = np.cross(triangles[:, 1] - triangles[:, 0], triangles[:, 2] - triangles[:, 0])
    area = float(np.linalg.norm(cross, axis=1).sum() / 2.0)
    signed_volume = np.einsum("ij,ij->i", triangles[:, 0], cross).sum() / 6.0
    return area, abs(float(signed_volume))



def _compare_section_profile(
    reference: np.ndarray,
    generated: np.ndarray,
    *,
    section_axis: int,
    section_value: float,
    point_filter,
    use_local_z: bool = False,
) -> dict[str, object]:
    reference_points = _section_sample_points(
        reference, section_axis, section_value, use_local_z=use_local_z
    )
    generated_points = _section_sample_points(
        generated, section_axis, section_value, use_local_z=use_local_z
    )
    reference_points = reference_points[point_filter(reference_points)]
    generated_points = generated_points[point_filter(generated_points)]

    result: dict[str, object] = {
        "reference_bbox": _section_bbox(reference_points),
        "generated_bbox": _section_bbox(generated_points),
    }
    if len(reference_points) == 0 or len(generated_points) == 0:
        result["found"] = False
        return result

    try:
        from scipy.spatial import cKDTree
    except ImportError:
        result["found"] = True
        return result

    generated_to_reference, _ = cKDTree(reference_points).query(generated_points, k=1)
    reference_to_generated, _ = cKDTree(generated_points).query(reference_points, k=1)
    result.update(
        {
            "found": True,
            "generated_to_reference_mm": _distance_stats(generated_to_reference),
            "reference_to_generated_mm": _distance_stats(reference_to_generated),
        }
    )
    return result


def _section_sample_points(
    triangles: np.ndarray, axis: int, value: float, *, use_local_z: bool
) -> np.ndarray:
    points: list[np.ndarray] = []
    z_min = float(triangles.reshape(-1, 3)[:, 2].min())

    for triangle in triangles:
        intersections = []
        for first_index, second_index in ((0, 1), (1, 2), (2, 0)):
            first = triangle[first_index]
            second = triangle[second_index]
            first_delta = first[axis] - value
            second_delta = second[axis] - value

            if abs(first_delta) < 1e-7 and abs(second_delta) < 1e-7:
                continue
            if abs(first_delta) < 1e-7:
                intersections.append(np.delete(first, axis))
            if first_delta * second_delta < 0:
                amount = abs(first_delta) / (abs(first_delta) + abs(second_delta))
                intersections.append(np.delete(first + (second - first) * amount, axis))
            elif abs(second_delta) < 1e-7:
                intersections.append(np.delete(second, axis))

        if len(intersections) < 2:
            continue

        start = intersections[0]
        end = intersections[1]
        for amount in np.linspace(0.0, 1.0, SECTION_SAMPLE_STEPS):
            point = start + (end - start) * amount
            if use_local_z:
                point = point.copy()
                point[-1] -= z_min
            points.append(point)

    if not points:
        return np.empty((0, 2))

    return np.array(points)


def _section_bbox(points: np.ndarray) -> dict[str, object]:
    if len(points) == 0:
        return {"found": False}

    return {
        "found": True,
        "min": _round_vector(points.min(axis=0)),
        "max": _round_vector(points.max(axis=0)),
        "size": _round_vector(np.ptp(points, axis=0)),
    }



def _compare_horizontal_feature(
    reference: np.ndarray, generated: np.ndarray, local_z: float, normal: str
) -> dict[str, object]:
    return {
        "reference": _horizontal_feature(reference, local_z, normal, use_local_z=True),
        "generated": _horizontal_feature(generated, local_z, normal, use_local_z=True),
    }


def _compare_absolute_horizontal_feature(
    reference: np.ndarray,
    generated: np.ndarray,
    z: float,
    normal: str,
    x_range: tuple[float, float] | None = None,
) -> dict[str, object]:
    return {
        "reference": _horizontal_feature(reference, z, normal, use_local_z=False, x_range=x_range),
        "generated": _horizontal_feature(generated, z, normal, use_local_z=False, x_range=x_range),
    }


def _horizontal_feature(
    triangles: np.ndarray,
    z: float,
    normal: str,
    *,
    use_local_z: bool,
    x_range: tuple[float, float] | None = None,
) -> dict[str, object]:
    normals, areas, centroids = _triangle_measurements(triangles)
    if use_local_z:
        z_values = centroids[:, 2] - triangles.reshape(-1, 3)[:, 2].min()
    else:
        z_values = centroids[:, 2]
    sign = 1.0 if normal == "+Z" else -1.0
    mask = (normals[:, 2] * sign > 0.99) & np.isclose(z_values, z, atol=0.015)
    if x_range is not None:
        mask &= (centroids[:, 0] >= x_range[0]) & (centroids[:, 0] <= x_range[1])

    if not mask.any():
        return {"found": False}

    vertices = _aligned_xy(triangles[mask].reshape(-1, 3))
    return {
        "found": True,
        "area_mm2": round(float(areas[mask].sum()), 3),
        "bbox_xy_centered_mm": {
            "min": _round_vector(vertices[:, :2].min(axis=0)),
            "max": _round_vector(vertices[:, :2].max(axis=0)),
            "size": _round_vector(np.ptp(vertices[:, :2], axis=0)),
        },
    }


def _major_vertical_x_faces(triangles: np.ndarray) -> list[float]:
    normals, areas, centroids = _triangle_measurements(triangles)
    mask = np.abs(normals[:, 0]) > 0.99
    planes: dict[float, float] = {}

    for x_value, area in zip(np.round(centroids[mask, 0], 3), areas[mask]):
        if abs(x_value) < 50.0:
            planes[x_value] = planes.get(x_value, 0.0) + float(area)

    return sorted(x for x, area in planes.items() if area > 1_000.0)


def _slot_openings(x_faces: list[float]) -> list[float]:
    paired_faces = list(zip(x_faces[1::2], x_faces[2::2]))
    return [round(right - left, 3) for left, right in paired_faces]



def _triangle_measurements(triangles: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    ab = triangles[:, 1] - triangles[:, 0]
    ac = triangles[:, 2] - triangles[:, 0]
    cross = np.cross(ab, ac)
    lengths = np.linalg.norm(cross, axis=1)
    normals = cross / np.where(lengths[:, None] == 0, 1, lengths[:, None])
    areas = lengths / 2.0
    centroids = triangles.mean(axis=1)
    return normals, areas, centroids


def _aligned_xy(vertices: np.ndarray) -> np.ndarray:
    center = (vertices.min(axis=0) + vertices.max(axis=0)) / 2.0
    aligned = vertices.copy()
    aligned[:, 0] -= center[0]
    aligned[:, 1] -= center[1]
    return aligned


def _align_for_shape_check(triangles: np.ndarray) -> np.ndarray:
    vertices = triangles.reshape(-1, 3)
    center = (vertices.min(axis=0) + vertices.max(axis=0)) / 2.0
    aligned = triangles - center
    aligned[:, :, 2] -= aligned.reshape(-1, 3)[:, 2].min()
    return aligned


def _sample_surface(triangles: np.ndarray, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    ab = triangles[:, 1] - triangles[:, 0]
    ac = triangles[:, 2] - triangles[:, 0]
    area = np.linalg.norm(np.cross(ab, ac), axis=1) / 2.0
    triangle_index = rng.choice(len(triangles), size=SURFACE_SAMPLE_COUNT, p=area / area.sum())
    first = np.sqrt(rng.random(SURFACE_SAMPLE_COUNT))
    second = rng.random(SURFACE_SAMPLE_COUNT)
    selected = triangles[triangle_index]

    return (
        (1.0 - first)[:, None] * selected[:, 0]
        + (first * (1.0 - second))[:, None] * selected[:, 1]
        + (first * second)[:, None] * selected[:, 2]
    )


def _point_to_mesh_distances(points: np.ndarray, triangles: np.ndarray) -> np.ndarray:
    from scipy.spatial import cKDTree

    centroids = triangles.mean(axis=1)
    triangle_tree = cKDTree(centroids)
    _, nearest_indices = triangle_tree.query(points, k=CANDIDATE_TRIANGLES)
    nearest_indices = np.atleast_2d(nearest_indices)
    distances = np.empty(len(points))

    for start in range(0, len(points), 512):
        stop = min(start + 512, len(points))
        chunk_points = points[start:stop]
        chunk_triangles = triangles[nearest_indices[start:stop]]
        repeated_points = np.repeat(chunk_points[:, None, :], CANDIDATE_TRIANGLES, axis=1)
        distances[start:stop] = np.sqrt(
            _point_triangle_distance_squared(repeated_points, chunk_triangles).min(axis=1)
        )

    return distances


def _point_triangle_distance_squared(points: np.ndarray, triangles: np.ndarray) -> np.ndarray:
    a = triangles[:, :, 0]
    b = triangles[:, :, 1]
    c = triangles[:, :, 2]
    ab = b - a
    ac = c - a
    ap = points - a
    d1 = _dot(ab, ap)
    d2 = _dot(ac, ap)
    closest = np.zeros(points.shape[:-1] + (3,))
    handled = np.zeros(points.shape[:-1], dtype=bool)

    mask = (d1 <= 0.0) & (d2 <= 0.0)
    closest[mask] = a[mask]
    handled |= mask

    bp = points - b
    d3 = _dot(ab, bp)
    d4 = _dot(ac, bp)
    mask = (d3 >= 0.0) & (d4 <= d3) & ~handled
    closest[mask] = b[mask]
    handled |= mask

    vc = d1 * d4 - d3 * d2
    mask = (vc <= 0.0) & (d1 >= 0.0) & (d3 <= 0.0) & ~handled
    v = d1 / (d1 - d3)
    closest[mask] = a[mask] + v[mask, None] * ab[mask]
    handled |= mask

    cp = points - c
    d5 = _dot(ab, cp)
    d6 = _dot(ac, cp)
    mask = (d6 >= 0.0) & (d5 <= d6) & ~handled
    closest[mask] = c[mask]
    handled |= mask

    vb = d5 * d2 - d1 * d6
    mask = (vb <= 0.0) & (d2 >= 0.0) & (d6 <= 0.0) & ~handled
    w = d2 / (d2 - d6)
    closest[mask] = a[mask] + w[mask, None] * ac[mask]
    handled |= mask

    va = d3 * d6 - d5 * d4
    mask = (va <= 0.0) & ((d4 - d3) >= 0.0) & ((d5 - d6) >= 0.0) & ~handled
    w = (d4 - d3) / ((d4 - d3) + (d5 - d6))
    closest[mask] = b[mask] + w[mask, None] * (c - b)[mask]
    handled |= mask

    denominator = va + vb + vc
    v = vb / denominator
    w = vc / denominator
    mask = ~handled
    closest[mask] = a[mask] + ab[mask] * v[mask, None] + ac[mask] * w[mask, None]

    return _dot(points - closest, points - closest)


def _dot(left: np.ndarray, right: np.ndarray) -> np.ndarray:
    return np.einsum("...i,...i->...", left, right)


def _multi_section_checks(
    part: str, reference: np.ndarray, generated: np.ndarray
) -> list[dict[str, object]]:
    if part == "lid":
        sections = [(0, 0.0), (1, 0.0)]
        sections.extend((2, z) for z in (0.8, 1.076608, 2.676608))
    else:
        sections = [
            (0, -60.0),
            (0, -30.0),
            (0, 0.0),
            (0, 30.0),
            (0, 60.0),
            (1, -29.0),
            (1, 0.0),
            (1, 29.0),
            (2, 4.0),
            (2, 37.243),
            (2, 70.4),
            (2, 88.723392),
        ]

    results = []
    for axis, value in sections:
        reference_points = _section_sample_points(reference, axis, value, use_local_z=False)
        generated_points = _section_sample_points(generated, axis, value, use_local_z=False)
        if len(reference_points) == 0 or len(generated_points) == 0:
            results.append({"axis": axis, "value": value, "found": False})
            continue

        from scipy.spatial import cKDTree

        generated_to_reference, _ = cKDTree(reference_points).query(generated_points, k=1)
        reference_to_generated, _ = cKDTree(generated_points).query(reference_points, k=1)
        results.append(
            {
                "axis": axis,
                "value": value,
                "found": True,
                "generated_to_reference": _distance_stats(generated_to_reference),
                "reference_to_generated": _distance_stats(reference_to_generated),
            }
        )

    return results


def _distance_stats(values: np.ndarray) -> dict[str, float]:
    return {
        "mean": round(float(values.mean()), 4),
        "p95": round(float(np.quantile(values, 0.95)), 4),
        "max": round(float(values.max()), 4),
    }


def _round_vector(values: np.ndarray) -> list[float]:
    return [round(float(value), 6) for value in values]


if __name__ == "__main__":
    main()
