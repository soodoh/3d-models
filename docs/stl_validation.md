# STL baseline validation approach

This project treats downloaded STL files as validation baselines only. CadQuery model scripts must
construct geometry parametrically and must not import the baseline mesh.

## Recommended authoritative checks

1. **Coordinate and orientation check**: confirm both meshes share the same coordinate frame, units,
   bounding-box min/max, and major section planes before any distance metric is trusted.
2. **Mesh scalar checks**: compare watertightness/manifoldness when tooling is available, triangle
   count, bounding-box size, surface area, and enclosed volume.
3. **Bidirectional distance checks**: use both directions, not just generated-to-source. One-sided
   Hausdorff-like distances are not symmetric; a missing feature can appear only in the
   source-to-generated direction, while an extra generated feature appears in the reverse direction.
4. **Dense surface sampling**: MeshLab's Hausdorff workflow describes sampling points on one mesh and
   searching closest points on the other mesh, with results reported as min/max/mean/RMS and relative
   to the bounding-box diagonal. Use high sample counts and repeat both directions.
5. **Point-to-mesh distance with octrees**: CloudCompare's C2M routines compute point-cloud to mesh
   distances against mesh triangles with octree acceleration. For final sign-off, sample each STL to a
   dense point cloud and run CloudCompare C2M in both directions, recording RMS, 95%, 99%, and max.
6. **Visual error maps and cross sections**: inspect colorized distance fields and critical XY/XZ/YZ
   sections so a low average error does not hide localized feature mismatches.

## Local lightweight validator

`scripts/validate_stl_match.py` provides a deterministic, dependency-light check for iteration:

```bash
.venv/bin/python scripts/validate_stl_match.py \
  exports/source/five_crowns/fiveCrownsCaseBody00.stl \
  build/five_crowns_current/five_crowns_deck_box_container.stl \
  --samples 120000 \
  --json build/five_crowns_validation/container_report.json
```

The script reports:

- triangle count
- bounding-box size and delta
- surface-area and volume deltas
- source-to-candidate, candidate-to-source, and symmetric sampled surface distances

This script is sufficient for fast CadQuery fitting loops. For publication-quality claims, verify with
CloudCompare C2M or MeshLab/Metro Hausdorff using dense samples and archived settings.

## Sources

- CloudCompare Core `DistanceComputationTools`: cloud-cloud and cloud-mesh distance algorithms,
  RMS/95%/99%/max estimators, point-to-triangle support.
- MeshLab/Metro Hausdorff workflow: one-sided distances, sampling dependence, mean/RMS/max reporting,
  and colorized quality-field inspection.
