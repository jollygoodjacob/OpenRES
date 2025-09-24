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

from qgis.core import (
    QgsVectorLayer,
    QgsFeature,
    QgsField,
    QgsPointXY,
    QgsRaster,
    QgsRasterLayer
)
from PyQt5.QtCore import QVariant
import math


def get_elevation_at_point(point, raster_layer):
    """
    Extract elevation value from raster at a given QgsPoint or QgsPointXY.

    Parameters:
        point (QgsPoint or QgsPointXY): Point to sample elevation at.
        raster_layer (QgsRasterLayer): Elevation raster.

    Returns:
        float or None: Elevation value or None if invalid.
    """
    pt_xy = point if isinstance(point, QgsPointXY) else QgsPointXY(point.x(), point.y())
    ident = raster_layer.dataProvider().identify(pt_xy, QgsRaster.IdentifyFormatValue)
    return ident.results().get(1, None) if ident.isValid() else None


def build_pairwise_slope_input(layer_a, layer_b, raster, id_field="t_id"):
    """
    Constructs dictionary with geometry-based distance and elevation extracted from raster.

    Parameters:
        layer_a (QgsVectorLayer): First layer (e.g., VW).
        layer_b (QgsVectorLayer): Second layer (e.g., VFW).
        raster (QgsRasterLayer): Elevation raster.
        id_field (str): Common ID field (e.g., 't_id').

    Returns:
        dict: {t_id: {'elev1': float, 'elev2': float, 'dist': float}}
    """
    dict_a = {f[id_field]: f for f in layer_a.getFeatures()}
    dict_b = {f[id_field]: f for f in layer_b.getFeatures()}

    slope_data = {}

    for t_id in dict_a:
        if t_id not in dict_b:
            continue

        feat1 = dict_a[t_id]
        feat2 = dict_b[t_id]
        pt1 = feat1.geometry().asPoint()
        pt2 = feat2.geometry().asPoint()

        elev1 = get_elevation_at_point(pt1, raster)
        elev2 = get_elevation_at_point(pt2, raster)

        if elev1 is None or elev2 is None:
            continue

        dist = math.hypot(pt2.x() - pt1.x(), pt2.y() - pt1.y())

        slope_data[t_id] = {
            "elev1": elev1,
            "elev2": elev2,
            "dist": dist
        }

    return slope_data


def calculate_side_slopes_from_pairs(center_points_layer,
                                     left_vw_layer, left_vfw_layer,
                                     right_vw_layer, right_vfw_layer,
                                     elevation_raster,
                                     id_field="t_id"):
    """
    Calculates LSS and RSS using paired intersection points and elevation sampled from raster.

    Parameters:
        center_points_layer (QgsVectorLayer): Centerline points where LVS and RVS will be written.
        left_vw_layer (QgsVectorLayer): Left side valley wall points.
        left_vfw_layer (QgsVectorLayer): Left side valley floor wall points.
        right_vw_layer (QgsVectorLayer): Right side valley wall points.
        right_vfw_layer (QgsVectorLayer): Right side valley floor wall points.
        elevation_raster (QgsRasterLayer): Elevation raster.
        id_field (str): Field to join all layers (e.g., 't_id').
    """
    # Add LSS and RSS fields if missing
    for field_name in ["LVS", "RVS"]:
        if center_points_layer.fields().indexFromName(field_name) == -1:
            center_points_layer.dataProvider().addAttributes([QgsField(field_name, QVariant.Double)])
    center_points_layer.updateFields()

    # Build slope info from raster
    left_slopes = build_pairwise_slope_input(left_vw_layer, left_vfw_layer, elevation_raster, id_field)
    right_slopes = build_pairwise_slope_input(right_vw_layer, right_vfw_layer, elevation_raster, id_field)

    # Start editing
    center_points_layer.startEditing()
    for feature in center_points_layer.getFeatures():
        t_id = feature[id_field]

        # Left Side Slope
        if t_id in left_slopes:
            l = left_slopes[t_id]
            elev_diff = abs(l["elev1"] - l["elev2"])
            slope = (elev_diff / l["dist"]) * 100 if l["dist"] > 0 else None
            feature["LVS"] = slope
        else:
            feature["LVS"] = None

        # Right Side Slope
        if t_id in right_slopes:
            r = right_slopes[t_id]
            elev_diff = abs(r["elev1"] - r["elev2"])
            slope = (elev_diff / r["dist"]) * 100 if r["dist"] > 0 else None
            feature["RVS"] = slope
        else:
            feature["RVS"] = None

        center_points_layer.updateFeature(feature)

    if center_points_layer.commitChanges():
        print("✅ LVS and RVS calculated using elevation raster.")
    else:
        print("❌ Failed to commit LVS and RVS.")
