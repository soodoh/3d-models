#!/usr/bin/env python3
"""Fast CadQuery preview, inspection, and export helper."""

from __future__ import annotations

import argparse
import importlib.util
import re
import sys
import xml.etree.ElementTree as ET
from collections.abc import Mapping
from pathlib import Path
from types import ModuleType
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent
SRC_DIR = PROJECT_ROOT / "src"
if SRC_DIR.exists():
    sys.path.insert(0, str(SRC_DIR))

from cadquery import exporters  # noqa: E402

from print_models.catalog import load_models  # noqa: E402
from print_models.cli import normalize_exportables, parse_parameters  # noqa: E402
from print_models.filenames import output_filename, sanitize_filename  # noqa: E402

PREVIEW_FORMATS = ("svg", "png", "both")
EXPORT_FORMATS = ("stl", "step", "3mf", "svg")
DEFAULT_VIEWS = ("isometric", "top", "front", "right")
VIEW_DIRECTIONS = {
    "isometric": (-1.75, 1.1, 5.0),
    "iso": (-1.75, 1.1, 5.0),
    "front": (0.0, -1.0, 0.0),
    "back": (0.0, 1.0, 0.0),
    "top": (0.0, 0.0, 1.0),
    "bottom": (0.0, 0.0, -1.0),
    "left": (-1.0, 0.0, 0.0),
    "right": (1.0, 0.0, 0.0),
}


class CapturedObjects:
    """Collect objects from CQ-editor style show_object calls."""

    def __init__(self) -> None:
        self.objects: dict[str, Any] = {}
        self.count = 0

    def show_object(self, obj: Any, name: str | None = None, **_kwargs: Any) -> None:
        self.count += 1
        object_name = name or f"object_{self.count}"
        self.objects[object_name] = obj


def main() -> None:
    args = parse_args()
    module, result = build_model(args.model, args.param)
    model_name = getattr(module, "NAME", Path(args.model).stem)
    exportables = normalize_named_exportables(model_name, result)

    if args.inspect:
        inspect_exportables(exportables)

    if args.preview:
        write_previews(exportables, args)

    for file_format in args.exports:
        write_exports(exportables, args.export_dir, file_format)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Render quick SVG views, print geometry stats, and optionally export registered "
            "or file-based CadQuery models."
        )
    )
    parser.add_argument(
        "model",
        help=(
            "Registered model name from generate-model list, or a path to a .py file with "
            "build(), result, or show_object(...)."
        ),
    )
    parser.add_argument(
        "--param",
        action="append",
        default=[],
        help="Parameter override as key=value. Repeat for multiple overrides.",
    )
    parser.add_argument(
        "--views",
        default=",".join(DEFAULT_VIEWS),
        help=(
            "Comma-separated SVG views. Choices: all, "
            f"{', '.join(sorted(VIEW_DIRECTIONS))}. Defaults to %(default)s."
        ),
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path("build/previews"),
        help="Directory for previews. Defaults to build/previews/.",
    )
    parser.add_argument(
        "--preview-format",
        choices=PREVIEW_FORMATS,
        default="png",
        help=(
            "Preview image format. Defaults to png. PNG previews are rendered from "
            "CadQuery SVG output."
        ),
    )
    parser.add_argument(
        "--export-dir",
        type=Path,
        default=Path("build"),
        help="Directory for exported STL/STEP/3MF/SVG files. Defaults to build/.",
    )
    parser.add_argument(
        "--export",
        choices=EXPORT_FORMATS,
        action="append",
        default=[],
        dest="exports",
        help="Export format. Repeat for multiple formats.",
    )
    parser.add_argument(
        "--width",
        type=int,
        default=1000,
        help="SVG preview width in pixels. Defaults to %(default)s.",
    )
    parser.add_argument(
        "--height",
        type=int,
        default=750,
        help="SVG preview height in pixels. Defaults to %(default)s.",
    )
    parser.add_argument(
        "--hide-hidden",
        action="store_true",
        help="Hide occluded/back-side edges in SVG previews.",
    )
    parser.add_argument(
        "--no-preview",
        action="store_false",
        dest="preview",
        help="Skip SVG preview rendering.",
    )
    parser.add_argument(
        "--no-inspect",
        action="store_false",
        dest="inspect",
        help="Skip bounding box, volume, area, and center-of-mass output.",
    )
    parser.set_defaults(preview=True, inspect=True)
    return parser.parse_args()


