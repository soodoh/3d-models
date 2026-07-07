#!/usr/bin/env python3
"""Compare a generated STL against a source STL baseline.

This intentionally does not import the source STL into CadQuery; it only uses the STL as a
validation oracle after the generated model has been exported.
"""

from __future__ import annotations

import argparse
import json
import math
import struct
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree


@dataclass(frozen=True)
class MeshStats:
    triangles: int
    area_mm2: float
    volume_mm3: float
    bbox_min: list[float]
    bbox_max: list[float]
    bbox_size: list[float]


@dataclass(frozen=True)
class DistanceStats:
    mean_mm: float
    rms_mm: float
    p95_mm: float
    p99_mm: float
    max_mm: float


@dataclass(frozen=True)
class PairReport:
    source: str
    candidate: str
    source_stats: MeshStats
    candidate_stats: MeshStats
    bbox_size_delta_mm: list[float]
    area_delta_percent: float
    volume_delta_percent: float
    source_to_candidate: DistanceStats
    candidate_to_source: DistanceStats
    symmetric: DistanceStats


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="Baseline STL path.")
    parser.add_argument("candidate", type=Path, help="Generated STL path.")
    parser.add_argument(
        "--samples",
        type=int,
        default=120_000,
        help="Surface samples per mesh for distance estimates. Defaults to 120000.",
    )
    parser.add_argument("--seed", type=int, default=7, help="Deterministic sample seed.")
    parser.add_argument(
        "--neighbors",
        type=int,
        default=48,
        help="Nearest STL vertices to expand into candidate triangles per sample.",
    )
    parser.add_argument("--json", type=Path, help="Optional path to write JSON report.")
    args = parser.parse_args()

    report = compare(
        args.source,
        args.candidate,
        sample_count=args.samples,
        seed=args.seed,
        neighbors=args.neighbors,
    )
    print_report(report)

    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(asdict(report), indent=2) + "\n")


def compare(
    source: Path,
    candidate: Path,
    *,
    sample_count: int,
    seed: int,
    neighbors: int,
) -> PairReport:
    source_tris = read_stl_triangles(source)
    candidate_tris = read_stl_triangles(candidate)
    source_stats = mesh_stats(source_tris)
    candidate_stats = mesh_stats(candidate_tris)

    source_points = sample_surface(source_tris, sample_count, seed=seed)
    candidate_points = sample_surface(candidate_tris, sample_count, seed=seed + 1)
    # The default report uses symmetric dense surface sampling. For external, more rigorous
    # point-to-mesh runs, use CloudCompare C2M or MeshLab/Metro as documented in docs/.
    source_to_candidate_distances = cKDTree(candidate_points).query(source_points, k=1)[0]
    candidate_to_source_distances = cKDTree(source_points).query(candidate_points, k=1)[0]
    symmetric_distances = np.concatenate(
        [source_to_candidate_distances, candidate_to_source_distances]
    )

    return PairReport(
        source=str(source),
        candidate=str(candidate),
        source_stats=source_stats,
        candidate_stats=candidate_stats,
        bbox_size_delta_mm=(
            np.array(candidate_stats.bbox_size) - np.array(source_stats.bbox_size)
        ).tolist(),
        area_delta_percent=percent_delta(candidate_stats.area_mm2, source_stats.area_mm2),
        volume_delta_percent=percent_delta(candidate_stats.volume_mm3, source_stats.volume_mm3),
        source_to_candidate=distance_stats(source_to_candidate_distances),
        candidate_to_source=distance_stats(candidate_to_source_distances),
        symmetric=distance_stats(symmetric_distances),
    )


def read_stl_triangles(path: Path) -> np.ndarray:
    data = path.read_bytes()
    if len(data) < 84:
        return read_ascii_stl(path)

    triangle_count = struct.unpack("<I", data[80:84])[0]
    expected_binary_size = 84 + triangle_count * 50
    if expected_binary_size == len(data):
        dtype = np.dtype([("normal", "<f4", 3), ("vertices", "<f4", (3, 3)), ("attr", "<u2")])
        triangles = np.frombuffer(data, dtype=dtype, offset=84, count=triangle_count)[
            "vertices"
        ]
        return triangles.astype(np.float64)

    return read_ascii_stl(path)


