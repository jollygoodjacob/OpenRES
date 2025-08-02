###############################################################################
#                                                                             #
#                     OpenRES: Open Riverine Ecosytem Synthesis               #
#                                                                             #
#      A QGIS plugin for automated extraction of hydrogeomorphic features to  #
#       support functional process zone classification of river networks      #
#                                                                             #
#                         Developed by Jacob Nesslage                         #
#                             © 2025 Jacob Nesslage                           #
#                                                                             #
#                             MIT License Notice                              #
#                                                                             #
# Permission is hereby granted, free of charge, to any person obtaining a     #
# copy of this software and associated documentation files (the "Software"),  #
# to deal in the Software without restriction, including without limitation   #
# the rights to use, copy, modify, merge, publish, distribute, sublicense,    #
# and/or sell copies of the Software, and to permit persons to whom the       #
# Software is furnished to do so, subject to the following conditions:        #
#                                                                             #
# The above copyright notice and this permission notice shall be included in  #
# all copies or substantial portions of the Software.                         #
#                                                                             #
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR  #
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,    #
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL     #
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER  #
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING     #
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER         #
# DEALINGS IN THE SOFTWARE.                                                   #
#                                                                             #
###############################################################################

from qgis.core import (
    QgsProcessingAlgorithm,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterVectorLayer,
    QgsProcessingParameterVectorDestination,
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

from ..extract_valley_width import (
    find_two_intersections_by_side,
    add_points_in_batch,
    compute_valley_width
)


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

        self.addParameter(QgsProcessingParameterVectorDestination(self.LEFT_VFW, "Left VFW Reference"))
        self.addParameter(QgsProcessingParameterVectorDestination(self.RIGHT_VFW, "Right VFW Reference"))
        self.addParameter(QgsProcessingParameterVectorDestination(self.LEFT_VW, "Left VW Reference"))
        self.addParameter(QgsProcessingParameterVectorDestination(self.RIGHT_VW, "Right VW Reference"))
        self.addParameter(QgsProcessingParameterVectorDestination(self.CENTER_OUT, "[3] Segment Centers"))

    def name(self):
        return "extract_valley_width"

    def displayName(self):
        return "[3] Extract VW and VFW"

    def group(self):
        return "Feature Extraction"

    def groupId(self):
        return "feature_extraction"

    def createInstance(self):
        return ExtractVWAlgorithm()

    def processAlgorithm(self, parameters, context: QgsProcessingContext, feedback: QgsProcessingFeedback):

        transects = self.parameterAsVectorLayer(parameters, self.TRANSECTS, context)
        center = self.parameterAsVectorLayer(parameters, self.CENTER_POINTS, context)
        valley_lines = self.parameterAsVectorLayer(parameters, self.VALLEY_LINES, context)
        stream_network = self.parameterAsVectorLayer(parameters, self.STREAM_NETWORK, context)

        crs = transects.sourceCrs().authid()

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
        self.save_output_layer(left_vfw, parameters, self.LEFT_VFW, context)
        self.save_output_layer(right_vfw, parameters, self.RIGHT_VFW, context)
        self.save_output_layer(left_vw, parameters, self.LEFT_VW, context)
        self.save_output_layer(right_vw, parameters, self.RIGHT_VW, context)
        

        # Compute valley widths and get updated layer
        center_updated1 = compute_valley_width(center, left1, right1, out_field="VFW")
        center_updated2 = compute_valley_width(center_updated1, left2, right2, out_field="VW")

        self.save_output_layer(center_updated2, parameters, self.CENTER_OUT, context)


        return {
            self.LEFT_VFW: parameters[self.LEFT_VFW],
            self.RIGHT_VFW: parameters[self.RIGHT_VFW],
            self.LEFT_VW: parameters[self.LEFT_VW],
            self.RIGHT_VW: parameters[self.RIGHT_VW],
            self.CENTER_OUT: parameters[self.CENTER_OUT]
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
