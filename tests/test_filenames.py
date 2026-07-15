"""Filename policy tests for generated model files."""

from __future__ import annotations

import argparse
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import preview

from print_models.cli import export_models
from print_models.filenames import (
    PRUSA_CORE_ONE_PLUS_MAX_FILENAME_LENGTH,
    output_filename,
)


class RecordingExportable:
    def __init__(self) -> None:
        self.paths: list[Path] = []

    def export(self, path: str) -> None:
        self.paths.append(Path(path))


class OutputFilenameTests(unittest.TestCase):
    def test_counts_extension_within_prusa_limit(self) -> None:
        extension = ".stl"
        stem = "a" * (PRUSA_CORE_ONE_PLUS_MAX_FILENAME_LENGTH - len(extension))

        filename = output_filename(stem, extension)

        self.assertEqual(filename, f"{stem}{extension}")
        self.assertEqual(len(filename), PRUSA_CORE_ONE_PLUS_MAX_FILENAME_LENGTH)

    def test_shortens_long_names_and_preserves_extension(self) -> None:
        filename = output_filename("prefix_" + "parameter_" * 30 + "printable_part", "step")

        self.assertEqual(len(filename), PRUSA_CORE_ONE_PLUS_MAX_FILENAME_LENGTH)
        self.assertTrue(filename.startswith("prefix_"))
        self.assertTrue(filename.endswith("printable_part.step"))

    def test_hash_keeps_truncated_names_unique(self) -> None:
        shared = "parameter_" * 30

        first = output_filename(f"{shared}first", "3mf")
        second = output_filename(f"{shared}second", "3mf")

        self.assertNotEqual(first, second)
        self.assertLessEqual(len(first), PRUSA_CORE_ONE_PLUS_MAX_FILENAME_LENGTH)
        self.assertLessEqual(len(second), PRUSA_CORE_ONE_PLUS_MAX_FILENAME_LENGTH)

    def test_sanitizes_unsafe_characters(self) -> None:
        self.assertEqual(output_filename("box / lid: final", ".stl"), "box_lid_final.stl")

    def test_handles_an_extension_that_leaves_no_retained_suffix(self) -> None:
        extension = "e" * 155

        filename = output_filename("model" * 40, extension)

        self.assertEqual(len(filename), PRUSA_CORE_ONE_PLUS_MAX_FILENAME_LENGTH)
        self.assertTrue(filename.endswith(f".{extension}"))

    def test_requires_an_extension(self) -> None:
        with self.assertRaisesRegex(ValueError, "extension is required"):
            output_filename("model", "")


class CliFilenameTests(unittest.TestCase):
    def test_export_enforces_limit_at_the_write_boundary(self) -> None:
        exportable = RecordingExportable()
        model_name = "model_" * 40
        module = SimpleNamespace(PARAMETERS={}, build=lambda: exportable)

        with tempfile.TemporaryDirectory() as temporary_directory:
            args = argparse.Namespace(
                all=True,
                model=None,
                formats=["stl"],
                out_dir=Path(temporary_directory),
                param=[],
            )
            export_models({model_name: module}, args)

        self.assertEqual(len(exportable.paths), 1)
        self.assertLessEqual(
            len(exportable.paths[0].name),
            PRUSA_CORE_ONE_PLUS_MAX_FILENAME_LENGTH,
        )
        self.assertEqual(exportable.paths[0].suffix, ".stl")


class PreviewFilenameTests(unittest.TestCase):
    def test_model_export_enforces_limit_at_the_write_boundary(self) -> None:
        exportable = RecordingExportable()

        with tempfile.TemporaryDirectory() as temporary_directory:
            preview.write_exports(
                {"model_" * 40: exportable},
                Path(temporary_directory),
                "step",
            )

        self.assertEqual(len(exportable.paths), 1)
        self.assertLessEqual(
            len(exportable.paths[0].name),
            PRUSA_CORE_ONE_PLUS_MAX_FILENAME_LENGTH,
        )
        self.assertEqual(exportable.paths[0].suffix, ".step")

    def test_rendered_preview_enforces_limit_at_the_write_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            output_directory = Path(temporary_directory)
            args = argparse.Namespace(
                views="isometric",
                out_dir=output_directory,
                preview_format="svg",
                width=100,
                height=100,
                hide_hidden=False,
            )
            with (
                patch.object(preview, "shape_from_exportable", return_value=object()),
                patch.object(preview.exporters, "getSVG", return_value="<svg />"),
            ):
                preview.write_previews({"model_" * 40: object()}, args)

            filenames = [path.name for path in output_directory.iterdir()]

        self.assertEqual(len(filenames), 1)
        self.assertLessEqual(
            len(filenames[0]),
            PRUSA_CORE_ONE_PLUS_MAX_FILENAME_LENGTH,
        )
        self.assertTrue(filenames[0].endswith("isometric.svg"))


if __name__ == "__main__":
    unittest.main()
