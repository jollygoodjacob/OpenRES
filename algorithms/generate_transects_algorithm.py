from qgis.core import (
    QgsProcessingAlgorithm,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterFeatureSink,
    QgsProcessingParameterNumber,
    QgsFeature,
    QgsGeometry,
    QgsPointXY,
    QgsWkbTypes,
    QgsSpatialIndex,
    QgsField,
    QgsFields,
    QgsFeatureSink,
    QgsProcessingContext,
    QgsProcessingFeedback,
    QgsProcessingOutputVectorLayer,
    QgsVectorLayer,
    QgsFeatureRequest
)
from qgis.core import QgsProcessing
from PyQt5.QtCore import QVariant
import math


class GenerateTransectsAlgorithm(QgsProcessingAlgorithm):
    RIVER_LAYER = 'RIVER_LAYER'
    LINE_LAYER = 'LINE_LAYER'
    EXTENSION_INCREMENT = 'EXTENSION_INCREMENT'
    MAX_LENGTH = 'MAX_LENGTH'
    TRANSECTS = 'TRANSECTS'
    CENTER_POINTS = 'CENTER_POINTS'

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterFeatureSource(self.RIVER_LAYER, "Input River Layer"))
        self.addParameter(QgsProcessingParameterFeatureSource(self.LINE_LAYER, "Intersecting Lines Layer"))
        self.addParameter(QgsProcessingParameterNumber(self.EXTENSION_INCREMENT, "Extension Increment (m)", defaultValue=250))
        self.addParameter(QgsProcessingParameterNumber(self.MAX_LENGTH, "Max Length (m)", defaultValue=50000))
        self.addParameter(QgsProcessingParameterFeatureSink(self.TRANSECTS, "Transects Output"))
        self.addParameter(QgsProcessingParameterFeatureSink(self.CENTER_POINTS, "Center Points Output"))

    def name(self):
        return "generate_transects"

    def displayName(self):
        return "[1] Generate Transects"

    def group(self):
        return "Feature Extraction"

    def groupId(self):
        return "feature_extraction"

    def createInstance(self):
        return GenerateTransectsAlgorithm()

    def processAlgorithm(self, parameters, context: QgsProcessingContext, feedback: QgsProcessingFeedback):
        river_layer = self.parameterAsSource(parameters, self.RIVER_LAYER, context)
        lines_layer = self.parameterAsSource(parameters, self.LINE_LAYER, context)
        extension_increment = self.parameterAsInt(parameters, self.EXTENSION_INCREMENT, context)
        max_length = self.parameterAsInt(parameters, self.MAX_LENGTH, context)

        river_fields = QgsFields()
        river_fields.append(QgsField("t_ID", QVariant.Int))
        river_fields.append(QgsField("left_n", QVariant.Int))
        river_fields.append(QgsField("right_n", QVariant.Int))

        center_fields = QgsFields()
        center_fields.append(QgsField("t_ID", QVariant.Int))

        (transect_sink, transect_dest_id) = self.parameterAsSink(parameters, self.TRANSECTS, context, river_fields, QgsWkbTypes.MultiLineString, river_layer.sourceCrs())
        (center_sink, center_dest_id) = self.parameterAsSink(parameters, self.CENTER_POINTS, context, center_fields, QgsWkbTypes.Point, river_layer.sourceCrs())

        lines_index = QgsSpatialIndex(lines_layer.getFeatures())

        for i, river_feature in enumerate(river_layer.getFeatures()):
            if feedback.isCanceled():
                break

            feedback.setProgress(int(i / river_layer.featureCount() * 100))

            river_geom = river_feature.geometry()
            if river_geom is None or river_geom.isNull():
                continue

            midpoint = river_geom.interpolate(river_geom.length() / 2).asPoint()
            center_distance = river_geom.length() / 2
            delta = min(500, center_distance - 1)
            pt_before = river_geom.interpolate(center_distance - delta).asPoint()
            pt_after = river_geom.interpolate(center_distance + delta).asPoint()
            perpendicular_angle = self.calculate_perpendicular_angle(pt_before, pt_after)

            # LEFT
            left_geom, left_intersections = self.extend_until_intersections(midpoint, perpendicular_angle, lines_layer, lines_index, -1, extension_increment, max_length)
            # RIGHT
            right_geom, right_intersections = self.extend_until_intersections(midpoint, perpendicular_angle, lines_layer, lines_index, 1, extension_increment, max_length)

            if len(left_intersections) >= 2 and len(right_intersections) >= 2:
                full_transect = QgsGeometry.fromPolylineXY(left_geom.asPolyline() + right_geom.asPolyline()[1:])
                t_feat = QgsFeature()
                t_feat.setGeometry(full_transect)
                t_feat.setAttributes([river_feature["t_ID"], len(left_intersections), len(right_intersections)])
                transect_sink.addFeature(t_feat, QgsFeatureSink.FastInsert)

                c_feat = QgsFeature()
                c_feat.setGeometry(QgsGeometry.fromPointXY(midpoint))
                c_feat.setAttributes([river_feature["t_ID"]])
                center_sink.addFeature(c_feat, QgsFeatureSink.FastInsert)

        return {
            self.TRANSECTS: transect_dest_id,
            self.CENTER_POINTS: center_dest_id
        }

    def calculate_perpendicular_angle(self, line_start, line_end):
        dx = line_end.x() - line_start.x()
        dy = line_end.y() - line_start.y()
        angle = math.atan2(dy, dx) * 180 / math.pi
        if angle < 0:
            angle += 360
        return angle + 90

    def find_intersections(self, transect_line, spatial_index, lines_layer, tolerance=1e-8):
        candidate_ids = spatial_index.intersects(transect_line.boundingBox())
        intersections = []

        for fid in candidate_ids:
            line_feature = next(lines_layer.getFeatures(QgsFeatureRequest(fid)))
            line_geom = line_feature.geometry()

            if transect_line.intersects(line_geom):
                result = transect_line.intersection(line_geom)

                if not result.isEmpty():
                    if result.isMultipart():
                        points = result.asMultiPoint()
                    elif result.type() == QgsWkbTypes.PointGeometry:
                        points = [result.asPoint()]
                    elif result.type() == QgsWkbTypes.MultiPointGeometry:
                        points = result.asMultiPoint()
                    elif result.type() == QgsWkbTypes.GeometryCollection:
                        points = []
                        for i in range(result.numGeometries()):
                            part = result.geometryN(i)
                            if part.type() == QgsWkbTypes.PointGeometry:
                                points.append(part.asPoint())
                    else:
                        continue

                    for pt in points:
                        if all(pt.distance(existing) > tolerance for existing in intersections):
                            intersections.append(pt)

        return intersections

    def extend_until_intersections(self, midpoint, angle, lines_layer, spatial_index, direction, increment, max_length):
        length = 0
        intersections = []
        geom = None

        while len(intersections) < 2 and length < max_length:
            length += increment
            dx = math.cos(math.radians(angle)) * length
            dy = math.sin(math.radians(angle)) * length
            endpoint = QgsPointXY(midpoint.x() + direction * dx, midpoint.y() + direction * dy)
            if direction == -1:
                transect = QgsGeometry.fromPolylineXY([endpoint, midpoint])
            else:
                transect = QgsGeometry.fromPolylineXY([midpoint, endpoint])
            new_pts = self.find_intersections(transect, spatial_index, lines_layer)
            intersections.extend([i for i in new_pts if i not in intersections])
            geom = transect

        return geom, intersections
