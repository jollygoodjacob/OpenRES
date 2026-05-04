from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterVectorDestination,
    QgsProcessingParameterNumber,
    QgsProcessingException,
    QgsVectorLayer,
    QgsFeature,
    QgsFeatureRequest,
    QgsGeometry
)
import processing
from ..icon_utils import openres_icon

class CreateValleyBoundary(QgsProcessingAlgorithm):
    VALLEY = "VALLEY"
    MICROSHEDS = "MICROSHEDS"
    ITERATIONS = "ITERATIONS"
    OFFSET = "OFFSET"
    MAX_ANGLE = "MAX_ANGLE"
    OUTPUT = "OUTPUT"

    def tr(self, string):
        return QCoreApplication.translate("Processing", string)

    def createInstance(self):
        return CreateValleyBoundary()

    def name(self):
        return "createvalleyboundary"

    def displayName(self):
        return self.tr("Create Valley Boundary")

    def group(self):
        return self.tr("Geomorphology")

    def groupId(self):
        return "geomorphology"

    def icon(self):
        return openres_icon("openres_provider.png")

    def shortHelpString(self):
        return self.tr(
            "Subtract valley floor polygons from microsheds polygons that intersect the "
            "valley floor using an optimized per-feature difference workflow, then convert to lines, "
            "lightly smooth, and dissolve the final valley boundary. The created valley boundary layer "
            "should delineate the valley floor boundary and the confining valley margins."
        )

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.MICROSHEDS,
                self.tr("Microsheds polygons"),
                [QgsProcessing.TypeVectorPolygon]
            )
        )

        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.VALLEY,
                self.tr("Valley floor polygons"),
                [QgsProcessing.TypeVectorPolygon]
            )
        )

        self.addParameter(
            QgsProcessingParameterNumber(
                self.ITERATIONS,
                self.tr("Smoothing iterations"),
                type=QgsProcessingParameterNumber.Integer,
                defaultValue=1,
                minValue=1
            )
        )

        self.addParameter(
            QgsProcessingParameterNumber(
                self.OFFSET,
                self.tr("Smoothing offset"),
                type=QgsProcessingParameterNumber.Double,
                defaultValue=0.25,
                minValue=0.0
            )
        )

        self.addParameter(
            QgsProcessingParameterNumber(
                self.MAX_ANGLE,
                self.tr("Maximum node angle"),
                type=QgsProcessingParameterNumber.Double,
                defaultValue=180.0,
                minValue=0.0,
                maxValue=180.0
            )
        )

        self.addParameter(
            QgsProcessingParameterVectorDestination(
                self.OUTPUT,
                self.tr("Valley boundary lines"),
                type=QgsProcessing.TypeVectorLine
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        iterations = self.parameterAsInt(parameters, self.ITERATIONS, context)
        offset = self.parameterAsDouble(parameters, self.OFFSET, context)
        max_angle = self.parameterAsDouble(parameters, self.MAX_ANGLE, context)
        output = self.parameterAsOutputLayer(parameters, self.OUTPUT, context)

        feedback.pushInfo("Fixing microsheds geometries...")
        microsheds_fixed = processing.run(
            "native:fixgeometries",
            {"INPUT": parameters[self.MICROSHEDS], "OUTPUT": "memory:"},
            context=context,
            feedback=feedback
        )["OUTPUT"]

        feedback.pushInfo("Fixing valley floor geometries...")
        valley_fixed = processing.run(
            "native:fixgeometries",
            {"INPUT": parameters[self.VALLEY], "OUTPUT": "memory:"},
            context=context,
            feedback=feedback
        )["OUTPUT"]

        valley_fixed.dataProvider().createSpatialIndex()

        crs_authid = microsheds_fixed.crs().authid()
        diff_layer = QgsVectorLayer(f"Polygon?crs={crs_authid}", "diff_result", "memory")
        diff_provider = diff_layer.dataProvider()
        diff_provider.addAttributes(microsheds_fixed.fields())
        diff_layer.updateFields()

        microshed_features = list(microsheds_fixed.getFeatures())
        total = len(microshed_features)
        out_features = []

        for i, microshed_feat in enumerate(microshed_features):
            if feedback.isCanceled():
                break

            microshed_geom = microshed_feat.geometry()
            if microshed_geom is None or microshed_geom.isEmpty():
                continue

            diff_geom = QgsGeometry(microshed_geom)
            intersects_valley = False

            request = QgsFeatureRequest().setFilterRect(microshed_geom.boundingBox())

            for valley_feat in valley_fixed.getFeatures(request):
                valley_geom = valley_feat.geometry()
                if valley_geom is None or valley_geom.isEmpty():
                    continue

                if microshed_geom.intersects(valley_geom):
                    intersects_valley = True
                    diff_geom = diff_geom.difference(valley_geom)

                    if diff_geom.isEmpty():
                        break

            if intersects_valley and not diff_geom.isEmpty():
                new_feat = QgsFeature(diff_layer.fields())
                new_feat.setGeometry(diff_geom)
                new_feat.setAttributes(microshed_feat.attributes())
                out_features.append(new_feat)

            feedback.setProgress(int((i + 1) / total * 100))

        diff_provider.addFeatures(out_features)
        diff_layer.updateExtents()

        line_result = processing.run(
            "native:polygonstolines",
            {"INPUT": diff_layer, "OUTPUT": "memory:"},
            context=context,
            feedback=feedback
        )["OUTPUT"]

        smooth_result = processing.run(
            "native:smoothgeometry",
            {
                "INPUT": line_result,
                "ITERATIONS": iterations,
                "OFFSET": offset,
                "MAX_ANGLE": max_angle,
                "OUTPUT": "memory:"
            },
            context=context,
            feedback=feedback
        )["OUTPUT"]

        dissolve_result = processing.run(
            "native:dissolve",
            {
                "INPUT": smooth_result,
                "FIELD": [],
                "SEPARATE_DISJOINT": False,
                "OUTPUT": output
            },
            context=context,
            feedback=feedback
        )

        return {self.OUTPUT: dissolve_result["OUTPUT"]}