def build_model(source: str, raw_parameters: list[str]) -> tuple[ModuleType, Any]:
    source_path = Path(source)
    if source_path.exists():
        module, captured = load_module_from_path(source_path)
        if hasattr(module, "build"):
            parameters = parse_module_parameters(module, raw_parameters)
            return module, module.build(**parameters)
        if raw_parameters:
            raise SystemExit("--param requires a file model with PARAMETERS and build().")
        if "result" in module.__dict__:
            return module, module.__dict__["result"]
        if captured.objects:
            return module, captured.objects
        raise SystemExit(f"{source_path} did not define build(), result, or call show_object(...).")

    models = load_models()
    try:
        module = models[source]
    except KeyError as error:
        available = ", ".join(sorted(models))
        raise SystemExit(
            f"Unknown model {source!r}. Use a .py path or one of: {available}"
        ) from error

    parameters = parse_parameters(module, raw_parameters)
    return module, module.build(**parameters)


def load_module_from_path(path: Path) -> tuple[ModuleType, CapturedObjects]:
    module_path = path.resolve()
    module_name = f"cadquery_preview_{sanitize_module_name(module_path.stem)}"
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"Could not load Python module from {module_path}.")

    captured = CapturedObjects()
    module = importlib.util.module_from_spec(spec)
    module.show_object = captured.show_object
    sys.modules[module_name] = module

    module_dir = str(module_path.parent)
    sys.path.insert(0, module_dir)
    try:
        spec.loader.exec_module(module)
    finally:
        sys.path.remove(module_dir)

    return module, captured


def parse_module_parameters(module: ModuleType, raw_parameters: list[str]) -> dict[str, Any]:
    if not hasattr(module, "PARAMETERS"):
        if raw_parameters:
            raise SystemExit("--param requires a PARAMETERS dict in file-based models.")
        return {}
    return parse_parameters(module, raw_parameters)


def normalize_named_exportables(model_name: str, result: Any) -> dict[str, Any]:
    if isinstance(result, Mapping):
        return {
            sanitize_filename(name): exportable
            for name, exportable in normalize_exportables(model_name, result).items()
        }
    return {sanitize_filename(model_name): result}


def inspect_exportables(exportables: Mapping[str, Any]) -> None:
    print("Geometry inspection")
    print("===================")
    for name, exportable in exportables.items():
        shape = shape_from_exportable(exportable)
        bounding_box = shape.BoundingBox()
        center = shape.Center()
        print(f"{name}:")
        print(
            "  bounding box: "
            f"{bounding_box.xlen:.3f} x {bounding_box.ylen:.3f} x {bounding_box.zlen:.3f} mm"
        )
        print(
            "  extents: "
            f"x[{bounding_box.xmin:.3f}, {bounding_box.xmax:.3f}], "
            f"y[{bounding_box.ymin:.3f}, {bounding_box.ymax:.3f}], "
            f"z[{bounding_box.zmin:.3f}, {bounding_box.zmax:.3f}]"
        )
        print(f"  volume: {shape.Volume():.3f} mm^3")
        print(f"  surface area: {shape.Area():.3f} mm^2")
        print(f"  center of mass: ({center.x:.3f}, {center.y:.3f}, {center.z:.3f})")
    print()


