"""Command-line tools for exporting CadQuery models."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Mapping
from pathlib import Path
from types import ModuleType
from typing import Any

from print_models.catalog import load_models
from print_models.filenames import output_filename

EXPORT_FORMATS = ("stl", "step", "3mf", "svg")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="generate-model",
        description="Generate CadQuery models for 3D printing.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("list", help="List registered models.")

    describe_parser = subparsers.add_parser("describe", help="Show model parameters.")
    describe_parser.add_argument("model", help="Model name to describe.")

    export_parser = subparsers.add_parser("export", help="Export one or all models.")
    export_parser.add_argument("model", nargs="?", help="Model name to export.")
    export_parser.add_argument("--all", action="store_true", help="Export all registered models.")
    export_parser.add_argument(
        "--format",
        choices=EXPORT_FORMATS,
        action="append",
        dest="formats",
        help="Output format. Repeat for multiple formats. Defaults to stl.",
    )
    export_parser.add_argument(
        "--out-dir",
        default="build",
        type=Path,
        help="Directory for generated files. Defaults to build/.",
    )
    export_parser.add_argument(
        "--param",
        action="append",
        default=[],
        help="Parameter override as key=value. Repeat for multiple overrides.",
    )

    args = parser.parse_args()
    models = load_models()

    if args.command == "list":
        list_models(models)
        return

    if args.command == "describe":
        model = get_model(models, args.model)
        describe_model(model)
        return

    if args.command == "export":
        export_models(models, args)
        return


def list_models(models: dict[str, ModuleType]) -> None:
    for name, module in sorted(models.items()):
        print(f"{name}: {module.DESCRIPTION}")


def describe_model(module: ModuleType) -> None:
    print(f"{module.NAME}: {module.DESCRIPTION}")
    print()
    print("Parameters:")

    for name, default in module.PARAMETERS.items():
        print(f"  {name} = {default!r}")

    supported_formats = getattr(module, "SUPPORTED_FORMATS", None)
    if supported_formats:
        print()
        print("Supported formats:")
        print(f"  {', '.join(supported_formats)}")

    notes = getattr(module, "PRINT_NOTES", None)
    if notes:
        print()
        print("Print notes:")
        print(f"  {notes}")


def export_models(models: dict[str, ModuleType], args: argparse.Namespace) -> None:
    if args.all:
        selected_models = models
    elif args.model:
        selected_models = {args.model: get_model(models, args.model)}
    else:
        raise SystemExit("Specify a model name or pass --all.")

    formats = args.formats or ["stl"]
    args.out_dir.mkdir(parents=True, exist_ok=True)

    for name, module in sorted(selected_models.items()):
        parameters = parse_parameters(module, args.param)
        result = module.build(**parameters)
        supported_formats = getattr(module, "SUPPORTED_FORMATS", EXPORT_FORMATS)
        exportables = normalize_exportables(name, result)

        for file_format in formats:
            if file_format not in supported_formats:
                supported = ", ".join(supported_formats)
                message = f"Model {name!r} supports these formats only: {supported}"
                if args.all:
                    print(f"Skipping {name}.{file_format}: {message}", file=sys.stderr)
                    continue
                raise SystemExit(message)

            for output_name, exportable in exportables.items():
                output_path = args.out_dir / output_filename(output_name, file_format)
                exportable.export(str(output_path))
                print(output_path)


def normalize_exportables(model_name: str, result: Any) -> dict[str, Any]:
    """Return one or more named objects that provide an export(path) method."""
    if not isinstance(result, Mapping):
        return {model_name: result}

    return {f"{model_name}_{part_name}": exportable for part_name, exportable in result.items()}


def get_model(models: dict[str, ModuleType], name: str) -> ModuleType:
    try:
        return models[name]
    except KeyError as error:
        available = ", ".join(sorted(models))
        raise SystemExit(f"Unknown model {name!r}. Available models: {available}") from error


def parse_parameters(module: ModuleType, raw_parameters: list[str]) -> dict[str, Any]:
    parameters = dict(module.PARAMETERS)

    for raw_parameter in raw_parameters:
        key, separator, raw_value = raw_parameter.partition("=")
        if not separator:
            raise SystemExit(f"Parameter {raw_parameter!r} must use key=value syntax.")

        if key not in parameters:
            available = ", ".join(sorted(parameters))
            raise SystemExit(f"Unknown parameter {key!r}. Available parameters: {available}")

        parameters[key] = parse_value(raw_value, parameters[key])

    return parameters


def parse_value(raw_value: str, default: Any) -> Any:
    if isinstance(default, bool):
        normalized = raw_value.lower()
        if normalized in {"1", "true", "yes", "on"}:
            return True
        if normalized in {"0", "false", "no", "off"}:
            return False
        raise SystemExit(f"Expected a boolean value, got {raw_value!r}.")

    if isinstance(default, int):
        return int(raw_value)

    if isinstance(default, float):
        return float(raw_value)

    return raw_value


if __name__ == "__main__":
    main()
