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
"""Run the seven feature-extraction tools on a synthetic valley whose
answers are known exactly (see ``synthetic.py``) and check every extracted
feature against them."""
import math
import unittest

import bootstrap
from bootstrap import alg
from synthetic import (
    EXPECTED,
    INT,
    channel_belt_layer,
    dem_layer,
    elevation,
    geology_layer,
    line_layer,
    point_layer,
    precip_layer,
    river_layer,
    valley_lines_layer,
)

TMP = "TEMPORARY_OUTPUT"
FEATURES = ["ELE", "PRE", "GEO", "VFW", "VW", "RAT", "LVS", "RVS", "MVS",
            "DVS", "SIN", "CBW", "LCS", "RCS", "CBS"]


def setUpModule():
    bootstrap.setup()


def only_feature(testcase, layer):
    feats = list(layer.getFeatures())
    testcase.assertEqual(len(feats), 1, f"expected 1 feature in {layer.name()}, got {len(feats)}")
    return feats[0]


def is_null(value):
    from qgis.core import NULL

    return value is None or value == NULL


class TestSyntheticValleyWorkflow(unittest.TestCase):
    """Tools [1]-[7] run in sequence, exactly as in the README walkthrough."""

    @classmethod
    def setUpClass(cls):
        import processing

        cls._tmp = bootstrap.scratch_dir("synthetic")
        dem = dem_layer(cls._tmp)
        precip = precip_layer(cls._tmp)

        cls.s1 = processing.run(alg("generate_transects"), {
            "RIVER_LAYER": river_layer(), "LINE_LAYER": valley_lines_layer(),
            "EXTENSION_INCREMENT": 250, "MAX_LENGTH": 50000,
            "TRANSECTS": TMP, "CENTER_POINTS": TMP, "OUTPUT_STREAM": TMP,
        })
        s2 = processing.run(alg("extract_point_attributes"), {
            "POINTS": cls.s1["CENTER_POINTS"], "RASTER1": dem, "RASTER2": precip,
            "POLYGONS": geology_layer(), "POLY_FIELD": "GEOLOGY", "OUTPUT": TMP,
        })
        cls.s3 = processing.run(alg("extract_valley_width"), {
            "TRANSECTS": cls.s1["TRANSECTS"], "CENTER_POINTS": s2["OUTPUT"],
            "VALLEY_LINES": valley_lines_layer(), "STREAM_NETWORK": cls.s1["OUTPUT_STREAM"],
            "LEFT_VFW": TMP, "RIGHT_VFW": TMP, "LEFT_VW": TMP, "RIGHT_VW": TMP, "CENTER_OUT": TMP,
        })
        s4 = processing.run(alg("extract_side_slopes"), {
            "CENTER": cls.s3["CENTER_OUT"],
            "LEFT_VW": cls.s3["LEFT_VW"], "LEFT_VFW": cls.s3["LEFT_VFW"],
            "RIGHT_VW": cls.s3["RIGHT_VW"], "RIGHT_VFW": cls.s3["RIGHT_VFW"],
            "RASTER": dem, "OUTPUT": TMP,
        })
        s5 = processing.run(alg("extract_dvs_sinuosity"), {
            "CENTER_POINTS": s4["OUTPUT"], "STREAM_SEGMENTS": cls.s1["OUTPUT_STREAM"],
            "ELEVATION": dem, "OUTPUT": TMP,
        })
        s6 = processing.run(alg("extract_cbw"), {
            "TRANSECTS": cls.s1["TRANSECTS"], "CENTER_POINTS": s5["OUTPUT"],
            "CHANNEL_BELT": channel_belt_layer(), "STREAM_NETWORK": cls.s1["OUTPUT_STREAM"],
            "LEFT_CB": TMP, "RIGHT_CB": TMP, "CENTER_OUT": TMP,
        })
        s7 = processing.run(alg("extract_channel_belt_sinuosity"), {
            "CENTER_POINTS": s6["CENTER_OUT"], "CHANNEL_BELT": channel_belt_layer(), "OUTPUT": TMP,
        })
        cls.final = s7["OUTPUT"]

    @classmethod
    def tearDownClass(cls):
        cls.s1 = cls.s3 = cls.final = None
        bootstrap.remove_quietly(cls._tmp)

    def test_step1_generate_transects(self):
        transect = only_feature(self, self.s1["TRANSECTS"])
        self.assertEqual(transect["t_ID"], 0)
        self.assertGreaterEqual(transect["left_n"], 2)
        self.assertGreaterEqual(transect["right_n"], 2)

        center = only_feature(self, self.s1["CENTER_POINTS"]).geometry().asPoint()
        self.assertAlmostEqual(center.x(), 2005.0, places=6)
        self.assertAlmostEqual(center.y(), 0.0, places=6)
        self.assertEqual(only_feature(self, self.s1["OUTPUT_STREAM"])["t_ID"], 0)

    def test_step3_reference_points_on_correct_lines(self):
        """1st intersection on each side = valley floor line; 2nd = valley top."""
        expected_y = {"LEFT_VFW": 300.0, "LEFT_VW": 900.0, "RIGHT_VFW": -100.0, "RIGHT_VW": -2100.0}
        for key, y in expected_y.items():
            with self.subTest(output=key):
                pt = only_feature(self, self.s3[key]).geometry().asPoint()
                self.assertAlmostEqual(pt.y(), y, places=6)

    def test_all_fifteen_features(self):
        feat = only_feature(self, self.final)
        for field in FEATURES:
            with self.subTest(feature=field):
                self.assertIn(field, feat.fields().names(), f"{field} missing from output")
                value, expected = feat[field], EXPECTED[field]
                if isinstance(expected, str):
                    self.assertEqual(value, expected)
                else:
                    self.assertFalse(is_null(value), f"{field} is NULL")
                    self.assertTrue(math.isclose(float(value), expected, rel_tol=1e-6, abs_tol=1e-6),
                                    f"{field} = {value}, expected {expected}")