def write_previews(exportables: Mapping[str, Any], args: argparse.Namespace) -> None:
    views = parse_views(args.views)
    args.out_dir.mkdir(parents=True, exist_ok=True)

    for name, exportable in exportables.items():
        shape = shape_from_exportable(exportable)
        for view in views:
            svg_text = exporters.getSVG(shape, preview_options(args, view))

            if args.preview_format in {"svg", "both"}:
                svg_path = args.out_dir / output_filename(f"{name}_{view}", "svg")
                svg_path.write_text(svg_text)
                print(svg_path)

            if args.preview_format in {"png", "both"}:
                png_path = args.out_dir / output_filename(f"{name}_{view}", "png")
                write_png_preview(svg_text, png_path)
                print(png_path)


def preview_options(args: argparse.Namespace, view: str) -> dict[str, Any]:
    return {
        "width": args.width,
        "height": args.height,
        "marginLeft": 30,
        "marginTop": 30,
        "projectionDir": VIEW_DIRECTIONS[view],
        "showAxes": view in {"isometric", "iso"},
        "showHidden": not args.hide_hidden,
    }


def write_png_preview(svg_text: str, output_path: Path) -> None:
    try:
        from PIL import Image, ImageDraw
    except ModuleNotFoundError as error:
        raise SystemExit(
            "PNG previews require Pillow. Run `python -m pip install -e .` "
            "or `python -m pip install pillow`, then retry."
        ) from error

    root = ET.fromstring(svg_text)
    width = int(float(root.attrib["width"]))
    height = int(float(root.attrib["height"]))
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    draw_svg_paths(draw, root)
    image.save(output_path)


def draw_svg_paths(draw: Any, root: ET.Element) -> None:
    walk_svg(root, identity_matrix(), {}, draw)


def walk_svg(
    element: ET.Element,
    parent_transform: tuple[float, float, float, float, float, float],
    inherited_style: dict[str, str],
    draw: Any,
) -> None:
    style = inherited_style | svg_style_attributes(element)
    local_transform = parse_svg_transform(element.attrib.get("transform", ""))
    transform = multiply_matrices(parent_transform, local_transform)

    if strip_namespace(element.tag) == "path" and "d" in element.attrib:
        draw_svg_path(draw, element.attrib["d"], transform, style)

    for child in element:
        walk_svg(child, transform, style, draw)


def svg_style_attributes(element: ET.Element) -> dict[str, str]:
    names = ("stroke", "stroke-width", "fill", "stroke-dasharray")
    style = {name: element.attrib[name] for name in names if name in element.attrib}

    inline_style = element.attrib.get("style")
    if inline_style:
        for declaration in inline_style.split(";"):
            key, separator, value = declaration.partition(":")
            if separator:
                style[key.strip()] = value.strip()

    return style


def draw_svg_path(
    draw: Any,
    path_data: str,
    transform: tuple[float, float, float, float, float, float],
    style: dict[str, str],
) -> None:
    stroke = parse_svg_color(style.get("stroke", "rgb(0,0,0)"))
    if stroke is None:
        return

    points = [apply_matrix(transform, point) for point in parse_svg_path_points(path_data)]
    if len(points) < 2:
        return

    stroke_width = max(1, round(float(style.get("stroke-width", "1"))))
    draw.line(points, fill=stroke, width=stroke_width)


def parse_svg_path_points(path_data: str) -> list[tuple[float, float]]:
    tokens = re.findall(
        r"[MLZmlz]|[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?",
        path_data,
    )
    points: list[tuple[float, float]] = []
    command = ""
    current = (0.0, 0.0)
    index = 0

    while index < len(tokens):
        token = tokens[index]
        if token.isalpha():
            command = token
            index += 1
            if command in {"Z", "z"}:
                continue

        if command not in {"M", "L", "m", "l"} or index + 1 >= len(tokens):
            break

        x = float(tokens[index])
        y = float(tokens[index + 1])
        index += 2
        if command.islower():
            x += current[0]
            y += current[1]
        current = (x, y)
        points.append(current)

    return points


