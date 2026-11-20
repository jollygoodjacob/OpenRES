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
"""End-to-end run of tools [1]-[7] on the bundled Eerste River sample data
(the README walkthrough). Checks that every output is produced and that the
extracted features are physically consistent."""
import unittest

import bootstrap
import pipelines

ALL_FIELDS = ["t_ID", "ELE", "PRE", "GEO", "VFW", "VW", "RAT", "LVS", "RVS", "MVS",
              "DVS", "SIN", "CBW", "LCS", "RCS", "CBS"]


def setUpModule():
    bootstrap.setup()


def is_null(value):
    from qgis.core import NULL

    return value is None or value == NULL


class TestEersteSampleWorkflow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        inputs = pipelines.eerste_inputs()
        cls.river = inputs["river"]
        steps = pipelines.run_workflow(**inputs)
        cls.s1 = steps["s1"]
        cls.final = steps["s7"]["OUTPUT"]
        cls.features = list(cls.final.getFeatures())

    def test_one_center_per_transect(self):
        n_transects = self.s1["TRANSECTS"].featureCount()
        self.assertGreater(n_transects, 0)
        self.assertEqual(len(self.features), n_transects)
        # Almost every 2 km reach in the sample lies inside the delineated valley.
        self.assertGreaterEqual(n_transects, 0.9 * self.river.featureCount())

    def test_all_fifteen_features_present(self):
        names = self.final.fields().names()
        self.assertEqual([f for f in ALL_FIELDS if f not in names], [], "missing output fields")

    def test_transect_ids_unique_and_joinable(self):
        ids = [f["t_ID"] for f in self.features]
        self.assertEqual(len(ids), len(set(ids)), "duplicate t_ID values")
        stream_ids = {f["t_ID"] for f in self.s1["OUTPUT_STREAM"].getFeatures() if not is_null(f["t_ID"])}
        self.assertEqual(set(ids), stream_ids, "t_IDs do not match the river network output")

    def test_features_physically_plausible(self):
        problems = []
        for f in self.features:
            t = f["t_ID"]

            def check(ok, msg):
                if not ok:
                    problems.append(f"t_ID {t}: {msg}")

            check(not is_null(f["ELE"]) and f["ELE"] != -9999, f"ELE = {f['ELE']}")
            check(not is_null(f["PRE"]) and f["PRE"] > 0, f"PRE = {f['PRE']}")
            vfw, vw = f["VFW"], f["VW"]
            if not is_null(vfw) and not is_null(vw):
                check(0 < vfw <= vw, f"expected 0 < VFW ({vfw:.1f}) <= VW ({vw:.1f})")
                check(f["RAT"] >= 1, f"RAT = {f['RAT']}")
            for k in ("LVS", "RVS", "MVS", "DVS"):
                if not is_null(f[k]):
                    check(f[k] >= 0, f"{k} = {f[k]}")
            for k in ("SIN", "LCS", "RCS", "CBS"):
                if not is_null(f[k]):
                    check(f[k] >= 1 - 1e-9, f"{k} = {f[k]}")
            if not is_null(f["CBW"]) and not is_null(vw):
                check(f["CBW"] <= vw, f"CBW ({f['CBW']:.1f}) wider than valley ({vw:.1f})")
        self.assertEqual(problems, [], "\n" + "\n".join(problems[:25]))

    def test_core_features_mostly_populated(self):
        for k in ("VFW", "VW", "LVS", "RVS", "DVS", "SIN"):
            with self.subTest(feature=k):
                filled = sum(not is_null(f[k]) for f in self.features)
                self.assertGreaterEqual(filled, 0.8 * len(self.features),
                                        f"only {filled}/{len(self.features)} centers have {k}")


if __name__ == "__main__":
    unittest.main()
