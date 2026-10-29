"""Verify the actual vendored country/flag links and redistribution notices."""
import hashlib
import json
from pathlib import Path
import unittest

from PIL import Image


ASSETS = Path(__file__).resolve().parents[1] / "assets"


class LicensedAssetTests(unittest.TestCase):
    def test_vendored_catalog_integrity_and_country_mapping(self):
        manifest = json.loads((ASSETS / "asset_manifest.json").read_text(encoding="utf-8"))
        countries = json.loads((ASSETS / "countries.json").read_text(encoding="utf-8"))
        upstream = json.loads((ASSETS / "country_source_upstream.json").read_text(encoding="utf-8"))
        expected_names = {row["code"].lower(): row["name"] for row in upstream}
        self.assertEqual(len(countries), manifest["count"])
        self.assertGreaterEqual(len(countries), 40)
        self.assertEqual(len({row["code"] for row in countries}), len(countries))
        self.assertEqual(len({row["name"] for row in countries}), len(countries))
        self.assertEqual({row["difficulty"] for row in countries}, {"Easy", "Normal", "Hard"})
        self.assertEqual(hashlib.sha256((ASSETS / "countries.json").read_bytes()).hexdigest(),
                         manifest["country_manifest_sha256"])
        self.assertEqual(hashlib.sha256((ASSETS / "country_source_upstream.json").read_bytes()).hexdigest(),
                         manifest["upstream_country_data_sha256"])
        for row in countries:
            with self.subTest(country=row["code"]):
                self.assertEqual(row["name"], expected_names[row["code"]])
                self.assertEqual(row["license"], "MIT")
                self.assertIn(manifest["revision"], row["source"])
                self.assertTrue(row["source"].endswith("/" + row["code"] + ".svg"))
                flag = ASSETS / row["flag"]
                self.assertEqual(flag.stem, row["code"])
                self.assertEqual(hashlib.sha256(flag.read_bytes()).hexdigest(), row["sha256"])
                with Image.open(flag) as image:
                    image.verify()
                with Image.open(flag) as image:
                    self.assertEqual(list(image.size), manifest["png_size"])
                svg = ASSETS / "source_svg" / (row["code"] + ".svg")
                self.assertEqual(hashlib.sha256(svg.read_bytes()).hexdigest(), row["source_svg_sha256"])

    def test_free_asset_license_notices_are_present(self):
        text = (ASSETS / "licenses" / "flag-icons-MIT.txt").read_text(encoding="utf-8")
        self.assertIn("Permission is hereby granted", text)
        font_license = (ASSETS / "licenses" / "DejaVu-font-license.txt").read_text(encoding="utf-8")
        self.assertIn("Permission is hereby granted", font_license)
        self.assertTrue((ASSETS / "fonts" / "DejaVuSans-Bold.ttf").is_file())


if __name__ == "__main__":
    unittest.main()
