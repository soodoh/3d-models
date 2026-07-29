"""Geometry policy tests for the upgraded ratchet toothpaste tube squeezer."""

from __future__ import annotations

import math
import struct
import tempfile
import unittest
from collections import Counter

import cadquery as cq

from print_models.models import ratchet_toothpaste_tube_squeezer as squeezer


class RatchetToothpasteTubeSqueezerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.default_parts = squeezer.build()

    def test_builds_all_upgraded_parts_as_valid_single_solids(self) -> None:
        self.assertEqual(tuple(self.default_parts), ("body", "shaft", "handle", "ratchet", "nut"))
        for name, part in self.default_parts.items():
            with self.subTest(part=name):
                self.assertEqual(len(part.solids().vals()), 1)
                self.assertTrue(part.val().isValid())

    def test_default_envelopes_match_upgraded_stls(self) -> None:
        expected_sizes = {
            "body": (26.0, 26.0, 71.05),
            "shaft": (15.0, 89.0, 6.0),
            "handle": (27.283939, 27.28272, 7.8),
            "ratchet": (18.5, 18.5, 4.0),
            "nut": (14.339522, 14.368098, 12.0),
        }
        for name, expected_size in expected_sizes.items():
            with self.subTest(part=name):
                bounds = self.default_parts[name].val().BoundingBox()
                for actual, expected in zip(
                    (bounds.xlen, bounds.ylen, bounds.zlen), expected_size, strict=True
                ):
                    self.assertAlmostEqual(actual, expected, delta=0.06)

    def test_shaft_exports_broad_side_flat_on_build_plane(self) -> None:
        shaft = self.default_parts["shaft"]
        bounds = shaft.val().BoundingBox()
        bottom_faces = shaft.faces("<Z").vals()

        self.assertAlmostEqual(bounds.zmin, 0.0, places=5)
        self.assertAlmostEqual(bounds.zlen, squeezer.SHAFT_DEPTH_MM, delta=0.001)
        self.assertGreater(bounds.ylen, bounds.zlen * 10.0)
        self.assertGreater(sum(face.Area() for face in bottom_faces), 300.0)

    def test_default_volumes_remain_close_to_upgraded_stls(self) -> None:
        expected_volumes = {
            "body": 7532.860093,
            "shaft": 3351.845007,
            "handle": 1979.639543,
            "ratchet": 355.520314,
            "nut": 1325.475649,
        }
        tolerances = {
            "body": 0.01,
            "shaft": 0.01,
            "handle": 0.02,
            "ratchet": 0.01,
            "nut": 0.02,
        }
        for name, expected_volume in expected_volumes.items():
            with self.subTest(part=name):
                actual_volume = self.default_parts[name].val().Volume()
                self.assertLessEqual(
                    abs(actual_volume - expected_volume) / expected_volume,
                    tolerances[name],
                )

    def test_tube_width_changes_only_body_and_shaft_lengths(self) -> None:
        wider_parts = squeezer.build(tube_width_mm=65.0)
        body_default_bounds = self.default_parts["body"].val().BoundingBox()
        body_wider_bounds = wider_parts["body"].val().BoundingBox()
        shaft_default_bounds = self.default_parts["shaft"].val().BoundingBox()
        shaft_wider_bounds = wider_parts["shaft"].val().BoundingBox()

        self.assertAlmostEqual(body_wider_bounds.zlen - body_default_bounds.zlen, 10.0, places=5)
        self.assertAlmostEqual(shaft_wider_bounds.ylen - shaft_default_bounds.ylen, 10.0, places=5)

        for name in ("handle", "ratchet", "nut"):
            default_shape = self.default_parts[name].val()
            wider_shape = wider_parts[name].val()
            default_bounds = default_shape.BoundingBox()
            wider_bounds = wider_shape.BoundingBox()
            self.assertAlmostEqual(wider_bounds.xlen, default_bounds.xlen, places=6)
            self.assertAlmostEqual(wider_bounds.ylen, default_bounds.ylen, places=6)
            self.assertAlmostEqual(wider_bounds.zlen, default_bounds.zlen, places=6)
            self.assertAlmostEqual(wider_shape.Volume(), default_shape.Volume(), places=6)

    def test_gap_controls_shaft_slot_and_body_throat_directly(self) -> None:
        wider_gap_parts = squeezer.build(gap_mm=2.0)
        for name in ("body", "shaft"):
            with self.subTest(part=name):
                self.assertTrue(wider_gap_parts[name].val().isValid())
                self.assertEqual(len(wider_gap_parts[name].solids().vals()), 1)
                self.assertLess(
                    wider_gap_parts[name].val().Volume(),
                    self.default_parts[name].val().Volume(),
                )

        self.assertAlmostEqual(_shaft_slot_width(self.default_parts["shaft"]), 1.0, places=5)
        self.assertAlmostEqual(_shaft_slot_width(wider_gap_parts["shaft"]), 2.0, places=5)
        self.assertAlmostEqual(_body_throat_width(self.default_parts["body"]), 1.0, places=5)
        self.assertAlmostEqual(_body_throat_width(wider_gap_parts["body"]), 2.0, places=5)

    def test_body_bottom_preserves_bearing_boss_tooth_ring_and_joining_plate(self) -> None:
        expected_ring_area = 254.6813968
        for height in (0.25, 1.25):
            with self.subTest(height=height):
                section = cq.Workplane("XY").add(self.default_parts["body"].val()).section(height)
                self.assertEqual(len(section.faces().vals()), 2)
                self.assertAlmostEqual(
                    sum(face.Area() for face in section.faces().vals()),
                    expected_ring_area,
                    places=5,
                )

        joining_plate = cq.Workplane("XY").add(self.default_parts["body"].val()).section(2.5)
        self.assertEqual(len(joining_plate.faces().vals()), 1)
        self.assertAlmostEqual(
            sum(face.Area() for face in joining_plate.faces().vals()),
            math.pi * (13.0**2 - 4.5**2),
            places=5,
        )

    def test_ratchet_pads_keep_directional_upgraded_orientation(self) -> None:
        ratchet = self.default_parts["ratchet"].val()
        for height in (1.0, 3.0):
            with self.subTest(height=height):
                self.assertTrue(ratchet.isInside(cq.Vector(-3.0, -8.75, height)))
                self.assertFalse(ratchet.isInside(cq.Vector(3.0, -8.75, height)))

    def test_shaft_uses_one_piece_repeating_thread_instead_of_flexible_tabs(self) -> None:
        shaft = _shaft_in_assembly_orientation(self.default_parts["shaft"]).val()
        sections = []
        for height in (80.0, 81.25, 85.0):
            section = cq.Workplane("XY").add(shaft).section(height)
            self.assertEqual(len(section.faces().vals()), 1)
            sections.append(sum(face.Area() for face in section.faces().vals()))

        self.assertAlmostEqual(sections[0], sections[1], delta=0.01)
        self.assertAlmostEqual(sections[0], sections[2], delta=0.01)
        self.assertAlmostEqual(sections[0], 34.8, delta=0.75)

    def test_thread_is_right_handed_and_fits_through_screw_motion(self) -> None:
        shaft_thread = (
            _shaft_in_assembly_orientation(self.default_parts["shaft"])
            .intersect(cq.Workplane("XY").box(20.0, 20.0, 10.0).translate((0.0, 0.0, 84.0)))
            .translate((0.0, 0.0, -79.0))
        )
        nut_in_assembly_orientation = (
            self.default_parts["nut"]
            .rotate((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), 180.0)
            .translate((0.0, 0.0, squeezer.NUT_HEIGHT_MM))
        )
        nut_thread_region = nut_in_assembly_orientation.intersect(
            cq.Workplane("XY").circle(5.0).extrude(10.1)
        )
        for angle_degrees in (45.0, 90.0, 135.0):
            with self.subTest(angle_degrees=angle_degrees):
                axial_travel = angle_degrees / 360.0 * squeezer.THREAD_PITCH_MM
                moving_thread = shaft_thread.rotate(
                    (0.0, 0.0, 0.0), (0.0, 0.0, 1.0), angle_degrees
                ).translate((0.0, 0.0, axial_travel))
                interference = moving_thread.intersect(nut_thread_region)
                self.assertEqual(len(interference.solids().vals()), 0)

        # Counterclockwise rotation viewed from the free end travels away from the base.
        # Moving in the former left-hand direction must cross the nut's thread flanks.
        wrong_way_thread = shaft_thread.rotate((0.0, 0.0, 0.0), (0.0, 0.0, 1.0), 90.0).translate(
            (0.0, 0.0, -squeezer.THREAD_PITCH_MM / 4.0)
        )
        self.assertGreater(wrong_way_thread.intersect(nut_thread_region).val().Volume(), 1.0)

    def test_nut_exports_with_closed_flat_face_on_build_plane(self) -> None:
        nut = self.default_parts["nut"]
        bounds = nut.val().BoundingBox()
        bottom_faces = nut.faces("<Z").vals()

        self.assertAlmostEqual(bounds.zmin, 0.0, places=5)
        self.assertEqual(len(bottom_faces), 1)
        self.assertGreater(bottom_faces[0].Area(), 130.0)
        self.assertTrue(nut.val().isInside(cq.Vector(0.0, 0.0, 0.1)))
        self.assertFalse(nut.val().isInside(cq.Vector(0.0, 0.0, squeezer.NUT_HEIGHT_MM - 0.1)))

    def test_all_parts_export_as_watertight_stls(self) -> None:
        for name, part in self.default_parts.items():
            with self.subTest(part=name):
                self.assertEqual(_stl_non_manifold_edge_count(part), 0)

    def test_accepts_supported_parameter_boundaries(self) -> None:
        for parameters in (
            {"tube_width_mm": 13.0},
            {"gap_mm": squeezer.MINIMUM_GAP_MM},
            {"gap_mm": 6.9},
        ):
            with self.subTest(parameters=parameters):
                parts = squeezer.build(**parameters)
                for part in parts.values():
                    self.assertEqual(len(part.solids().vals()), 1)
                    self.assertTrue(part.val().isValid())

    def test_rejects_geometry_breaking_parameters(self) -> None:
        invalid_parameters = (
            {"tube_width_mm": 0.0},
            {"tube_width_mm": 12.99},
            {"gap_mm": 0.0},
            {"gap_mm": -1.0},
            {"gap_mm": 1e-9},
            {"gap_mm": squeezer.MINIMUM_GAP_MM - 0.001},
            {"gap_mm": 7.0},
            {"tube_width_mm": math.nan},
            {"tube_width_mm": math.inf},
            {"gap_mm": math.nan},
            {"gap_mm": math.inf},
        )
        for parameters in invalid_parameters:
            with self.subTest(parameters=parameters), self.assertRaises(ValueError):
                squeezer.build(**parameters)