def read_ascii_stl(path: Path) -> np.ndarray:
    vertices: list[list[float]] = []
    for line in path.read_text(errors="ignore").splitlines():
        stripped = line.strip()
        if not stripped.startswith("vertex "):
            continue
        _, x, y, z = stripped.split()
        vertices.append([float(x), float(y), float(z)])

    if len(vertices) % 3 != 0 or not vertices:
        raise ValueError(f"{path} is not a readable binary or ASCII STL")

    return np.array(vertices, dtype=np.float64).reshape((-1, 3, 3))


def mesh_stats(triangles: np.ndarray) -> MeshStats:
    vertices = triangles.reshape((-1, 3))
    bbox_min = vertices.min(axis=0)
    bbox_max = vertices.max(axis=0)
    cross = np.cross(triangles[:, 1] - triangles[:, 0], triangles[:, 2] - triangles[:, 0])
    area = np.linalg.norm(cross, axis=1).sum() / 2.0
    volume = abs(
        np.einsum("ij,ij->i", triangles[:, 0], np.cross(triangles[:, 1], triangles[:, 2])).sum()
        / 6.0
    )
    return MeshStats(
        triangles=int(len(triangles)),
        area_mm2=float(area),
        volume_mm3=float(volume),
        bbox_min=bbox_min.tolist(),
        bbox_max=bbox_max.tolist(),
        bbox_size=(bbox_max - bbox_min).tolist(),
    )


