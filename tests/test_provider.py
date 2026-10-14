# OpenRES: Open Riverine Ecosystem Synthesis
# Copyright (C) 2025  Jacob Nesslage
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""The plugin loads and exposes every documented Processing algorithm."""
import configparser
import unittest

import bootstrap

EXPECTED_ALGORITHMS = {
    # Feature extraction ([1]-[7])
    "generate_transects",
    "extract_point_attributes",
    "extract_valley_width",
    "extract_side_slopes",
    "extract_dvs_sinuosity",
    "extract_cbw",
    "extract_channel_belt_sinuosity",
    # Geomorphology utilities
    "valley_floor_costdist",
    "generate_channel_belt",
    "GenerateMicroshedsAlgorithm",
    "createvalleyboundary",
}


def setUpModule():
    bootstrap.setup()


class TestProvider(unittest.TestCase):
    def test_all_algorithms_registered(self):
        names = {a.name() for a in bootstrap.provider().algorithms()}
        self.assertEqual(names, EXPECTED_ALGORITHMS)

    def test_algorithms_have_help_and_groups(self):
        for a in bootstrap.provider().algorithms():
            with self.subTest(algorithm=a.name()):
                self.assertTrue(a.displayName())
                self.assertIn(a.groupId(), {"feature_extraction", "geomorphology"})
                self.assertTrue(a.shortHelpString(), "missing help text")


class TestMetadata(unittest.TestCase):
    def test_metadata_has_required_keys(self):
        meta = configparser.ConfigParser()
        meta.read(bootstrap.REPO_ROOT / "metadata.txt", encoding="utf-8")
        general = meta["general"]
        for key in ("name", "version", "qgisMinimumVersion", "author", "email",
                    "repository", "tracker", "description", "about"):
            with self.subTest(key=key):
                self.assertTrue(general.get(key), f"metadata.txt is missing '{key}'")
        self.assertEqual(general["hasProcessingProvider"].strip().lower(), "yes")

    def test_citation_version_matches_metadata(self):
        meta = configparser.ConfigParser()
        meta.read(bootstrap.REPO_ROOT / "metadata.txt", encoding="utf-8")
        cff = (bootstrap.REPO_ROOT / "CITATION.cff").read_text(encoding="utf-8")
        cff_version = next(
            line.split(":", 1)[1].strip().strip('"')
            for line in cff.splitlines() if line.startswith("version:")
        )
        self.assertEqual(cff_version, meta["general"]["version"].strip(),
                         "CITATION.cff and metadata.txt list different versions")


if __name__ == "__main__":
    unittest.main()