def parse_svg_transform(value: str) -> tuple[float, float, float, float, float, float]:
    matrix = identity_matrix()
    for name, raw_arguments in re.findall(r"(\w+)\(([^)]*)\)", value):
        arguments = [
            float(argument)
            for argument in re.findall(
                r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?",
                raw_arguments,
            )
        ]
        if name == "translate" and arguments:
            tx = arguments[0]
            ty = arguments[1] if len(arguments) > 1 else 0.0
            operation = (1.0, 0.0, 0.0, 1.0, tx, ty)
        elif name == "scale" and arguments:
            sx = arguments[0]
            sy = arguments[1] if len(arguments) > 1 else sx
            operation = (sx, 0.0, 0.0, sy, 0.0, 0.0)
        elif name == "matrix" and len(arguments) == 6:
            operation = (
                arguments[0],
                arguments[1],
                arguments[2],
                arguments[3],
                arguments[4],
                arguments[5],
            )
        else:
            continue
        matrix = multiply_matrices(matrix, operation)
    return matrix


def identity_matrix() -> tuple[float, float, float, float, float, float]:
    return (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)


def multiply_matrices(
    left: tuple[float, float, float, float, float, float],
    right: tuple[float, float, float, float, float, float],
) -> tuple[float, float, float, float, float, float]:
    left_a, left_b, left_c, left_d, left_e, left_f = left
    right_a, right_b, right_c, right_d, right_e, right_f = right
    return (
        left_a * right_a + left_c * right_b,
        left_b * right_a + left_d * right_b,
        left_a * right_c + left_c * right_d,
        left_b * right_c + left_d * right_d,
        left_a * right_e + left_c * right_f + left_e,
        left_b * right_e + left_d * right_f + left_f,
    )


def apply_matrix(
    matrix: tuple[float, float, float, float, float, float], point: tuple[float, float]
) -> tuple[float, float]:
    a, b, c, d, e, f = matrix
    x, y = point
    return (a * x + c * y + e, b * x + d * y + f)


def parse_svg_color(value: str) -> tuple[int, int, int] | None:
    if value == "none":
        return None
    if value.startswith("rgb(") and value.endswith(")"):
        return tuple(int(part) for part in re.findall(r"\d+", value)[:3])
    if value.startswith("#") and len(value) == 7:
        return tuple(int(value[index : index + 2], 16) for index in (1, 3, 5))
    return (0, 0, 0)


def strip_namespace(tag: str) -> str:
    return tag.rpartition("}")[2]


def write_exports(exportables: Mapping[str, Any], export_dir: Path, file_format: str) -> None:
    export_dir.mkdir(parents=True, exist_ok=True)
    for name, exportable in exportables.items():
        output_path = export_dir / output_filename(name, file_format)
        if hasattr(exportable, "export"):
            exportable.export(str(output_path))
        else:
            exporters.export(exportable, str(output_path), exportType=file_format.upper())
        print(output_path)


def parse_views(raw_views: str) -> tuple[str, ...]:
    requested_views = tuple(view.strip().lower() for view in raw_views.split(",") if view.strip())
    if not requested_views:
        raise SystemExit("--views must include at least one view.")
    if requested_views == ("all",):
        return tuple(view for view in VIEW_DIRECTIONS if view != "iso")

    unknown_views = sorted(set(requested_views) - set(VIEW_DIRECTIONS))
    if unknown_views:
        available = ", ".join(sorted(VIEW_DIRECTIONS))
        raise SystemExit(f"Unknown views: {', '.join(unknown_views)}. Available: {available}")
    return requested_views


def shape_from_exportable(exportable: Any) -> Any:
    if hasattr(exportable, "val"):
        return exportable.val()
    return exportable


def sanitize_module_name(value: str) -> str:
    module_name = re.sub(r"\W+", "_", value).strip("_") or "model"
    if module_name[0].isdigit():
        return f"_{module_name}"
    return module_name


if __name__ == "__main__":
    main()
