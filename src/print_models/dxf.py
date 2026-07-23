"""Shared helpers for deterministic extrusion of fixed DXF regions."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path


DxfRegion = tuple[int, tuple[int, ...]]


def extrude_dxf_regions(
    cq,
    *,
    path: Path,
    height: float,
    regions: Sequence[DxfRegion],
):
    """Extrude explicitly grouped DXF wires into valid solids.

    Fixed logo assets can contain nested islands that CadQuery cannot infer from a flat
    ``wires().toPending()`` selection. Each region identifies one outer wire and its hole
    wires; nested islands are represented as their own regions.
    """
    if height <= 0:
        raise ValueError("DXF extrusion height must be positive.")
    if not regions:
        raise ValueError("DXF extrusion requires at least one region.")

    wires = cq.importers.importDXF(str(path)).wires().vals()
    wire_count = len(wires)
    used_indices = [
        index
        for outer_index, hole_indices in regions
        for index in (outer_index, *hole_indices)
    ]
    if len(used_indices) != len(set(used_indices)):
        raise ValueError(f"DXF region map for {path.name} repeats a wire index.")
    if any(index < 0 or index >= wire_count for index in used_indices):
        raise ValueError(
            f"DXF region map for {path.name} references a missing wire; "
            f"asset contains {wire_count} wires."
        )
    if set(used_indices) != set(range(wire_count)):
        raise ValueError(
            f"DXF region map for {path.name} does not account for all {wire_count} wires."
        )

    solids = []
    for outer_index, hole_indices in regions:
        face = cq.Face.makeFromWires(
            wires[outer_index],
            [wires[index] for index in hole_indices],
        )
        if not face.isValid():
            raise ValueError(
                f"DXF region beginning with wire {outer_index} in {path.name} is invalid."
            )
        solid = cq.Workplane("XY").newObject([face]).extrude(height).val()
        if not solid.isValid():
            raise ValueError(
                f"DXF region beginning with wire {outer_index} in {path.name} "
                "did not extrude to a valid solid."
            )
        solids.append(solid)

    compound = cq.Compound.makeCompound(solids)
    return cq.Workplane("XY").newObject([compound])


def union_dxf_regions(cq, *, base, regions):
    """Union every disconnected DXF region into a supporting base."""
    solids = regions.solids().vals()
    if not solids:
        raise ValueError("DXF region union requires at least one solid.")

    result = base
    for solid in solids:
        result = result.union(cq.Workplane("XY").newObject([solid]))
    return result
