from qgis.core import (
    QgsProcessingAlgorithm,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterRasterLayer,
    QgsProcessingParameterVectorDestination,
    QgsFeatureSink,
    QgsField,
    QgsWkbTypes,
    QgsFeature,
    QgsVectorLayer,
    QgsProcessingContext,
    QgsProcessingFeedback,
    QgsFields,
)
from qgis.core import QgsProcessing
from PyQt5.QtCore import QVariant

from ..extract_side_slopes import calculate_side_slopes_from_pairs


class ExtractSideSlopesAlgorithm(QgsProcessingAlgorithm):
    CENTER = 'CENTER'
    LEFT_VW = 'LEFT_VW'
    LEFT_VFW = 'LEFT_VFW'
    RIGHT_VW = 'RIGHT_VW'
    RIGHT_VFW = 'RIGHT_VFW'
    RASTER = 'RASTER'
    OUTPUT = 'OUTPUT'

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterFeatureSource(self.CENTER, "Segment Centers Layer", [QgsProcessing.TypeVectorPoint]))
        self.addParameter(QgsProcessingParameterFeatureSource(self.LEFT_VW, "Left Valley Width Reference Layer", [QgsProcessing.TypeVectorPoint]))
        self.addParameter(QgsProcessingParameterFeatureSource(self.LEFT_VFW, "Left Valley Floor Width Reference Layer", [QgsProcessing.TypeVectorPoint]))
        self.addParameter(QgsProcessingParameterFeatureSource(self.RIGHT_VW, "Right Valley Width Reference Layer", [QgsProcessing.TypeVectorPoint]))
        self.addParameter(QgsProcessingParameterFeatureSource(self.RIGHT_VFW, "Right Valley Floor Width Reference Layer", [QgsProcessing.TypeVectorPoint]))
        self.addParameter(QgsProcessingParameterRasterLayer(self.RASTER, "Elevation Raster Layer"))
        self.addParameter(QgsProcessingParameterVectorDestination(self.OUTPUT, "[4] Segment Centers"))

    def name(self):
        return "extract_side_slopes"

    def displayName(self):
        return "[4] Extract LVS and RVS"

    def group(self):
        return "Feature Extraction"

    def groupId(self):
        return "feature_extraction"

    def createInstance(self):
        return ExtractSideSlopesAlgorithm()

    def processAlgorithm(self, parameters, context: QgsProcessingContext, feedback: QgsProcessingFeedback):

        center = self.parameterAsVectorLayer(parameters, self.CENTER, context)
        left_vw = self.parameterAsVectorLayer(parameters, self.LEFT_VW, context)
        left_vfw = self.parameterAsVectorLayer(parameters, self.LEFT_VFW, context)
        right_vw = self.parameterAsVectorLayer(parameters, self.RIGHT_VW, context)
        right_vfw = self.parameterAsVectorLayer(parameters, self.RIGHT_VFW, context)
        raster = self.parameterAsRasterLayer(parameters, self.RASTER, context)

        # Make an in-memory copy to edit safely
        temp_center = QgsVectorLayer("Point?crs={}".format(center.crs().authid()), "temp_center", "memory")
        temp_center_data = temp_center.dataProvider()
        temp_center_data.addAttributes(center.fields())
        temp_center.updateFields()

        features = [f for f in center.getFeatures()]
        temp_center_data.addFeatures(features)

        # Run slope calculation and write LSS/RSS
        calculate_side_slopes_from_pairs(temp_center, left_vw, left_vfw, right_vw, right_vfw, raster)

        # Output to user-defined destination
        sink, dest_id = self.parameterAsSink(parameters, self.OUTPUT, context,
                                             temp_center.fields(), QgsWkbTypes.Point, temp_center.crs())
        for f in temp_center.getFeatures():
            sink.addFeature(f)

        return {self.OUTPUT: dest_id}