class TestSingleTools(unittest.TestCase):
    def test_dvs_and_sinuosity_on_meandering_reach(self):
        """SIN = channel length / straight-line distance;
        DVS = elevation drop / channel length x 100."""
        import processing

        zigzag = [(5.0, 0.0), (1005.0, 1000.0), (2005.0, 0.0)]
        length = 2 * math.hypot(1000.0, 1000.0)
        centers = point_layer("centers", [(1005.0, 1000.0)], fields=[("t_ID", INT)], attrs=[[0]])
        tmp = bootstrap.scratch_dir("synthetic")
        out = processing.run(alg("extract_dvs_sinuosity"), {
            "CENTER_POINTS": centers, "STREAM_SEGMENTS": river_layer(zigzag, t_id=0),
            "ELEVATION": dem_layer(tmp), "OUTPUT": TMP,
        })["OUTPUT"]
        feat = only_feature(self, out)
        out = None
        bootstrap.remove_quietly(tmp)
        drop = elevation(5.0, 0.0) - elevation(2005.0, 0.0)
        self.assertAlmostEqual(feat["SIN"], length / 2000.0, places=6)
        self.assertAlmostEqual(feat["DVS"], drop / length * 100.0, places=6)

    def test_valley_width_null_when_one_side_open(self):
        """No valley-floor intersection on one side -> VFW, VW, RAT are NULL."""
        import processing

        transect = line_layer("t", [[(2005.0, -2250.0), (2005.0, 0.0), (2005.0, 1000.0)]],
                              fields=[("t_ID", INT)], attrs=[[0]])
        centers = point_layer("c", [(2005.0, 0.0)], fields=[("t_ID", INT)], attrs=[[0]])
        left_only = line_layer("v", [[(-500.0, 300.0), (4505.0, 300.0)],
                                     [(-500.0, 900.0), (4505.0, 900.0)]])
        out = processing.run(alg("extract_valley_width"), {
            "TRANSECTS": transect, "CENTER_POINTS": centers, "VALLEY_LINES": left_only,
            "STREAM_NETWORK": river_layer(t_id=0),
            "LEFT_VFW": TMP, "RIGHT_VFW": TMP, "LEFT_VW": TMP, "RIGHT_VW": TMP, "CENTER_OUT": TMP,
        })["CENTER_OUT"]
        feat = only_feature(self, out)
        for field in ("VFW", "VW", "RAT"):
            with self.subTest(field=field):
                self.assertTrue(is_null(feat[field]), f"{field} = {feat[field]}, expected NULL")


if __name__ == "__main__":
    unittest.main()
