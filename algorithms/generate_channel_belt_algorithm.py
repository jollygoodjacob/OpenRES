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

from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingParameterVectorLayer,
    QgsProcessingParameterNumber,
    QgsProcessingParameterEnum,
    QgsProcessingParameterFeatureSink,
    QgsProcessingException,
    QgsFeature,
    QgsFields,
    QgsField,
    QgsGeometry,
    QgsWkbTypes,
    QgsFeatureSink,
)

from qgis.PyQt.QtCore import QMetaType

try:
    INT = QMetaType.Type.Int
    DOUBLE = QMetaType.Type.Double
    STRING = QMetaType.Type.QString
    BOOL = QMetaType.Type.Bool
    LONG_LONG = QMetaType.Type.LongLong
except AttributeError:
    from qgis.PyQt.QtCore import QVariant
    INT = QVariant.Int
    DOUBLE = QVariant.Double
    STRING = QVariant.String
    BOOL = QVariant.Bool
    LONG_LONG = QVariant.LongLong
    
from ..icon_utils import openres_icon

class GenerateChannelBeltAlgorithm(QgsProcessingAlgorithm):
    """
    Offset a stream network to the left (+) and right (-) and write all offsets
    (no dissolve) to a single line layer with side and t_ID attributes.
    """


    PARAM_INPUT = "INPUT"
    PARAM_OFFSET = "OFFSET"
    PARAM_SEGMENTS = "SEGMENTS"
    PARAM_JOINSTYLE = "JOINSTYLE"
    PARAM_MITERLIMIT = "MITERLIMIT"
    OUTPUT = "OUTPUT"

    def tr(self, string):
        return QCoreApplication.translate("Processing", string)

    def createInstance(self):
        return GenerateChannelBeltAlgorithm()

    def name(self):
        return "generate_channel_belt"

    def displayName(self):
        return self.tr("Generate Channel Belt")

    def group(self):
        return self.tr('Geomorphology')

    def groupId(self):
        return 'geomorphology'

    def icon(self):
        return openres_icon("openres_provider.png")

    def shortHelpString(self):
        return self.tr(
            "Offsets each input river segment to LEFT (+) and RIGHT (-) by the given distance "
            "and writes results into a single line layer. "
            "Copies t_ID from input when present; otherwise creates sequential t_ID. "
            "Adds fields: t_ID (int), side {'LEFT'|'RIGHT'}, offset (double).\n\n"
            "Notes:\n"
            "• Offsets use layer CRS units; use a projected CRS (e.g., meters).\n"
            "• LEFT/RIGHT are relative to the digitized direction of each line.\n"
            "• Use Round joins for smooth banks; Miter for sharp corners (tune miter limit)."
        )




    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.PARAM_INPUT,
                self.tr("River network"),
                [QgsProcessing.TypeVectorLine],
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.PARAM_OFFSET,
                self.tr("Offset distance (map units; meters if projected)"),
                type=QgsProcessingParameterNumber.Double,
                defaultValue=10.0,
                minValue=0.0,
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.PARAM_SEGMENTS,
                self.tr("Segments (curve smoothing)"),
                type=QgsProcessingParameterNumber.Integer,
                defaultValue=8,
                minValue=1,
            )
        )
        self.addParameter(
            QgsProcessingParameterEnum(
                self.PARAM_JOINSTYLE,
                self.tr("Join style"),
                options=["Round", "Miter", "Bevel"],
                defaultValue=0,
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.PARAM_MITERLIMIT,
                self.tr("Miter limit (used for Miter joins)"),
                type=QgsProcessingParameterNumber.Double,
                defaultValue=2.0,
                minValue=1.0,
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr("Channel Belt")
            )
        )


    def _join_style(self, idx: int):
        # Map UI enum -> QgsGeometry join style
        if idx == 1:
            return QgsGeometry.JoinStyleMiter
        if idx == 2:
            return QgsGeometry.JoinStyleBevel
        return QgsGeometry.JoinStyleRound

    def _ensure_multiline(self, g: QgsGeometry) -> QgsGeometry:
        """Force LineString -> MultiLineString for a consistent sink type."""
        if not g or g.isEmpty():
            return g
        flat = QgsWkbTypes.flatType(g.wkbType())
        if flat == QgsWkbTypes.LineString:
            return QgsGeometry.collectGeometry([g])
        return g


    def processAlgorithm(self, parameters, context, feedback):
        in_lyr = self.parameterAsVectorLayer(parameters, self.PARAM_INPUT, context)
        if in_lyr is None:
            raise QgsProcessingException(self.tr("Invalid input layer."))

        crs = in_lyr.crs()
        if crs.isGeographic():
            feedback.reportError(
                self.tr("Input CRS appears geographic (degrees). Offsets are in map units; "
                        "use a projected CRS (meters) for correct distances.")
            )

        offset = self.parameterAsDouble(parameters, self.PARAM_OFFSET, context)
        if offset <= 0:
            raise QgsProcessingException(self.tr("Offset distance must be > 0."))

        segments = self.parameterAsInt(parameters, self.PARAM_SEGMENTS, context)
        join_style = self._join_style(self.parameterAsEnum(parameters, self.PARAM_JOINSTYLE, context))
        miter_limit = self.parameterAsDouble(parameters, self.PARAM_MITERLIMIT, context)


        fields = QgsFields()
        fields.append(QgsField("t_ID", INT))
        fields.append(QgsField("side", STRING))
        fields.append(QgsField("offset", DOUBLE))

        (sink, dest_id) = self.parameterAsSink(
            parameters,
            self.OUTPUT,
            context,
            fields,
            QgsWkbTypes.MultiLineString,
            crs
        )
        if sink is None:
            raise QgsProcessingException(self.tr("Could not create output sink."))

        has_tid = "t_ID" in in_lyr.fields().names()
        fallback_tid = 1
        total = in_lyr.featureCount() or 1

        for i, f in enumerate(in_lyr.getFeatures()):
            if feedback.isCanceled():
                break

            g = f.geometry()
            if not g or g.isEmpty():
                continue

            # Determine t_ID
            if has_tid and f["t_ID"] not in (None, ""):
                try:
                    t_id_val = int(f["t_ID"])
                except Exception:
                    t_id_val = fallback_tid
                    fallback_tid += 1
            else:
                t_id_val = fallback_tid
                fallback_tid += 1

            # LEFT (+) offset
            try:
                g_left = g.offsetCurve(+offset, segments, join_style, miter_limit)
            except Exception as e:
                g_left = None
                feedback.reportError(self.tr(f"LEFT offset failed for feature {f.id()}: {e}"))

            # RIGHT (-) offset
            try:
                g_right = g.offsetCurve(-offset, segments, join_style, miter_limit)
            except Exception as e:
                g_right = None
                feedback.reportError(self.tr(f"RIGHT offset failed for feature {f.id()}: {e}"))

            # Write 
            if g_left and not g_left.isEmpty():
                of = QgsFeature(fields)
                of.setGeometry(self._ensure_multiline(g_left))
                of.setAttributes([t_id_val, "LEFT", float(offset)])
                sink.addFeature(of, QgsFeatureSink.FastInsert)

            if g_right and not g_right.isEmpty():
                of = QgsFeature(fields)
                of.setGeometry(self._ensure_multiline(g_right))
                of.setAttributes([t_id_val, "RIGHT", float(offset)])
                sink.addFeature(of, QgsFeatureSink.FastInsert)

            if (i + 1) % 1000 == 0:
                feedback.pushInfo(self.tr(f"Processed {i+1}/{total} features..."))

            feedback.setProgress(int(100 * (i + 1) / total))

        return {self.OUTPUT: dest_id}
