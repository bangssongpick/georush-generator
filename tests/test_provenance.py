import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from georush.catalog import Catalog, CatalogError

ASSETS = Path(__file__).resolve().parents[1]/'assets'


class ProductionProvenanceTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.root = Path(self.folder.name)
        for name in ('countries.json', 'asset_manifest.json', 'country_source_upstream.json'):
            shutil.copy2(ASSETS/name, self.root/name)

    def tearDown(self):
        self.folder.cleanup()

    def test_changed_country_data_refused(self):
        countries = json.loads((self.root/'countries.json').read_text())
        countries[0]['name'] = 'Incorrect country'
        (self.root/'countries.json').write_text(json.dumps(countries))
        with self.assertRaises(CatalogError):
            Catalog(self.root)

    def test_wrong_mapping_refused_even_if_catalog_hash_updated(self):
        countries = json.loads((self.root/'countries.json').read_text())
        countries[0]['name'], countries[1]['name'] = countries[1]['name'], countries[0]['name']
        path = self.root/'countries.json'
        path.write_text(json.dumps(countries))
        manifest_path = self.root/'asset_manifest.json'
        manifest = json.loads(manifest_path.read_text())
        manifest['country_manifest_sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
        manifest_path.write_text(json.dumps(manifest))
        with self.assertRaises(CatalogError):
            Catalog(self.root)

    def test_missing_provenance_refused(self):
        (self.root/'country_source_upstream.json').unlink()
        with self.assertRaises(CatalogError):
            Catalog(self.root)


if __name__ == '__main__':
    unittest.main()
