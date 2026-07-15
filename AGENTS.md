# AGENTS.md

## Repository purpose

This repository builds parametric, 3D-printable models with Python 3.11 and CadQuery. Keep model source editable and deterministic; dimensions are in millimeters unless explicitly documented otherwise.

## Setup and common commands

Run commands from the repository root.

```bash
python3.11 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -e .

MODEL=gridfinity_shims
.venv/bin/generate-model list
.venv/bin/generate-model describe "$MODEL"
.venv/bin/python preview.py "$MODEL" --no-preview
.venv/bin/python preview.py "$MODEL" --views isometric,top,front,right
.venv/bin/python -m unittest discover -s tests
```

For a focused test module, use:

```bash
.venv/bin/python -m unittest tests.test_gridfinity_box
```

## Model export policy

- **Generate model deliverables only as STL files.** Do not export STEP, 3MF, SVG, or another model format, even though the CLI supports them.
- Use an explicit STL format so tool defaults cannot produce additional formats:

```bash
MODEL=gridfinity_shims
.venv/bin/generate-model export "$MODEL" --format stl --out-dir build
.venv/bin/generate-model export --all --format stl --out-dir build
```

- Do not run bare `make export`, `make export-all`, or `make all`; the Makefile currently defaults to both STL and STEP. Ignore README examples that include `--format step` or `EXPORT_FORMATS='stl step'`.
- After export, inspect the output directory and remove any accidentally generated non-STL model files before finishing.
- PNG or SVG preview images may be created under `build/previews/` when needed for visual validation, but they are previews, not model deliverables.
- Keep generated files under `build/` or `exports/`. Both directories are ignored except for their `.gitkeep` files; do not commit generated artifacts unless the user explicitly requests it.

## Repository map

- `src/print_models/models/`: canonical parametric model implementations.
- `src/print_models/catalog.py`: registry of models exposed by `generate-model`.
- `src/print_models/cli.py`: model description, parameter parsing, and export behavior.
- `preview.py`: geometry inspection, preview rendering, and export helper.
- `tests/`: `unittest` tests, including geometry-policy coverage.
- `docs/stl_validation.md`: baseline-mesh comparison procedure.
- `scripts/validate_stl_match.py`: lightweight bidirectional STL comparison tool.
- `exports/source/`: local reference meshes and images when present; treat them as validation inputs, not editable model source.

## Adding or changing models

- Follow the structure of an existing module in `src/print_models/models/`.
- Define `NAME`, `DESCRIPTION`, `PARAMETERS`, optional `PRINT_NOTES`, and a `build()` function.
- Return one CadQuery-exportable object or a mapping of stable part names to exportable objects.
- Register new modules in `MODEL_MODULES` in `src/print_models/catalog.py`.
- Keep dimensions parameterized and printable. Validate invalid, empty, negative, and geometry-breaking parameter combinations early with clear errors.
- Prefer shared helpers and existing model patterns over parallel implementations.
- Use fillets or chamfers where they improve printing, while preserving intended fit and tolerances.
- Build geometry parametrically. Never import an STL reference mesh into CadQuery as implementation geometry; downloaded meshes are validation baselines only.

## Code conventions

- Support the Python range declared in `pyproject.toml` (`>=3.10,<3.13`); use Python 3.11 for local setup.
- Follow the Ruff configuration in `pyproject.toml`: 100-character lines and the `E`, `F`, `I`, `UP`, and `B` rule sets.
- Preserve type annotations and descriptive parameter names. Do not add lint or type-check suppression comments.
- Keep imports at module scope unless a local import intentionally avoids loading heavy CAD dependencies before model construction.
- Update tests when changing parameter parsing, output naming, splitting, fit, or other geometry policy.

## Validation expectations

- Run the full `unittest` suite after Python changes.
- For every changed model, run `.venv/bin/python preview.py "$MODEL" --no-preview` with representative parameters and review bounding box, extents, volume, area, and center of mass for plausibility.
- Render relevant orthographic and isometric previews for geometry changes; inspect critical clearances, wall thicknesses, orientation, mating parts, and split interfaces.
- Export the final candidate explicitly as STL only.
- When matching a reference STL, follow `docs/stl_validation.md`; compare coordinate frames and scalar geometry before bidirectional surface distances, and never rely on a one-sided distance alone.
- If a required check cannot run, report the exact command and reason rather than claiming validation succeeded.

## Change boundaries

- Do not hand-edit generated CAD outputs or cached files.
- Do not run `make clean`; it deletes everything under `exports/`, including local reference assets in `exports/source/`.
- Do not modify or replace reference assets in `exports/source/` unless the task explicitly requires it.
- Keep unrelated working-tree changes intact and avoid destructive Git operations.
- Ask before adding dependencies or changing the supported Python range.
- Keep this file current when repository commands, layout, output policy, or validation requirements change.
