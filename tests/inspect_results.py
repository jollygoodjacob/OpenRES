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
"""See what the tests see. Runs the same OpenRES workflow the tests run, on the
same two datasets, then:

* saves every input and output layer to a GeoPackage, plus the final feature
  table as CSV, in tests/output/<date_time>/
* adds them to your QGIS map in two groups, so you can measure, open attribute
  tables and compare with the expected values yourself
* prints, for the synthetic valley, each of the 15 features next to its
  expected value and how that value is worked out; and, for the Eerste sample,
  a summary of every feature plus any segment that breaks a physical check.

Run it from the QGIS Python Console (Plugins > Python Console):

    import runpy; _ = runpy.run_path(r"C:\\path\\to\\OpenRES\\tests\\inspect_results.py", run_name="__main__")

It does not change your installed OpenRES plugin. It can also be run from a
terminal with QGIS's Python (files are saved; nothing is shown on a map).
"""
import math
import statistics
import sys
from datetime import datetime
from pathlib import Path

FEATURES = ["ELE", "PRE", "GEO", "VFW", "VW", "RAT", "LVS", "RVS", "MVS",
            "DVS", "SIN", "CBW", "LCS", "RCS", "CBS"]
UNITS = {"ELE": "m", "PRE": "mm", "VFW": "m", "VW": "m", "CBW": "m",
         "LVS": "%", "RVS": "%", "MVS": "%", "DVS": "%"}


# ---- setup (same as run_tests.py) -------------------------------------------
def _tests_dir():
    try:
        return Path(__file__).resolve().parent
    except NameError:
        raise RuntimeError(
            "Run this file with runpy, e.g.\n"
            '  import runpy; _ = runpy.run_path(r"C:\\path\\to\\OpenRES\\tests\\inspect_results.py", '
            'run_name="__main__")'
        ) from None


def _prepare(tests_dir):
    for name, module in list(sys.modules.items()):
        path = getattr(module, "__file__", None) or ""
        if name == "openres_dev" or name.startswith("openres_dev."):
            del sys.modules[name]
        elif path and Path(path).resolve().parent == tests_dir:
            del sys.modules[name]
    if str(tests_dir) not in sys.path:
        sys.path.insert(0, str(tests_dir))


# ---- small helpers ------------------------------------------------------------
def _is_null(value):
    from qgis.core import NULL

    return value is None or value == NULL or (isinstance(value, float) and math.isnan(value))


def _fmt(value):
    if _is_null(value):
        return "NULL"
    if isinstance(value, (int, float)):
        return f"{value:,.4f}".rstrip("0").rstrip(".")
    return str(value)


def _save_vector(layer, gpkg, table):
    """Write a layer into a GeoPackage table and return the saved layer."""
    from qgis.core import QgsCoordinateTransformContext, QgsVectorFileWriter, QgsVectorLayer

    opts = QgsVectorFileWriter.SaveVectorOptions()
    opts.driverName = "GPKG"
    opts.layerName = table
    opts.actionOnExistingFile = (QgsVectorFileWriter.CreateOrOverwriteLayer if gpkg.exists()
                                 else QgsVectorFileWriter.CreateOrOverwriteFile)
    result = QgsVectorFileWriter.writeAsVectorFormatV3(layer, str(gpkg), QgsCoordinateTransformContext(), opts)
    if result[0] != QgsVectorFileWriter.NoError:
        raise RuntimeError(f"could not save {table} to {gpkg}: {result[1]}")
    return QgsVectorLayer(f"{gpkg}|layername={table}", table, "ogr")


def _save_csv(layer, path):
    from qgis.core import QgsCoordinateTransformContext, QgsVectorFileWriter

    opts = QgsVectorFileWriter.SaveVectorOptions()
    opts.driverName = "CSV"
    QgsVectorFileWriter.writeAsVectorFormatV3(layer, str(path), QgsCoordinateTransformContext(), opts)


def _style(layer, title):
    """Readable colours and labels so the important layers stand out."""
    from qgis.PyQt.QtGui import QColor

    colours = {
        "valley-floor": "#d7301f", "valley-top": "#7f0000", "channel-belt": "#41ab5d",
        "Transects": "#ff6011", "15 features": "#0000ff", "valley lines": "#636363",
        "channel belt": "#74c476", "River network": "#2171b5",
    }
    try:
        symbol = layer.renderer().symbol()
    except AttributeError:  # rasters, polygons with other renderers
        return
    for key, colour in colours.items():
        if key in title:
            symbol.setColor(QColor(colour))
    if "geology" in title.lower():
        symbol.setOpacity(0.25)


