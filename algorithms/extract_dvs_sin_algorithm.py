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
    QgsProcessingAlgorithm,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterRasterLayer,
    QgsProcessingParameterFeatureSink,
    QgsProcessingContext,
    QgsProcessingFeedback,
    QgsFeatureSink,
    QgsField,
    QgsWkbTypes,
    QgsVectorLayer,
    QgsFeature,
    QgsRaster,
    QgsPointXY
)
from qgis.core import QgsProcessing
from PyQt5.QtCore import QVariant
from qgis.PyQt.QtGui import QColor
import math
from ..icon_utils import openres_icon

class ExtractDVSAlgorithm(QgsProcessingAlgorithm):
    CENTER_POINTS = 'CENTER_POINTS'
    STREAM_SEGMENTS = 'STREAM_SEGMENTS'
    ELEVATION = 'ELEVATION'
    OUTPUT = 'OUTPUT'

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterFeatureSource(self.CENTER_POINTS, "Segment Centers Layer", [QgsProcessing.TypeVectorPoint]))
        self.addParameter(QgsProcessingParameterFeatureSource(self.STREAM_SEGMENTS, "River Network Layer", [QgsProcessing.TypeVectorLine]))
        self.addParameter(QgsProcessingParameterRasterLayer(self.ELEVATION, "Elevation Raster Layer"))
        self.addParameter(QgsProcessingParameterFeatureSink(self.OUTPUT, "[5] Segment Centers"))

    def name(self):
        return "extract_dvs_sinuosity"

    def displayName(self):
        return "[5] Extract DVS and SIN"

    def group(self):
        return "Feature Extraction"

    def groupId(self):
        return "feature_extraction"

    def icon(self):
        return openres_icon("openres_provider.png")

    def shortHelpString(self):
        return (
            "Computes downstream valley slope (DVS) and channel sinuosity (SIN) "
            "for each segment center using the associated river segment geometry "
            "and elevation data.\n\n"
            "DVS is calculated from the elevation difference between the upstream "
            "and downstream ends of each stream segment, normalized by segment length. "
            "SIN is computed as the ratio of channel length to straight-line distance.\n\n"
            "Inputs:\n"
            "• Segment Centers Layer (points; must include t_id)\n"
            "• River Network Layer (lines; must include matching t_id)\n"
            "• Elevation Raster Layer\n\n"
            "Output:\n"
            "• [5] Segment Centers with added DVS and SIN attributes\n\n"
            "Notes:\n"
            "• DVS is reported as percent slope.\n"
            "• SIN values ≥ 1 indicate increasing channel sinuosity."
        )

    def createInstance(self):
        return ExtractDVSAlgorithm()

    def processAlgorithm(self, parameters, context: QgsProcessingContext, feedback: QgsProcessingFeedback):
        center_layer = self.parameterAsVectorLayer(parameters, self.CENTER_POINTS, context)
        stream_layer = self.parameterAsVectorLayer(parameters, self.STREAM_SEGMENTS, context)
        raster = self.parameterAsRasterLayer(parameters, self.ELEVATION, context)

        # Make editable copy of center points
        out_layer = QgsVectorLayer("Point?crs={}".format(center_layer.sourceCrs().authid()), "temp_center", "memory")
        out_dp = out_layer.dataProvider()
        out_dp.addAttributes(center_layer.fields())
        out_layer.updateFields()
        out_dp.addFeatures([f for f in center_layer.getFeatures()])

        # Add missing fields
        for name in ["DVS", "SIN"]:
            if out_layer.fields().indexFromName(name) == -1:
                out_dp.addAttributes([QgsField(name, QVariant.Double)])
        out_layer.updateFields()

        # Stream features by t_id
        stream_by_id = {f["t_id"]: f for f in stream_layer.getFeatures()}

        # Elevation helper
        def get_elev(pt):
            pt = pt if isinstance(pt, QgsPointXY) else QgsPointXY(pt.x(), pt.y())
            ident = raster.dataProvider().identify(pt, QgsRaster.IdentifyFormatValue)
            return ident.results().get(1, None) if ident.isValid() else None

        # Compute DVS and SIN
        out_layer.startEditing()
        dvs_idx = out_layer.fields().indexFromName("DVS")
        sin_idx = out_layer.fields().indexFromName("SIN")

        for i, feat in enumerate(out_layer.getFeatures()):
            t_id = feat["t_id"]
            stream = stream_by_id.get(t_id)
            if not stream:
                continue

            geom = stream.geometry()
            stream_points = list(geom.constGet().points()) if not geom.isMultipart() else list(geom.parts())[0].points()

            if len(stream_points) < 2:
                continue

            start, end = stream_points[0], stream_points[-1]
            elev_start, elev_end = get_elev(start), get_elev(end)

            if elev_start is None or elev_end is None:
                continue

            length = geom.length()
            straight = math.hypot(end.x() - start.x(), end.y() - start.y())

            if length > 0:
                dvs = ((elev_start - elev_end) / length) * 100
                dvs = max(dvs, 0.00001)
            else:
                dvs = None
                
            sin = (length / straight) if straight > 0 else None

            out_layer.changeAttributeValue(feat.id(), dvs_idx, dvs)
            out_layer.changeAttributeValue(feat.id(), sin_idx, sin)

            if i % 100 == 0:
                feedback.setProgress(int(100 * i / out_layer.featureCount()))

        out_layer.commitChanges()

        # Save output
        sink, dest_id = self.parameterAsSink(parameters, self.OUTPUT, context,
                                             out_layer.fields(), QgsWkbTypes.Point, out_layer.sourceCrs())
        for f in out_layer.getFeatures():
            sink.addFeature(f)

        center_layer = context.getMapLayer(dest_id)
        if center_layer:
            symbol = center_layer.renderer().symbol()
            symbol.setColor(QColor(0,0,255))  # blue
            symbol.setSize(3) # 3 mm
            center_layer.triggerRepaint()
            feedback.pushInfo("Applied blue symbology to segment centers.")

        return {self.OUTPUT: dest_id}
