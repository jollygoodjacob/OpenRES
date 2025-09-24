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
    QgsProcessingParameterVectorLayer,
    QgsProcessingParameterField,
    QgsProcessingParameterVectorDestination,
    QgsFeatureSink,
    QgsField,
    QgsWkbTypes,
    QgsSpatialIndex,
    QgsPointXY,
    QgsFeature,
    QgsVectorLayer,
    QgsProcessingContext,
    QgsProcessingFeedback,
    QgsRaster
)
from qgis.core import QgsProcessing
from PyQt5.QtCore import QVariant


class ExtractPointDataAlgorithm(QgsProcessingAlgorithm):
    POINTS = 'POINTS'
    RASTER1 = 'RASTER1'
    RASTER2 = 'RASTER2'
    POLYGONS = 'POLYGONS'
    POLY_FIELD = 'POLY_FIELD'
    OUTPUT = 'OUTPUT'

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterFeatureSource(self.POINTS, "Segment Centers Layer", [QgsProcessing.TypeVectorPoint]))
        self.addParameter(QgsProcessingParameterRasterLayer(self.RASTER1, "Elevation Raster Layer (for 'ELE')"))
        self.addParameter(QgsProcessingParameterRasterLayer(self.RASTER2, "Precipitation Raster Layer (for 'PRE')"))
        self.addParameter(QgsProcessingParameterVectorLayer(self.POLYGONS, "Geology Polygon Layer (for 'GEO')", [QgsProcessing.TypeVectorPolygon]))
        self.addParameter(QgsProcessingParameterField(self.POLY_FIELD, "Geology Attribute Field", parentLayerParameterName=self.POLYGONS))
        self.addParameter(QgsProcessingParameterVectorDestination(self.OUTPUT, "[2] Segment Centers"))

    def name(self):
        return "extract_point_attributes"

    def displayName(self):
        return "[2] Extract ELE, PRE, and GEO"

    def group(self):
        return "Feature Extraction"

    def groupId(self):
        return "feature_extraction"

    def createInstance(self):
        return ExtractPointDataAlgorithm()

    def processAlgorithm(self, parameters, context: QgsProcessingContext, feedback: QgsProcessingFeedback):

        points = self.parameterAsVectorLayer(parameters, self.POINTS, context)
        raster1 = self.parameterAsRasterLayer(parameters, self.RASTER1, context)
        raster2 = self.parameterAsRasterLayer(parameters, self.RASTER2, context)
        polygons = self.parameterAsVectorLayer(parameters, self.POLYGONS, context)
        poly_field = self.parameterAsString(parameters, self.POLY_FIELD, context)

        # Make an editable memory copy
        out_layer = QgsVectorLayer("Point?crs={}".format(points.sourceCrs().authid()), "temp_points", "memory")
        out_dp = out_layer.dataProvider()
        out_dp.addAttributes(points.fields())
        out_layer.updateFields()
        out_dp.addFeatures([f for f in points.getFeatures()])

        # Add new fields if needed
        for name, typ in [("ELE", QVariant.Double), ("PRE", QVariant.Double), ("GEO", QVariant.String)]:
            if out_layer.fields().indexFromName(name) == -1:
                out_dp.addAttributes([QgsField(name, typ)])
        out_layer.updateFields()

        # Sample raster 1 (ELE)
        self.extract_raster_value(out_layer, raster1, "ELE", feedback)
        self.extract_raster_value(out_layer, raster2, "PRE", feedback)
        self.extract_polygon_value(out_layer, polygons, poly_field, "GEO", feedback)

        # Output
        sink, dest_id = self.parameterAsSink(parameters, self.OUTPUT, context,
                                             out_layer.fields(), QgsWkbTypes.Point, out_layer.sourceCrs())
        for f in out_layer.getFeatures():
            sink.addFeature(f)

        return {self.OUTPUT: dest_id}

    def extract_raster_value(self, point_layer, raster_layer, field_name, feedback):
        point_layer.startEditing()
        for i, feature in enumerate(point_layer.getFeatures()):
            point = feature.geometry().asPoint() if not feature.geometry().isMultipart() else feature.geometry().asMultiPoint()[0]
            pt_xy = QgsPointXY(point.x(), point.y())
            ident = raster_layer.dataProvider().identify(pt_xy, QgsRaster.IdentifyFormatValue)
            value = ident.results().get(1, None) if ident.isValid() else None
            feature[field_name] = value if value is not None else -9999
            point_layer.updateFeature(feature)
            if i % 100 == 0:
                feedback.setProgress(int(100 * i / point_layer.featureCount()))
        point_layer.commitChanges()

    def extract_polygon_value(self, point_layer, polygon_layer, polygon_attribute, target_field, feedback):
        spatial_index = QgsSpatialIndex(polygon_layer.getFeatures())
        point_layer.startEditing()
        for i, feature in enumerate(point_layer.getFeatures()):
            geom = feature.geometry()
            point = geom.asPoint() if not geom.isMultipart() else geom.asMultiPoint()[0]
            candidates = spatial_index.intersects(geom.boundingBox())
            value = "No Data"
            for pid in candidates:
                poly = polygon_layer.getFeature(pid)
                if poly.geometry().contains(geom):
                    value = poly[polygon_attribute]
                    break
            feature[target_field] = value
            point_layer.updateFeature(feature)
            if i % 100 == 0:
                feedback.setProgress(int(100 * i / point_layer.featureCount()))
        point_layer.commitChanges()