def _label(layer, expression):
    from qgis.core import QgsPalLayerSettings, QgsTextFormat, QgsVectorLayerSimpleLabeling

    settings = QgsPalLayerSettings()
    settings.fieldName = expression
    settings.isExpression = True
    fmt = QgsTextFormat()
    fmt.setSize(9)
    settings.setFormat(fmt)
    layer.setLabeling(QgsVectorLayerSimpleLabeling(settings))
    layer.setLabelsEnabled(True)


def _add_group(name, layers):
    """Add (title, layer) pairs to the QGIS map in a new group, if QGIS is open."""
    from qgis.core import QgsProject

    try:
        from qgis.utils import iface
    except ImportError:
        iface = None
    if iface is None:
        return None
    project = QgsProject.instance()
    group = project.layerTreeRoot().insertGroup(0, name)
    for title, layer in layers:
        layer.setName(title)
        project.addMapLayer(layer, False)
        group.addLayer(layer)
    return group


# ---- the two datasets ---------------------------------------------------------
def inspect_synthetic(out_dir):
    import pipelines
    import synthetic

    folder = out_dir / "synthetic_valley"
    folder.mkdir(parents=True, exist_ok=True)
    inputs = pipelines.synthetic_inputs(folder)
    steps = pipelines.run_workflow(**inputs)
    final = steps["s7"]["OUTPUT"]

    print("=" * 100)
    print("SYNTHETIC VALLEY: every feature should equal the value worked out by hand")
    print("(segment centre at x = 2005, y = 0; +y is river-left; units are metres)")
    print("=" * 100)
    feats = list(final.getFeatures())
    if len(feats) != 1:
        print(f"!! expected exactly 1 segment centre, got {len(feats)}")
    feat = feats[0] if feats else None
    print(f"{'feature':8} {'OpenRES':>12} {'expected':>12}  {'':5} how the expected value is worked out")
    n_bad = 0
    for field in FEATURES:
        expected = synthetic.EXPECTED[field]
        value = feat[field] if feat is not None and field in feat.fields().names() else None
        if isinstance(expected, str):
            ok = value == expected
        else:
            ok = (not _is_null(value)) and math.isclose(float(value), expected, rel_tol=1e-6, abs_tol=1e-6)
        n_bad += not ok
        print(f"{field:8} {_fmt(value):>12} {_fmt(expected):>12}  {'ok' if ok else 'WRONG':5} {synthetic.EXPLAIN[field]}")
    print(f"\n{15 - n_bad} of 15 features match." + ("" if n_bad == 0 else f"  {n_bad} DO NOT MATCH."))

    gpkg = folder / "synthetic_valley.gpkg"
    layers = []
    for step, key, title in pipelines.INSPECT_OUTPUTS:
        saved = _save_vector(steps[step][key], gpkg, f"{step}_{key.lower()}")
        _style(saved, title)
        layers.append((title, saved))
    for key, title in pipelines.INSPECT_INPUTS:
        from qgis.core import QgsVectorLayer

        layer = inputs[key]
        if isinstance(layer, QgsVectorLayer):  # in-memory: save so it survives
            layer = _save_vector(layer, gpkg, f"input_{key}")
        _style(layer, title)
        layers.append((title, layer))
    _label(layers[0][1], "'VFW ' || round(\"VFW\") || ' m   VW ' || round(\"VW\") || ' m   CBW ' || round(\"CBW\") || ' m'")
    _save_csv(final, folder / "synthetic_valley_features.csv")
    group = _add_group("OpenRES test: synthetic valley", layers)
    print(f"\nSaved to: {folder}")
    return group, layers