def sample_surface(triangles: np.ndarray, sample_count: int, *, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    cross = np.cross(triangles[:, 1] - triangles[:, 0], triangles[:, 2] - triangles[:, 0])
    areas = np.linalg.norm(cross, axis=1) / 2.0
    probabilities = areas / areas.sum()
    indices = rng.choice(len(triangles), size=sample_count, p=probabilities)
    selected = triangles[indices]

    # Uniform barycentric samples over triangles.
    r1 = np.sqrt(rng.random(sample_count))
    r2 = rng.random(sample_count)
    return (
        (1.0 - r1)[:, np.newaxis] * selected[:, 0]
        + (r1 * (1.0 - r2))[:, np.newaxis] * selected[:, 1]
        + (r1 * r2)[:, np.newaxis] * selected[:, 2]
    )


def points_to_mesh_distances(
    points: np.ndarray,
    triangles: np.ndarray,
    *,
    neighbors: int,
    chunk_size: int = 2_000,
) -> np.ndarray:
    # Query nearby STL vertices, then test the triangles that contain those vertices. This is
    # much closer to CloudCompare/MeshLab point-to-mesh logic than point-cloud-to-point-cloud
    # sampling, while staying dependency-light for this CadQuery workspace.
    vertices = triangles.reshape((-1, 3))
    tree = cKDTree(vertices)
    distances = np.empty(len(points), dtype=np.float64)
    neighbor_count = min(neighbors, len(vertices))

    for start in range(0, len(points), chunk_size):
        stop = min(start + chunk_size, len(points))
        chunk = points[start:stop]
        _, vertex_indices = tree.query(chunk, k=neighbor_count)
        if neighbor_count == 1:
            vertex_indices = vertex_indices[:, np.newaxis]

        for offset, nearby_vertices in enumerate(vertex_indices):
            triangle_indices = np.unique(nearby_vertices // 3)
            candidate_triangles = triangles[triangle_indices][np.newaxis, :, :, :]
            point = chunk[offset : offset + 1]
            distances[start + offset] = point_triangle_distances(point, candidate_triangles).min()

    return distances


def point_triangle_distances(points: np.ndarray, triangles: np.ndarray) -> np.ndarray:
    # Vectorized implementation of the closest-point regions from
    # Christer Ericson, Real-Time Collision Detection, section 5.1.5.
    p = points[:, np.newaxis, :]
    a = triangles[:, :, 0]
    b = triangles[:, :, 1]
    c = triangles[:, :, 2]
    ab = b - a
    ac = c - a
    ap = p - a

    d1 = np.einsum("ijk,ijk->ij", ab, ap)
    d2 = np.einsum("ijk,ijk->ij", ac, ap)
    distances_sq = np.full(d1.shape, np.inf, dtype=np.float64)

    mask = (d1 <= 0.0) & (d2 <= 0.0)
    distances_sq[mask] = squared_norm(p - a)[mask]

    bp = p - b
    d3 = np.einsum("ijk,ijk->ij", ab, bp)
    d4 = np.einsum("ijk,ijk->ij", ac, bp)
    mask = (d3 >= 0.0) & (d4 <= d3)
    distances_sq[mask] = squared_norm(p - b)[mask]

    vc = d1 * d4 - d3 * d2
    mask = (vc <= 0.0) & (d1 >= 0.0) & (d3 <= 0.0)
    v = d1 / (d1 - d3)
    projection = a + v[:, :, np.newaxis] * ab
    distances_sq[mask] = squared_norm(p - projection)[mask]

    cp = p - c
    d5 = np.einsum("ijk,ijk->ij", ab, cp)
    d6 = np.einsum("ijk,ijk->ij", ac, cp)
    mask = (d6 >= 0.0) & (d5 <= d6)
    distances_sq[mask] = squared_norm(p - c)[mask]

    vb = d5 * d2 - d1 * d6
    mask = (vb <= 0.0) & (d2 >= 0.0) & (d6 <= 0.0)
    w = d2 / (d2 - d6)
    projection = a + w[:, :, np.newaxis] * ac
    distances_sq[mask] = squared_norm(p - projection)[mask]

    va = d3 * d6 - d5 * d4
    mask = (va <= 0.0) & ((d4 - d3) >= 0.0) & ((d5 - d6) >= 0.0)
    w = (d4 - d3) / ((d4 - d3) + (d5 - d6))
    projection = b + w[:, :, np.newaxis] * (c - b)
    distances_sq[mask] = squared_norm(p - projection)[mask]

    mask = np.isinf(distances_sq)
    denom = va + vb + vc
    v = vb / denom
    w = vc / denom
    projection = a + ab * v[:, :, np.newaxis] + ac * w[:, :, np.newaxis]
    distances_sq[mask] = squared_norm(p - projection)[mask]
    return np.sqrt(np.maximum(distances_sq, 0.0))


def squared_norm(vectors: np.ndarray) -> np.ndarray:
    return np.einsum("ijk,ijk->ij", vectors, vectors)


def distance_stats(distances: np.ndarray) -> DistanceStats:
    return DistanceStats(
        mean_mm=float(distances.mean()),
        rms_mm=float(math.sqrt(np.square(distances).mean())),
        p95_mm=float(np.percentile(distances, 95)),
        p99_mm=float(np.percentile(distances, 99)),
        max_mm=float(distances.max()),
    )


def percent_delta(candidate: float, source: float) -> float:
    if source == 0:
        return 0.0
    return (candidate - source) / source * 100.0


def print_report(report: PairReport) -> None:
    print(f"Source:    {report.source}")
    print(f"Candidate: {report.candidate}")
    print()
    print("Mesh statistics")
    print(f"  source triangles:    {report.source_stats.triangles}")
    print(f"  candidate triangles: {report.candidate_stats.triangles}")
    print(f"  bbox source:         {format_vector(report.source_stats.bbox_size)} mm")
    print(f"  bbox candidate:      {format_vector(report.candidate_stats.bbox_size)} mm")
    print(f"  bbox delta:          {format_vector(report.bbox_size_delta_mm)} mm")
    print(f"  area delta:          {report.area_delta_percent:+.3f}%")
    print(f"  volume delta:        {report.volume_delta_percent:+.3f}%")
    print()
    print("Sampled bidirectional surface distances")
    print_distance("source → candidate", report.source_to_candidate)
    print_distance("candidate → source", report.candidate_to_source)
    print_distance("symmetric", report.symmetric)


def print_distance(label: str, stats: DistanceStats) -> None:
    print(
        f"  {label:20} mean={stats.mean_mm:.4f} mm "
        f"rms={stats.rms_mm:.4f} mm p95={stats.p95_mm:.4f} mm "
        f"p99={stats.p99_mm:.4f} mm max={stats.max_mm:.4f} mm"
    )


def format_vector(values: list[float]) -> str:
    return "[" + ", ".join(f"{value:.4f}" for value in values) + "]"


if __name__ == "__main__":
    main()
