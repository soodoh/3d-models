# 3D Models

A starter CadQuery workspace for generating parametric models for 3D printing.

## Setup

CadQuery currently works best on Python 3.10–3.12. Python 3.11 is a safe default. Python 3.13+ is intentionally rejected because CadQuery does not reliably support it yet.

First check that Python 3.11 is installed:

```bash
python3.11 --version
```

On macOS with Homebrew, install it if needed:

```bash
brew install python@3.11
```

Then create the virtual environment with that exact interpreter:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python --version
python -m pip install --upgrade pip
python -m pip install -e .
```

If you use fish shell, activate the environment with:

```fish
source .venv/bin/activate.fish
```

If you use `uv`:

```bash
uv venv --python 3.11
source .venv/bin/activate
uv pip install -e .
```

Or with fish shell:

```fish
uv venv --python 3.11
source .venv/bin/activate.fish
uv pip install -e .
```

## Generate models

List available models:

```bash
generate-model list
```

Describe model parameters:

```bash
generate-model describe calibration_cube
```

Export STL and STEP files:

```bash
generate-model export calibration_cube --format stl --format step
```

Override parameters with `--param key=value`:

```bash
generate-model export calibration_cube \
  --param size=25 \
  --param hole_diameter=6 \
  --format stl
```

Generate every starter model:

```bash
generate-model export --all --format stl --format step
```

Generated files are written to `build/` by default and ignored by git.

## Add a new model

1. Copy `src/print_models/models/template.py` to a new file.
2. Fill out `NAME`, `DESCRIPTION`, `PARAMETERS`, and `build()`.
3. Add the module path to `MODEL_MODULES` in `src/print_models/catalog.py`.
4. Run `generate-model describe your_model` and export it.

Model conventions:

- Use millimeters for dimensions.
- Keep parameters printable and documented.
- Export STL for slicers and STEP for editable CAD handoff.
- Prefer fillets/chamfers on sharp edges where they improve print quality.

## Included starter models

- `calibration_cube`: a chamfered calibration cube with an optional vertical hole.
- `phone_stand`: a simple printable desktop phone stand with a front lip.