def inspect_eerste(out_dir):
    import pipelines

    folder = out_dir / "eerste_sample"
    folder.mkdir(parents=True, exist_ok=True)
    inputs = pipelines.eerste_inputs()
    steps = pipelines.run_workflow(**inputs)
    final = steps["s7"]["OUTPUT"]
    feats = list(final.getFeatures())

    print("\n" + "=" * 100)
    print("EERSTE RIVER SAMPLE: no hand-worked answers, so check ranges and physical consistency")
    print("=" * 100)
    print(f"river segments: {inputs['river'].featureCount()}   transects made: "
          f"{steps['s1']['TRANSECTS'].featureCount()}   segment centres with features: {len(feats)}\n")
    print(f"{'feature':8} {'filled':>8} {'min':>12} {'median':>12} {'max':>12}  units")
    for field in FEATURES:
        values = [f[field] for f in feats if not _is_null(f[field])]
        if field == "GEO":
            classes = sorted({str(v) for v in values})
            print(f"{field:8} {len(values):>5}/{len(feats):<3} classes: {', '.join(classes)}")
            continue
        nums = [float(v) for v in values]
        if nums:
            print(f"{field:8} {len(nums):>5}/{len(feats):<3}{min(nums):>12,.3f} {statistics.median(nums):>12,.3f} "
                  f"{max(nums):>12,.3f}  {UNITS.get(field, '')}")
        else:
            print(f"{field:8} {0:>5}/{len(feats):<3}  (all NULL)")

    checks = {
        "ELE missing or -9999": lambda f: _is_null(f["ELE"]) or f["ELE"] == -9999,
        "PRE missing or <= 0": lambda f: _is_null(f["PRE"]) or f["PRE"] <= 0,
        "VFW > VW (floor wider than valley)": lambda f: not _is_null(f["VFW"]) and not _is_null(f["VW"]) and f["VFW"] > f["VW"],
        "RAT < 1": lambda f: not _is_null(f["RAT"]) and f["RAT"] < 1,
        "negative slope (LVS/RVS/MVS/DVS)": lambda f: any(not _is_null(f[k]) and f[k] < 0 for k in ("LVS", "RVS", "MVS", "DVS")),
        "sinuosity < 1 (SIN/LCS/RCS/CBS)": lambda f: any(not _is_null(f[k]) and f[k] < 1 - 1e-9 for k in ("SIN", "LCS", "RCS", "CBS")),
        "CBW wider than VW": lambda f: not _is_null(f["CBW"]) and not _is_null(f["VW"]) and f["CBW"] > f["VW"],
    }
    print("\nphysical checks (the test fails if any segment breaks one):")
    for name, broken in checks.items():
        bad = [f["t_ID"] for f in feats if broken(f)]
        shown = ", ".join(str(t) for t in bad[:15]) + (" ..." if len(bad) > 15 else "")
        print(f"  {'ok  ' if not bad else 'FAIL'} {name}: {len(bad)} segment(s){' -> t_ID ' + shown if bad else ''}")

    gpkg = folder / "eerste_sample.gpkg"
    layers = []
    for step, key, title in pipelines.INSPECT_OUTPUTS:
        saved = _save_vector(steps[step][key], gpkg, f"{step}_{key.lower()}")
        _style(saved, title)
        layers.append((title, saved))
    for key, title in pipelines.INSPECT_INPUTS:
        layer = inputs[key].clone()
        _style(layer, title)
        layers.append((title, layer))
    _label(layers[0][1], '"t_ID"')
    _save_csv(final, folder / "eerste_features.csv")
    group = _add_group("OpenRES test: Eerste sample", layers)
    print(f"\nSaved to: {folder}")
    return group, layers


def main():
    tests_dir = _tests_dir()
    _prepare(tests_dir)
    import bootstrap

    bootstrap.setup()
    from qgis.core import QgsProject

    project_was_empty = not QgsProject.instance().mapLayers()
    out_dir = tests_dir / "output" / datetime.now().strftime("%Y-%m-%d_%H%M%S")
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"Running the test workflow with OpenRES from: {bootstrap.REPO_ROOT}\n")

    try:
        syn_group, syn_layers = inspect_synthetic(out_dir)
        eer_group, _ = inspect_eerste(out_dir)
    finally:
        bootstrap.teardown()

    try:
        from qgis.utils import iface
    except ImportError:
        iface = None
    if iface is not None and syn_group is not None:
        from qgis.core import QgsCoordinateReferenceSystem

        if project_was_empty:  # so the Measure tool reports metres in the test CRS
            QgsProject.instance().setCrs(QgsCoordinateReferenceSystem("EPSG:32734"))
        if eer_group is not None:
            eer_group.setExpanded(False)
        extent = syn_layers[-2][1].extent()  # the synthetic DEM
        iface.mapCanvas().setExtent(extent)
        iface.mapCanvas().refresh()
        print("""
WHAT TO LOOK AT
* The map is zoomed to the synthetic valley. The blue point is the segment centre,
  labelled with VFW, VW and CBW. Red points are where the transect meets the
  valley-floor lines, dark red the valley-top lines, green the channel belt.
* Measure it yourself: View > Measure > Measure Line, click the left and right
  valley-floor (red) points: that distance is VFW (should be 400 m). Do the same
  for the dark red points (VW, 3000 m) and the green points (CBW, 130 m).
* Open the attribute table of "[7] Segment centers - all 15 features" to see
  every value. Use the Identify tool on the DEM to check elevations.
* For the Eerste sample, right-click its group > Zoom to Group, and check any
  t_ID listed under the physical checks above.
* Everything is also saved as GeoPackage + CSV in the folder printed above, so
  you can reopen it later or load it in R.""")


if __name__ == "__main__":
    main()
