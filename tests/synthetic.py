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
r"""A synthetic valley with analytically known hydrogeomorphic features.

Geometry (projected CRS, metres; river flows in +x, so +y is river-left)::

        y = +900  ------------------------------  left valley top     (2nd left)
        y = +300  ------------------------------  left valley floor   (1st left)
        y =  +50  ..............................  left channel belt
        y =    0  ====== river (5,0)->(4005,0) =
        y =  -80  .\/\............/\/..........  right channel belt (zig-zag)
        y = -100  ------------------------------  right valley floor  (1st right)
        y = -2100 ------------------------------  right valley top    (2nd right)

The valley is deliberately asymmetric: transect extension stops at 1000 m on
the left and 2250 m on the right, so the transect's own midpoint sits 625 m
from the river, beyond the right valley-floor line. This is the case that
exposed the VFW reference-point bug.

Elevation  z(x, y) = 100 - 0.01 (x - 5) + { 0.10 y   if y > 0
                                           { 0.05 |y| if y <= 0
sampled on a 10 m grid whose cell centres fall exactly on every point the
algorithms sample (x = ...5, y = ...0), so expected values are exact.
"""
import math
from pathlib import Path

from osgeo import gdal, osr
from qgis.core import (
    QgsCoordinateReferenceSystem,
    QgsFeature,
    QgsField,
    QgsGeometry,
    QgsPointXY,
    QgsRasterLayer,
    QgsVectorLayer,
)
from qgis.PyQt.QtCore import QMetaType

try:  # QGIS >= 3.38 / QGIS 4
    INT, STRING = QMetaType.Type.Int, QMetaType.Type.QString
except AttributeError:  # older QGIS 3.x
    from qgis.PyQt.QtCore import QVariant

    INT, STRING = QVariant.Int, QVariant.String

EPSG = 32734  # WGS 84 / UTM 34S (same CRS as the Eerste sample data)

RIVER = [(5.0, 0.0), (4005.0, 0.0)]
VALLEY_Y = {"left_floor": 300.0, "left_top": 900.0, "right_floor": -100.0, "right_top": -2100.0}
BELT_LEFT_Y = 50.0
# zig-zag with a flat reach through x = 2005 so the transect crosses mid-segment
BELT_RIGHT = [(5.0, -80.0), (1005.0, -180.0), (1805.0, -80.0), (2205.0, -80.0), (3005.0, -180.0), (4005.0, -80.0)]
PRECIP = 750.0
GEOLOGY = "alluvial"

# ---- analytic expectations -------------------------------------------------
EXPECTED = {
    "VFW": VALLEY_Y["left_floor"] - VALLEY_Y["right_floor"],          # 400
    "VW": VALLEY_Y["left_top"] - VALLEY_Y["right_top"],               # 3000
    "LVS": 10.0,   # 0.10 rise per metre of run, in percent
    "RVS": 5.0,    # 0.05 rise per metre of run, in percent
    "ELE": 100.0 - 0.01 * (2005.0 - 5.0),                             # 80
    "PRE": PRECIP,
    "GEO": GEOLOGY,
    "DVS": (0.01 * 4000.0) / 4000.0 * 100.0,                          # 1 %
    "SIN": 1.0,
    "CBW": BELT_LEFT_Y - (-80.0),                                     # 130
    "LCS": 1.0,
}
EXPECTED["RAT"] = EXPECTED["VW"] / EXPECTED["VFW"]
EXPECTED["MVS"] = (EXPECTED["LVS"] + EXPECTED["RVS"]) / 2.0
EXPECTED["RCS"] = (2 * math.hypot(1000.0, 100.0) + 2 * math.hypot(800.0, 100.0) + 400.0) / 4000.0
EXPECTED["CBS"] = (EXPECTED["LCS"] + EXPECTED["RCS"]) / 2.0


def elevation(x, y):
    side = 0.10 * y if y > 0 else 0.05 * -y
    return 100.0 - 0.01 * (x - 5.0) + side


def _crs():
    return QgsCoordinateReferenceSystem(f"EPSG:{EPSG}")