def _shaft_in_assembly_orientation(shaft):
    return shaft.translate((0.0, 0.0, -squeezer.SHAFT_DEPTH_MM / 2.0)).rotate(
        (0.0, 0.0, 0.0), (1.0, 0.0, 0.0), 90.0
    )


def _shaft_slot_width(shaft) -> float:
    assembly_shaft = _shaft_in_assembly_orientation(shaft)
    section = cq.Workplane("XY").add(assembly_shaft.val()).section(40.0)
    bounds = sorted(
        (face.BoundingBox() for face in section.faces().vals()), key=lambda box: box.xmin
    )
    return bounds[1].xmin - bounds[0].xmax


def _body_throat_width(body) -> float:
    section = (
        cq.Workplane("XY")
        .add(body.val())
        .section(30.0)
        .rotate((0.0, 0.0, 0.0), (0.0, 0.0, 1.0), -60.0)
    )
    throat_edges = [
        edge
        for edge in section.edges().vals()
        if edge.geomType() == "LINE"
        and edge.BoundingBox().xmin > 10.0
        and abs(edge.BoundingBox().ylen) < 1e-6
    ]
    throat_coordinates = sorted(edge.Center().y for edge in throat_edges)
    return throat_coordinates[-1] - throat_coordinates[0]


def _stl_non_manifold_edge_count(part) -> int:
    with tempfile.NamedTemporaryFile(suffix=".stl") as output_file:
        cq.exporters.export(part.val().copy(), output_file.name)
        stl_data = output_file.read()

    triangle_count = struct.unpack_from("<I", stl_data, 80)[0]
    edges = Counter()
    for triangle_index in range(triangle_count):
        values = struct.unpack_from("<12fH", stl_data, 84 + triangle_index * 50)
        vertices = [
            tuple(round(coordinate, 5) for coordinate in values[offset : offset + 3])
            for offset in (3, 6, 9)
        ]
        for vertex_index in range(3):
            edge = tuple(sorted((vertices[vertex_index], vertices[(vertex_index + 1) % 3])))
            edges[edge] += 1
    return sum(count != 2 for count in edges.values())


if __name__ == "__main__":
    unittest.main()
