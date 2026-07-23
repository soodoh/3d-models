"""Geometry tests for shared sliding-dovetail primitives."""

from __future__ import annotations

import unittest

from print_models.dovetail import trapezoidal_panel
from print_models.models.dutch_blitz_storage_box import _lid_dovetail_blank


class TrapezoidalPanelTests(unittest.TestCase):
    def test_builds_centered_x_and_y_axis_panels(self) -> None:
        import cadquery as cq

        for axis in ("x", "y"):
            with self.subTest(axis=axis):
                panel = trapezoidal_panel(
                    cq,
                    length=10.0,
                    bottom_width=8.0,
                    height=2.0,
                    side_inset=2.0,
                    extrusion_axis=axis,
                )
                bounding_box = panel.val().BoundingBox()
                bottom_box = panel.faces("<Z").val().BoundingBox()
                top_box = panel.faces(">Z").val().BoundingBox()

                self.assertTrue(panel.val().isValid())
                self.assertEqual(len(panel.solids().vals()), 1)
                self.assertAlmostEqual(bounding_box.zlen, 2.0)
                if axis == "x":
                    self.assertAlmostEqual(bounding_box.xmin, -5.0)
                    self.assertAlmostEqual(bounding_box.xmax, 5.0)
                    self.assertAlmostEqual(bottom_box.ylen, 8.0)
                    self.assertAlmostEqual(top_box.ylen, 4.0)
                else:
                    self.assertAlmostEqual(bounding_box.ymin, -5.0)
                    self.assertAlmostEqual(bounding_box.ymax, 5.0)
                    self.assertAlmostEqual(bottom_box.xlen, 8.0)
                    self.assertAlmostEqual(top_box.xlen, 4.0)

    def test_front_inset_shortens_only_the_top_front(self) -> None:
        import cadquery as cq

        panel = trapezoidal_panel(
            cq,
            length=10.0,
            bottom_width=8.0,
            height=2.0,
            side_inset=1.0,
            extrusion_axis="y",
            front_inset=3.2,
        )
        bottom_box = panel.faces("<Z").val().BoundingBox()
        top_box = panel.faces(">Z").val().BoundingBox()

        self.assertAlmostEqual(bottom_box.ymin, -5.0)
        self.assertAlmostEqual(bottom_box.ymax, 5.0)
        self.assertAlmostEqual(top_box.ymin, -1.8)
        self.assertAlmostEqual(top_box.ymax, 5.0)
        self.assertAlmostEqual(top_box.ylen, 6.8)

    def test_rejects_invalid_dimensions_and_axis(self) -> None:
        import cadquery as cq

        invalid_parameters = (
            {"length": 0.0},
            {"bottom_width": 0.0},
            {"height": 0.0},
            {"side_inset": -0.1},
            {"side_inset": 4.0},
            {"front_inset": -0.1},
            {"front_inset": 10.0},
            {"extrusion_axis": "z"},
        )
        defaults = {
            "length": 10.0,
            "bottom_width": 8.0,
            "height": 2.0,
            "side_inset": 1.0,
            "extrusion_axis": "x",
            "front_inset": 0.0,
        }
        for overrides in invalid_parameters:
            with self.subTest(overrides=overrides), self.assertRaises(ValueError):
                trapezoidal_panel(cq, **(defaults | overrides))

    def test_dutch_blitz_wrapper_preserves_legacy_scalar_geometry(self) -> None:
        import cadquery as cq

        panel = _lid_dovetail_blank(cq, 95.362904, 61.820216, 3.076608)
        bounding_box = panel.val().BoundingBox()

        self.assertAlmostEqual(bounding_box.xlen, 95.362904)
        self.assertAlmostEqual(bounding_box.ylen, 61.820216)
        self.assertAlmostEqual(bounding_box.zlen, 3.076608)
        self.assertAlmostEqual(panel.val().Volume(), 17505.69440026066, places=6)


if __name__ == "__main__":
    unittest.main()
