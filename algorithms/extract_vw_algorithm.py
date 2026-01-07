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
    QgsProcessingParameterVectorLayer,
    QgsProcessingParameterFeatureSink,
    QgsWkbTypes,
    QgsProcessingContext,
    QgsProcessingFeedback,
    QgsFeatureSink,
    QgsField,
    QgsVectorLayer,
    QgsFeature,
    QgsGeometry,
    QgsPointXY,
    QgsSpatialIndex,
    QgsFields,
    QgsSimpleMarkerSymbolLayer
)
from qgis.core import QgsProcessing
from PyQt5.QtCore import QVariant
from qgis.PyQt.QtGui import QColor

from ..extract_valley_width import (
    find_two_intersections_by_side,
    add_points_in_batch,
    compute_valley_width
)
from ..icon_utils import openres_icon

class ExtractVWAlgorithm(QgsProcessingAlgorithm):
    TRANSECTS = 'TRANSECTS'
    CENTER_POINTS = 'CENTER_POINTS'
    VALLEY_LINES = 'VALLEY_LINES'
    STREAM_NETWORK = 'STREAM_NETWORK'
    LEFT_VFW = 'LEFT_VFW'
    RIGHT_VFW = 'RIGHT_VFW'
    LEFT_VW = 'LEFT_VW'
    RIGHT_VW = 'RIGHT_VW'
    CENTER_OUT = 'CENTER_OUT'

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterFeatureSource(self.TRANSECTS, "Transects Layer", [QgsProcessing.TypeVectorLine]))
        self.addParameter(QgsProcessingParameterFeatureSource(self.CENTER_POINTS, "Segment Centers Layer", [QgsProcessing.TypeVectorPoint]))
        self.addParameter(QgsProcessingParameterFeatureSource(self.VALLEY_LINES, "Valley Lines Layer", [QgsProcessing.TypeVectorLine]))
        self.addParameter(QgsProcessingParameterFeatureSource(self.STREAM_NETWORK, "River Network Layer", [QgsProcessing.TypeVectorLine]))

        self.addParameter(QgsProcessingParameterFeatureSink(self.LEFT_VFW, "Left VFW Reference"))
        self.addParameter(QgsProcessingParameterFeatureSink(self.RIGHT_VFW, "Right VFW Reference"))
        self.addParameter(QgsProcessingParameterFeatureSink(self.LEFT_VW, "Left VW Reference"))
        self.addParameter(QgsProcessingParameterFeatureSink(self.RIGHT_VW, "Right VW Reference"))
        self.addParameter(QgsProcessingParameterFeatureSink(self.CENTER_OUT, "[3] Segment Centers"))

    def name(self):
        return "extract_valley_width"

    def displayName(self):
        return "[3] Extract VW, VFW, and RAT"

    def group(self):
        return "Feature Extraction"

    def groupId(self):
        return "feature_extraction"

    def icon(self):
        return openres_icon("openres_provider.png")

    def shortHelpString(self):
        return (
            "Computes valley-floor width (VFW), valley width (VW), and their ratio (RAT) for each "
            "segment center using transects and valley boundary lines.\n\n"
            "The algorithm finds two intersections on the left and right side of each transect:\n"
            "• 1st intersection pair → VFW reference points\n"
            "• 2nd intersection pair → VW reference points\n\n"
            "Inputs:\n"
            "• Transects Layer (lines)\n"
            "• Segment Centers Layer (points; must include t_ID)\n"
            "• Valley Lines Layer (lines)\n"
            "• River Network Layer (lines)\n\n"
            "Outputs:\n"
            "• Left/Right VFW Reference (points)\n"
            "• Left/Right VW Reference (points)\n"
            "• [3] Segment Centers with added fields VFW, VW, and RAT\n\n"
            "Notes:\n"
            "• RAT = VW / VFW (null when VFW is 0 or missing)."
        )


    def createInstance(self):
        return ExtractVWAlgorithm()

    def add_ratio_field(self, layer: QgsVectorLayer, feedback: QgsProcessingFeedback):
            dp = layer.dataProvider()

            # add field if it doesn't exist yet
            if layer.fields().indexFromName("RAT") == -1:
                dp.addAttributes([QgsField("RAT", QVariant.Double)])
                layer.updateFields()

            vw_idx = layer.fields().indexFromName("VW")
            vfw_idx = layer.fields().indexFromName("VFW")
            rat_idx = layer.fields().indexFromName("RAT")

            layer.startEditing()
            count = layer.featureCount()

            for i, f in enumerate(layer.getFeatures()):
                vw = f[vw_idx]
                vfw = f[vfw_idx]

                if vfw in (None, 0):
                    rat_val = None  # or -9999
                else:
                    rat_val = float(vw) / float(vfw)

                f[rat_idx] = rat_val
                layer.updateFeature(f)

                if i % 100 == 0 and count:
                    feedback.setProgress(int(100 * i / count))

            layer.commitChanges()

    def processAlgorithm(self, parameters, context: QgsProcessingContext, feedback: QgsProcessingFeedback):

        transects = self.parameterAsVectorLayer(parameters, self.TRANSECTS, context)
        center = self.parameterAsVectorLayer(parameters, self.CENTER_POINTS, context)
        valley_lines = self.parameterAsVectorLayer(parameters, self.VALLEY_LINES, context)
        stream_network = self.parameterAsVectorLayer(parameters, self.STREAM_NETWORK, context)

        centers_crs = center.sourceCrs()
        crs = centers_crs.authid()

        def create_output_layer(name):
            fields = QgsFields()
            fields.append(QgsField("side", QVariant.String))
            fields.append(QgsField("t_ID", QVariant.Int))     # Field needed downstream
            fields.append(QgsField("distance", QVariant.Double))
            
            layer = QgsVectorLayer(f"Point?crs={crs}", name, "memory")
            layer.dataProvider().addAttributes(fields)
            layer.updateFields()
    
            return layer, fields

        
        # Create memory layers
        left_vfw, left_fields = create_output_layer("Left_VFW")
        right_vfw, _ = create_output_layer("Right_VFW")
        left_vw, _ = create_output_layer("Left_VW")
        right_vw, _ = create_output_layer("Right_VW")

        # Run intersection logic
        left1, left2, right1, right2 = find_two_intersections_by_side(transects, valley_lines, stream_network)

        # Add features to layers
        add_points_in_batch(left1, left_vfw, "left")
        add_points_in_batch(right1, right_vfw, "right")
        add_points_in_batch(left2, left_vw, "left")
        add_points_in_batch(right2, right_vw, "right")

        # Save temporary layers to outputs
        left_vfw_id  = self.save_output_layer(left_vfw,  parameters, self.LEFT_VFW,  context)
        right_vfw_id = self.save_output_layer(right_vfw, parameters, self.RIGHT_VFW, context)
        left_vw_id   = self.save_output_layer(left_vw,   parameters, self.LEFT_VW,   context)
        right_vw_id  = self.save_output_layer(right_vw,  parameters, self.RIGHT_VW,  context)
        

        # Compute valley widths and get updated layer
        center_updated1 = compute_valley_width(center, left1, right1, out_field="VFW")
        center_updated2 = compute_valley_width(center_updated1, left2, right2, out_field="VW")

        if center_updated2.isValid():
            center_updated2.setCrs(centers_crs)

        # Ratio of VW:VFW calculation
        self.add_ratio_field(center_updated2, feedback)

        center_id    = self.save_output_layer(center_updated2, parameters, self.CENTER_OUT, context)

        left_vfw_layer = context.getMapLayer(left_vfw_id)
        if left_vfw_layer:
            symbol = left_vfw_layer.renderer().symbol()
            symbol.setColor(QColor(180,0,0))  # red
            symbol.setSize(3) # 3 mm
            left_vfw_layer.triggerRepaint()
            

        left_vw_layer = context.getMapLayer(left_vw_id)
        if left_vw_layer:
            symbol = left_vw_layer.renderer().symbol()
            symbol.setColor(QColor(120,0,0))  # red
            symbol.setSize(4) # 4 mm
            sl = symbol.symbolLayer(0)
            if isinstance(sl, QgsSimpleMarkerSymbolLayer):
                sl.setShape(QgsSimpleMarkerSymbolLayer.Triangle)
            left_vw_layer.triggerRepaint()
            feedback.pushInfo("Applied red symbology to left intersections.")

        right_vfw_layer = context.getMapLayer(right_vfw_id)
        if right_vfw_layer:
            symbol = right_vfw_layer.renderer().symbol()
            symbol.setColor(QColor(0,180,0))  # green
            symbol.setSize(3) # 3 mm
            right_vfw_layer.triggerRepaint()
            

        right_vw_layer = context.getMapLayer(right_vw_id)
        if right_vw_layer:
            symbol = right_vw_layer.renderer().symbol()
            symbol.setColor(QColor(0,120,0))  # green
            symbol.setSize(4) # 4 mm
            sl = symbol.symbolLayer(0)
            if isinstance(sl, QgsSimpleMarkerSymbolLayer):
                sl.setShape(QgsSimpleMarkerSymbolLayer.Triangle)
            right_vw_layer.triggerRepaint()
            feedback.pushInfo("Applied green symbology to right intersections.")

        center_layer = context.getMapLayer(center_id)
        if center_layer:
            symbol = center_layer.renderer().symbol()
            symbol.setColor(QColor(0,0,255))  # red
            symbol.setSize(3) # 3 mm
            center_layer.triggerRepaint()
            feedback.pushInfo("Applied blue symbology to segment centers.")
            
        return {
            self.LEFT_VFW: left_vfw_id,
            self.RIGHT_VFW: right_vfw_id,
            self.LEFT_VW: left_vw_id,
            self.RIGHT_VW: right_vw_id,
            self.CENTER_OUT: center_id
        }


    def save_output_layer(self, layer, parameters, param_name, context):
        fields = layer.fields()
        geometry_type = layer.wkbType()
        crs = layer.sourceCrs()

        sink, dest_id = self.parameterAsSink(
            parameters, param_name, context,
            fields, geometry_type, crs
        )

        if sink is not None:
            for f in layer.getFeatures():
                sink.addFeature(f, QgsFeatureSink.FastInsert)
        return dest_id
