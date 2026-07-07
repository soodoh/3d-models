"""Exact mesh replicas of the Printables Dutch Blitz card storage box files."""

from __future__ import annotations

import io
import math
import struct
from collections.abc import Mapping
from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile

NAME = "dutch_blitz_card_storage_box"
DESCRIPTION = "Exact mesh replica of Printables model 1246621, including container and lid."
PARAMETERS = {
    "part": "all",
}
PRINT_NOTES = (
    "Exports exact mesh geometry from the original Printables 3MF files. "
    "Use part=container or part=lid to export only one piece."
)
SUPPORTED_FORMATS = ("stl", "3mf")

_RESOURCE_PACKAGE = "print_models.assets.dutch_blitz_card_storage_box"
_PART_ASSETS = {
    "container": "DutchBlitzCardBox.3mf",
    "lid": "DutchBlitzCardBoxLid.3mf",
}
_PART_ALIASES = {
    "all": "all",
    "box": "container",
    "base": "container",
    "container": "container",
    "lid": "lid",
}


@dataclass(frozen=True)
class ThreeMfMesh:
    """A 3MF-backed mesh with the same export API used by the CLI."""

    asset_name: str

    def export(self, output_path: str) -> None:
        """Export the source 3MF directly or an equivalent binary STL mesh."""
        path = Path(output_path)
        suffix = path.suffix.lower()
        source_bytes = _read_asset(self.asset_name)

        if suffix == ".3mf":
            path.write_bytes(source_bytes)
            return

        if suffix == ".stl":
            triangles = _triangles_from_3mf(source_bytes)
            _write_binary_stl(path, triangles)
            return

        supported = ", ".join(SUPPORTED_FORMATS)
        raise ValueError(f"{NAME} supports only these exact mesh export formats: {supported}")


def build(part: str = "all") -> Mapping[str, ThreeMfMesh]:
    """Build one or both exact Dutch Blitz storage box mesh parts."""
    normalized_part = _normalize_part(part)

    if normalized_part == "all":
        return {name: ThreeMfMesh(asset_name) for name, asset_name in _PART_ASSETS.items()}

    return {normalized_part: ThreeMfMesh(_PART_ASSETS[normalized_part])}


def _normalize_part(part: str) -> str:
    normalized = part.strip().lower()

    try:
        return _PART_ALIASES[normalized]
    except KeyError as error:
        choices = ", ".join(sorted(_PART_ALIASES))
        raise ValueError(f"part must be one of: {choices}") from error


def _read_asset(asset_name: str) -> bytes:
    return files(_RESOURCE_PACKAGE).joinpath(asset_name).read_bytes()


def _triangles_from_3mf(source_bytes: bytes) -> list[tuple[Vector, Vector, Vector]]:
    with ZipFile(io.BytesIO(source_bytes)) as archive:
        root = ET.fromstring(archive.read("3D/3dmodel.model"))

    namespace = {"m": "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"}
    objects = root.find("m:resources", namespace)
    if objects is None:
        raise ValueError("3MF does not contain resources.")

    meshes: dict[str, tuple[list[Vector], list[tuple[int, int, int]]]] = {}
    for object_element in objects.findall("m:object", namespace):
        object_id = object_element.attrib["id"]
        mesh_element = object_element.find("m:mesh", namespace)
        if mesh_element is None:
            continue

        vertex_elements = mesh_element.findall("m:vertices/m:vertex", namespace)
        vertices = [
            (
                float(vertex.attrib["x"]),
                float(vertex.attrib["y"]),
                float(vertex.attrib["z"]),
            )
            for vertex in vertex_elements
        ]
        triangle_elements = mesh_element.findall("m:triangles/m:triangle", namespace)
        triangles = [
            (
                int(triangle.attrib["v1"]),
                int(triangle.attrib["v2"]),
                int(triangle.attrib["v3"]),
            )
            for triangle in triangle_elements
        ]
        meshes[object_id] = (vertices, triangles)

    build_element = root.find("m:build", namespace)
    if build_element is None:
        raise ValueError("3MF does not contain a build item.")

    exported_triangles: list[tuple[Vector, Vector, Vector]] = []
    for item_element in build_element.findall("m:item", namespace):
        object_id = item_element.attrib["objectid"]
        vertices, triangles = meshes[object_id]
        transform = _parse_transform(item_element.attrib.get("transform"))

        for v1, v2, v3 in triangles:
            exported_triangles.append(
                (
                    _transform_vertex(vertices[v1], transform),
                    _transform_vertex(vertices[v2], transform),
                    _transform_vertex(vertices[v3], transform),
                )
            )

    return exported_triangles


Vector = tuple[float, float, float]
Transform = tuple[
    float,
    float,
    float,
    float,
    float,
    float,
    float,
    float,
    float,
    float,
    float,
    float,
]
IDENTITY_TRANSFORM: Transform = (
    1.0,
    0.0,
    0.0,
    0.0,
    1.0,
    0.0,
    0.0,
    0.0,
    1.0,
    0.0,
    0.0,
    0.0,
)


def _parse_transform(raw_transform: str | None) -> Transform:
    if raw_transform is None:
        return IDENTITY_TRANSFORM

    values = tuple(float(value) for value in raw_transform.split())
    if len(values) != 12:
        raise ValueError(f"Expected a 12-value 3MF transform, got {raw_transform!r}")

    return values


def _transform_vertex(vertex: Vector, transform: Transform) -> Vector:
    x, y, z = vertex
    return (
        x * transform[0] + y * transform[3] + z * transform[6] + transform[9],
        x * transform[1] + y * transform[4] + z * transform[7] + transform[10],
        x * transform[2] + y * transform[5] + z * transform[8] + transform[11],
    )


def _write_binary_stl(path: Path, triangles: list[tuple[Vector, Vector, Vector]]) -> None:
    header = f"{NAME} exact 3MF mesh export".encode("ascii")[:80]
    header = header.ljust(80, b" ")

    with path.open("wb") as file:
        file.write(header)
        file.write(struct.pack("<I", len(triangles)))

        for triangle in triangles:
            normal = _normal(triangle)
            file.write(struct.pack("<3f", *normal))
            for vertex in triangle:
                file.write(struct.pack("<3f", *vertex))
            file.write(struct.pack("<H", 0))


def _normal(triangle: tuple[Vector, Vector, Vector]) -> Vector:
    a, b, c = triangle
    ab = (b[0] - a[0], b[1] - a[1], b[2] - a[2])
    ac = (c[0] - a[0], c[1] - a[1], c[2] - a[2])
    cross = (
        ab[1] * ac[2] - ab[2] * ac[1],
        ab[2] * ac[0] - ab[0] * ac[2],
        ab[0] * ac[1] - ab[1] * ac[0],
    )
    length = math.sqrt(cross[0] ** 2 + cross[1] ** 2 + cross[2] ** 2)

    if length == 0:
        return (0.0, 0.0, 0.0)

    return (cross[0] / length, cross[1] / length, cross[2] / length)