def line_layer(name, lines, fields=(), attrs=None):
    """Memory line layer. ``lines`` is a list of vertex lists."""
    layer = QgsVectorLayer(f"LineString?crs=EPSG:{EPSG}", name, "memory")
    dp = layer.dataProvider()
    if fields:
        dp.addAttributes([QgsField(n, t) for n, t in fields])
        layer.updateFields()
    feats = []
    for i, verts in enumerate(lines):
        f = QgsFeature(layer.fields())
        f.setGeometry(QgsGeometry.fromPolylineXY([QgsPointXY(x, y) for x, y in verts]))
        if attrs:
            f.setAttributes(list(attrs[i]))
        feats.append(f)
    dp.addFeatures(feats)
    layer.updateExtents()
    assert layer.isValid()
    return layer


def point_layer(name, points, fields=(), attrs=None):
    layer = QgsVectorLayer(f"Point?crs=EPSG:{EPSG}", name, "memory")
    dp = layer.dataProvider()
    if fields:
        dp.addAttributes([QgsField(n, t) for n, t in fields])
        layer.updateFields()
    feats = []
    for i, (x, y) in enumerate(points):
        f = QgsFeature(layer.fields())
        f.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(x, y)))
        if attrs:
            f.setAttributes(list(attrs[i]))
        feats.append(f)
    dp.addFeatures(feats)
    layer.updateExtents()
    assert layer.isValid()
    return layer


def river_layer(vertices=RIVER, t_id=None):
    if t_id is None:
        return line_layer("river", [vertices])
    return line_layer("river", [vertices], fields=[("t_ID", INT)], attrs=[[t_id]])


def valley_lines_layer():
    lines = [[(-500.0, y), (4505.0, y)] for y in VALLEY_Y.values()]
    return line_layer("valley_lines", lines)


def channel_belt_layer():
    left = [(5.0, BELT_LEFT_Y), (4005.0, BELT_LEFT_Y)]
    return line_layer(
        "channel_belt",
        [left, BELT_RIGHT],
        fields=[("t_ID", INT), ("side", STRING)],
        attrs=[[0, "LEFT"], [0, "RIGHT"]],
    )


def geology_layer():
    layer = QgsVectorLayer(f"Polygon?crs=EPSG:{EPSG}", "geology", "memory")
    layer.dataProvider().addAttributes([QgsField("GEOLOGY", STRING)])
    layer.updateFields()
    f = QgsFeature(layer.fields())
    f.setGeometry(QgsGeometry.fromWkt("POLYGON((-500 -2500, 4505 -2500, 4505 1505, -500 1505, -500 -2500))"))
    f.setAttributes([GEOLOGY])
    layer.dataProvider().addFeatures([f])
    layer.updateExtents()
    return layer


def _write_raster(path, func):
    cell = 10.0
    x0, y0 = -500.0, 1505.0           # x centres end in 5, y centres are multiples of 10
    ncols, nrows = 501, 401           # covers x -500..4510, y 1505..-2505
    drv = gdal.GetDriverByName("GTiff")
    ds = drv.Create(str(path), ncols, nrows, 1, gdal.GDT_Float64)
    ds.SetGeoTransform((x0, cell, 0.0, y0, 0.0, -cell))
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(EPSG)
    ds.SetProjection(srs.ExportToWkt())
    band = ds.GetRasterBand(1)
    rows = []
    for r in range(nrows):
        yc = y0 - (r + 0.5) * cell
        rows.append([func(x0 + (c + 0.5) * cell, yc) for c in range(ncols)])
    try:
        import numpy as np

        band.WriteArray(np.array(rows, dtype="float64"))
    except ImportError:  # pragma: no cover - numpy ships with QGIS
        import struct

        for r, row in enumerate(rows):
            band.WriteRaster(0, r, ncols, 1, struct.pack(f"{ncols}d", *row))
    band.FlushCache()
    ds = None
    layer = QgsRasterLayer(str(path), Path(path).stem)
    assert layer.isValid(), f"could not load {path}"
    return layer


def dem_layer(tmp_dir):
    return _write_raster(Path(tmp_dir) / "dem.tif", elevation)


def precip_layer(tmp_dir):
    return _write_raster(Path(tmp_dir) / "precip.tif", lambda x, y: PRECIP)
