"""Topology regressions for the sliding card-storage boxes."""

from __future__ import annotations

import unittest
from importlib.resources import files

from print_models.dxf import extrude_dxf_regions
from print_models.models import (
    dutch_blitz_storage_box,
    five_crowns_storage_box,
    monopoly_deal_storage_box,
)


class CardStorageBoxTopologyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.results = {
            "dutch_blitz": dutch_blitz_storage_box.build(),
            "five_crowns": five_crowns_storage_box.build(),
            "monopoly_deal": monopoly_deal_storage_box.build(),
        }

    def test_default_parts_are_valid_connected_solids(self) -> None:
        for model_name, result in self.results.items():
            for part_name, part in result.items():
                with self.subTest(model=model_name, part=part_name):
                    self.assertTrue(part.val().isValid())
                    self.assertEqual(len(part.solids().vals()), 1)

    def test_default_part_envelopes_remain_stable(self) -> None:
        expected_envelopes = {
            ("dutch_blitz", "container"): (63.2, 66.4, 91.076608),
            ("dutch_blitz", "lid"): (59.0, 62.220216, 3.076608),
            ("five_crowns", "container"): (98.362904, 64.0, 48.0),
            ("five_crowns", "lid"): (95.362904, 61.820216, 5.53),
            ("monopoly_deal", "container"): (98.362904, 64.0, 41.0),
            ("monopoly_deal", "lid"): (95.362904, 61.820216, 5.53),
        }
        for (model_name, part_name), expected in expected_envelopes.items():
            with self.subTest(model=model_name, part=part_name):
                bounding_box = self.results[model_name][part_name].val().BoundingBox()
                actual = (bounding_box.xlen, bounding_box.ylen, bounding_box.zlen)
                for actual_extent, expected_extent in zip(actual, expected, strict=True):
                    self.assertAlmostEqual(actual_extent, expected_extent, places=5)

    def test_dutch_blitz_defaults_use_card_holder_insert_measurements(self) -> None:
        self.assertEqual(dutch_blitz_storage_box.PARAMETERS["card_length"], 82.0)
        self.assertEqual(dutch_blitz_storage_box.PARAMETERS["card_width"], 58.4)
        self.assertEqual(dutch_blitz_storage_box.PARAMETERS["deck_thickness"], 12.6)
        self.assertEqual(dutch_blitz_storage_box.PARAMETERS["divider_count"], 4)
        self.assertLess(
            63.2 * 66.4 * 91.076608,
            0.55 * (123.0 * 66.0 * 92.0),
        )

    def test_dutch_blitz_lid_handle_sits_below_the_logo(self) -> None:
        plain_lid = dutch_blitz_storage_box.build(
            part="lid", logo_depth=0, handle_slot=False, click_feature=False
        )["lid"]
        notched_lid = dutch_blitz_storage_box.build(
            part="lid", logo_depth=0, handle_slot=True, click_feature=False
        )["lid"]
        handle_cut = plain_lid.cut(notched_lid)
        bounding_box = handle_cut.val().BoundingBox()

        self.assertAlmostEqual(bounding_box.xmin, -12.5)
        self.assertAlmostEqual(bounding_box.xmax, 12.5)
        self.assertLess(bounding_box.ymax, 0.0)

    def test_dutch_blitz_lid_slides_and_locks_from_the_front(self) -> None:
        container = self.results["dutch_blitz"]["container"]
        lid = self.results["dutch_blitz"]["lid"]
        lid_z = 88.0
        locked_lid = lid.translate((0.0, -2.089892, lid_z))
        sliding_lid = lid.translate((0.0, -15.0, lid_z))

        self.assertEqual(len(container.intersect(locked_lid).solids().vals()), 0)
        click_overlap = sum(
            solid.Volume() for solid in container.intersect(sliding_lid).solids().vals()
        )
        self.assertGreater(click_overlap, 0.0)

    def test_logo_optional_lids_remain_valid(self) -> None:
        for module in (five_crowns_storage_box, monopoly_deal_storage_box):
            with self.subTest(model=module.NAME):
                lid = module.build(part="lid", logo_raise=False)["lid"]
                self.assertTrue(lid.val().isValid())
                self.assertEqual(len(lid.solids().vals()), 1)

    def test_fixed_logo_regions_preserve_nested_islands_and_counters(self) -> None:
        import cadquery as cq

        logos = (
            (
                five_crowns_storage_box._five_crowns_logo(cq, z=0.0, height=1.0),
                3,
                1692.4281594000984,
            ),
            (
                monopoly_deal_storage_box._monopoly_deal_logo(cq, z=0.0, height=1.0),
                10,
                717.5424851199696,
            ),
        )
        for logo, expected_region_count, expected_volume in logos:
            with self.subTest(region_count=expected_region_count):
                solids = logo.solids().vals()
                self.assertEqual(len(solids), expected_region_count)
                self.assertTrue(all(solid.isValid() for solid in solids))
                self.assertAlmostEqual(
                    sum(solid.Volume() for solid in solids),
                    expected_volume,
                    places=5,
                )

    def test_dutch_blitz_uses_valid_fraunces_otf_slogans(self) -> None:
        import cadquery as cq

        font_path = dutch_blitz_storage_box._logo_font_path("Fraunces")
        self.assertIsNotNone(font_path)
        self.assertEqual(font_path.suffix, ".otf")
        self.assertTrue(font_path.is_file())
        license_path = font_path.with_name("OFL.txt")
        self.assertTrue(license_path.is_file())
        self.assertIn("SIL OPEN FONT LICENSE", license_path.read_text())

        for right, x_coordinate in ((True, 61.5), (False, -61.5)):
            with self.subTest(right=right):
                cutter = dutch_blitz_storage_box._short_side_slogan_cutter(
                    cq=cq,
                    x=x_coordinate,
                    z_center=46.0,
                    size=10.0,
                    depth=0.8,
                    right=right,
                )
                solids = cutter.solids().vals()
                bounding_box = cutter.val().BoundingBox()
                self.assertTrue(cutter.val().isValid())
                self.assertEqual(len(solids), 20)
                self.assertTrue(all(solid.isValid() for solid in solids))
                self.assertAlmostEqual(
                    sum(solid.Volume() for solid in solids),
                    236.4336138556583,
                    places=5,
                )
                self.assertAlmostEqual(bounding_box.xlen, 0.8, places=5)
                self.assertAlmostEqual(bounding_box.ylen, 51.85504577291667, places=5)
                self.assertAlmostEqual(bounding_box.zlen, 16.159993689583338, places=5)


class DxfRegionValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.logo_path = files("print_models.assets.logos").joinpath(
            "five_crowns_lid_logo_from_source_section.dxf"
        )

    def test_rejects_repeated_wire_indices(self) -> None:
        import cadquery as cq

        with self.assertRaisesRegex(ValueError, "repeats a wire index"):
            extrude_dxf_regions(
                cq,
                path=self.logo_path,
                height=1.0,
                regions=((0, (0,)),),
            )

    def test_rejects_missing_wire_indices(self) -> None:
        import cadquery as cq

        with self.assertRaisesRegex(ValueError, "references a missing wire"):
            extrude_dxf_regions(
                cq,
                path=self.logo_path,
                height=1.0,
                regions=((99, ()),),
            )

    def test_rejects_unaccounted_wires(self) -> None:
        import cadquery as cq

        with self.assertRaisesRegex(ValueError, "does not account for all"):
            extrude_dxf_regions(
                cq,
                path=self.logo_path,
                height=1.0,
                regions=((0, ()),),
            )


if __name__ == "__main__":
    unittest.main()
