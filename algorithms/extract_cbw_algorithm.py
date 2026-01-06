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
    QgsFields
)
from qgis.core import QgsProcessing
from PyQt5.QtCore import QVariant
from qgis.PyQt.QtGui import QColor
from ..extract_valley_width import (
    find_one_intersection_by_side,
    add_points_in_batch,
    compute_valley_width
)


class ExtractCBWAlgorithm(QgsProcessingAlgorithm):
    TRANSECTS = 'TRANSECTS'
    CENTER_POINTS = 'CENTER_POINTS'
    CHANNEL_BELT = 'CHANNEL_BELT'
    STREAM_NETWORK = 'STREAM_NETWORK'
    LEFT_CB = 'LEFT_CB'
    RIGHT_CB = 'RIGHT_CB'
    CENTER_OUT = 'CENTER_OUT'

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterFeatureSource(self.TRANSECTS, "Transects Layer", [QgsProcessing.TypeVectorLine]))
        self.addParameter(QgsProcessingParameterFeatureSource(self.CENTER_POINTS, "Segment Centers Layer", [QgsProcessing.TypeVectorPoint]))
        self.addParameter(QgsProcessingParameterFeatureSource(self.CHANNEL_BELT, "Channel Belt Layer", [QgsProcessing.TypeVectorLine]))
        self.addParameter(QgsProcessingParameterFeatureSource(self.STREAM_NETWORK, "River Network Layer", [QgsProcessing.TypeVectorLine]))


        self.addParameter(QgsProcessingParameterFeatureSink(self.LEFT_CB, "Left CB Reference"))
        self.addParameter(QgsProcessingParameterFeatureSink(self.RIGHT_CB, "Right CB Reference"))
        self.addParameter(QgsProcessingParameterFeatureSink(self.CENTER_OUT, "[6] Segment Centers"))

    def name(self):
        return "extract_cbw"

    def displayName(self):
        return "[6] Extract CBW"

    def group(self):
        return "Feature Extraction"

    def groupId(self):
        return "feature_extraction"

    def shortHelpString(self):
        return (
            "Computes channel belt width (CBW) for each segment center by intersecting "
            "transects with the channel belt boundaries on the left and right sides.\n\n"
            "Inputs:\n"
            "• Transects Layer (lines)\n"
            "• Segment Centers Layer (points; must include t_ID)\n"
            "• Channel Belt Layer (lines)\n"
            "• River Network Layer (lines)\n\n"
            "Outputs:\n"
            "• Left CB Reference (points)\n"
            "• Right CB Reference (points)\n"
            "• [6] Segment Centers with added CBW attribute\n\n"
            "Notes:\n"
            "• CBW is calculated from the distance between left and right channel belt intersections "
            "along each transect."
        )


    def createInstance(self):
        return ExtractCBWAlgorithm()

    def processAlgorithm(self, parameters, context: QgsProcessingContext, feedback: QgsProcessingFeedback):

        transects = self.parameterAsVectorLayer(parameters, self.TRANSECTS, context)
        center = self.parameterAsVectorLayer(parameters, self.CENTER_POINTS, context)
        channel_belt = self.parameterAsVectorLayer(parameters, self.CHANNEL_BELT, context)
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
        left_cb, left_fields = create_output_layer("Left_CB")
        right_cb, _ = create_output_layer("Right_CB")


        # Run intersection logic
        left1, right1= find_one_intersection_by_side(transects, channel_belt, stream_network)

        # Add features to layers
        add_points_in_batch(left1, left_cb, "left")
        add_points_in_batch(right1, right_cb, "right")


        # Save temporary layers to outputs
        left_cb_id = self.save_output_layer(left_cb, parameters, self.LEFT_CB, context)
        right_cb_id = self.save_output_layer(right_cb, parameters, self.RIGHT_CB, context)

        

        # Compute valley widths and get updated layer
        center_updated = compute_valley_width(center, left1, right1, out_field="CBW")


        if center_updated.isValid():
            center_updated.setCrs(centers_crs)

        center_id = self.save_output_layer(center_updated, parameters, self.CENTER_OUT, context)

        left_cb_layer = context.getMapLayer(left_cb_id)
        if left_cb_layer:
            symbol = left_cb_layer.renderer().symbol()
            symbol.setColor(QColor(220,0,0))  # red
            symbol.setSize(3) # 3 mm
            left_cb_layer.triggerRepaint()

        right_cb_layer = context.getMapLayer(right_cb_id)
        if right_cb_layer:
            symbol = right_cb_layer.renderer().symbol()
            symbol.setColor(QColor(0,220,0))  # green
            symbol.setSize(3) # 3 mm
            right_cb_layer.triggerRepaint()

        center_layer = context.getMapLayer(center_id)
        if center_layer:
            symbol = center_layer.renderer().symbol()
            symbol.setColor(QColor(0,0,255))  # blue
            symbol.setSize(3) # 3 mm
            center_layer.triggerRepaint()
            feedback.pushInfo("Applied blue symbology to segment centers.")

        return {
            self.LEFT_CB: left_cb_id ,
            self.RIGHT_CB: right_cb_id,
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
