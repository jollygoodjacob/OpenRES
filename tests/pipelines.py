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
"""The OpenRES workflow (tools [1]-[7]) and the two input datasets it is run
on. Shared by the tests and by inspect_results.py, so the layers you inspect
on the map are produced by exactly the same calls the tests check."""
from pathlib import Path

import bootstrap
from bootstrap import alg

TMP = "TEMPORARY_OUTPUT"


def synthetic_inputs(raster_dir):
    """The synthetic valley (see synthetic.py). Rasters are written to raster_dir."""
    import synthetic

    return {
        "river": synthetic.river_layer(),
        "valley": synthetic.valley_lines_layer(),
        "belt": synthetic.channel_belt_layer(),
        "geology": synthetic.geology_layer(),
        "geology_field": "GEOLOGY",
        "dem": synthetic.dem_layer(raster_dir),
        "precip": synthetic.precip_layer(raster_dir),
    }


def eerste_inputs():
    """The bundled Eerste River sample data (unzipped once, then reused)."""
    from qgis.core import QgsRasterLayer, QgsVectorLayer

    d = bootstrap.sample_data_dir()

    def vec(rel):
        layer = QgsVectorLayer(str(d / rel), Path(rel).stem, "ogr")
        assert layer.isValid(), f"could not open {d / rel}"
        return layer

    def ras(rel):
        layer = QgsRasterLayer(str(d / rel), Path(rel).stem)
        assert layer.isValid(), f"could not open {d / rel}"
        return layer

    return {
        "river": vec("Eerste_stream_network/Eerste_stream_network/Eerste_stream_network_2km_final.shp"),
        "valley": vec("Eerste_valley_boundary/Eerste_valley_boundary.shp"),
        "belt": vec("Eerste_channel_belt/Eerste_channel_belt.shp"),
        "geology": vec("Eerste_geology/Eerste_geology/Eerste_geology.shp"),
        "geology_field": "GEOLOGY",
        "dem": ras("Eerste_elevation/Eerste_elevation/Eerste_SRTM_30m_extent.tif"),
        "precip": ras("Eerste_precipitation/Eerste_MAP/Eerste_MAP_extent.tif"),
    }


def run_workflow(river, valley, belt, geology, geology_field, dem, precip):
    """Run tools [1]-[7] in order, exactly as in the README example.

    Returns a dict with each step's Processing result: "s1" ... "s7".
    The final layer with all 15 features is result["s7"]["OUTPUT"].
    """
    import processing

    s1 = processing.run(alg("generate_transects"), {
        "RIVER_LAYER": river, "LINE_LAYER": valley,
        "EXTENSION_INCREMENT": 250, "MAX_LENGTH": 50000,
        "TRANSECTS": TMP, "CENTER_POINTS": TMP, "OUTPUT_STREAM": TMP,
    })
    s2 = processing.run(alg("extract_point_attributes"), {
        "POINTS": s1["CENTER_POINTS"], "RASTER1": dem, "RASTER2": precip,
        "POLYGONS": geology, "POLY_FIELD": geology_field, "OUTPUT": TMP,
    })
    s3 = processing.run(alg("extract_valley_width"), {
        "TRANSECTS": s1["TRANSECTS"], "CENTER_POINTS": s2["OUTPUT"],
        "VALLEY_LINES": valley, "STREAM_NETWORK": s1["OUTPUT_STREAM"],
        "LEFT_VFW": TMP, "RIGHT_VFW": TMP, "LEFT_VW": TMP, "RIGHT_VW": TMP, "CENTER_OUT": TMP,
    })
    s4 = processing.run(alg("extract_side_slopes"), {
        "CENTER": s3["CENTER_OUT"], "LEFT_VW": s3["LEFT_VW"], "LEFT_VFW": s3["LEFT_VFW"],
        "RIGHT_VW": s3["RIGHT_VW"], "RIGHT_VFW": s3["RIGHT_VFW"],
        "RASTER": dem, "OUTPUT": TMP,
    })
    s5 = processing.run(alg("extract_dvs_sinuosity"), {
        "CENTER_POINTS": s4["OUTPUT"], "STREAM_SEGMENTS": s1["OUTPUT_STREAM"],
        "ELEVATION": dem, "OUTPUT": TMP,
    })
    s6 = processing.run(alg("extract_cbw"), {
        "TRANSECTS": s1["TRANSECTS"], "CENTER_POINTS": s5["OUTPUT"],
        "CHANNEL_BELT": belt, "STREAM_NETWORK": s1["OUTPUT_STREAM"],
        "LEFT_CB": TMP, "RIGHT_CB": TMP, "CENTER_OUT": TMP,
    })
    s7 = processing.run(alg("extract_channel_belt_sinuosity"), {
        "CENTER_POINTS": s6["CENTER_OUT"], "CHANNEL_BELT": belt, "OUTPUT": TMP,
    })
    return {"s1": s1, "s2": s2, "s3": s3, "s4": s4, "s5": s5, "s6": s6, "s7": s7}


# Layers worth looking at, in map order (top to bottom), with readable names.
INSPECT_OUTPUTS = [
    ("s7", "OUTPUT", "[7] Segment centers - all 15 features"),
    ("s3", "LEFT_VFW", "[3] Left valley-floor (VFW) point"),
    ("s3", "RIGHT_VFW", "[3] Right valley-floor (VFW) point"),
    ("s3", "LEFT_VW", "[3] Left valley-top (VW) point"),
    ("s3", "RIGHT_VW", "[3] Right valley-top (VW) point"),
    ("s6", "LEFT_CB", "[6] Left channel-belt point"),
    ("s6", "RIGHT_CB", "[6] Right channel-belt point"),
    ("s1", "TRANSECTS", "[1] Transects"),
    ("s1", "OUTPUT_STREAM", "[1] River network with t_ID"),
]
INSPECT_INPUTS = [
    ("valley", "Input: valley lines"),
    ("belt", "Input: channel belt"),
    ("geology", "Input: geology"),
    ("dem", "Input: DEM"),
    ("precip", "Input: precipitation"),
]
