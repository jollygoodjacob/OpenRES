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

from qgis.PyQt.QtCore import QCoreApplication, QVariant
from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterVectorLayer,
    QgsProcessingParameterVectorDestination,
    QgsProcessingContext,
    QgsProcessingFeedback,
    QgsProcessingException,
    QgsFeatureSink,
    QgsFields, QgsField, QgsFeature,
    QgsGeometry, QgsWkbTypes,
)
import math
from collections import defaultdict


class ExtractCBSAlgorithm(QgsProcessingAlgorithm):
    """
    Compute Left (LCS), Right (RCS), and Mean (MCS) channel-belt sinuosity per t_ID.
    For each side (LEFT/RIGHT):
      sinuosity = geometry.length() / straight-line distance between its endpoints.
    Assumes each side is a continuous line per t_ID (if multiple, uses longest).
    """

    CENTER_POINTS = "CENTER_POINTS"
    CHANNEL_BELT = "CHANNEL_BELT"
    OUTPUT = "OUTPUT"

    def tr(self, s):
        return QCoreApplication.translate("Processing", s)

    def createInstance(self):
        return ExtractCBSAlgorithm()

    def name(self):
        return "extract_channel_belt_sinuosity"

    def displayName(self):
        return "[7] Extract LCS, RCS, and CBS"

    def group(self):
        return "Feature Extraction"

    def groupId(self):
        return "feature_extraction"

    # ---------------- Parameters ----------------
    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.CENTER_POINTS,
                self.tr("Segment Centers Layer"),
                [QgsProcessing.TypeVectorPoint],
            )
        )
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.CHANNEL_BELT,
                self.tr("Channel Belt Layer"),
                [QgsProcessing.TypeVectorLine],
            )
        )
        self.addParameter(
            QgsProcessingParameterVectorDestination(
                self.OUTPUT,
                self.tr("[7] Segment Centers"),
            )
        )

    # ---------------- Helpers ----------------
    def _require_tid(self, layer, lname):
        if "t_ID" not in layer.fields().names():
            raise QgsProcessingException(self.tr(f"{lname} must include 't_ID'."))

    def _require_side(self, layer):
        if "side" not in layer.fields().names():
            raise QgsProcessingException(self.tr("CHANNEL_BELT must include 'side' with values LEFT/RIGHT."))

    def _endpoints(self, g: QgsGeometry):
        """Return start and end points from a (multi)line geometry."""
        if not g or g.isEmpty():
            return None, None
        flat = QgsWkbTypes.flatType(g.wkbType())
        try:
            if flat == QgsWkbTypes.LineString:
                pl = g.asPolyline()
                if pl and len(pl) >= 2:
                    return pl[0], pl[-1]
            elif flat == QgsWkbTypes.MultiLineString:
                m = g.asMultiPolyline()
                if m:
                    # choose the longest subline
                    longest = max(m, key=lambda seg: QgsGeometry.fromPolylineXY(seg).length())
                    if longest and len(longest) >= 2:
                        return longest[0], longest[-1]
        except Exception:
            return None, None
        return None, None

    def _sinuosity_from_geom(self, g: QgsGeometry):
        """length / chord for a single side geometry."""
        if not g or g.isEmpty():
            return None
        sp, ep = self._endpoints(g)
        if not sp or not ep:
            return None
        chord = math.hypot(ep.x() - sp.x(), ep.y() - sp.y())
        if chord <= 0:
            return None
        L = g.length()  # planar length in CRS units
        if L <= 0:
            return 1.0
        return L / chord

    # ---------------- Core ----------------
    def processAlgorithm(self, params, context: QgsProcessingContext, feedback: QgsProcessingFeedback):
        centers = self.parameterAsVectorLayer(params, self.CENTER_POINTS, context)
        belt = self.parameterAsVectorLayer(params, self.CHANNEL_BELT, context)
        if centers is None or belt is None:
            raise QgsProcessingException(self.tr("Invalid input layer(s)."))

        # Field checks
        self._require_tid(centers, "CENTER_POINTS")
        self._require_tid(belt, "CHANNEL_BELT")
        self._require_side(belt)

        # CRS advisory
        for lyr, nm in ((centers, "CENTER_POINTS"), (belt, "CHANNEL_BELT")):
            if lyr.crs().isGeographic():
                feedback.reportError(self.tr(f"{nm} CRS appears geographic (degrees). Use a projected CRS for distances."))

        # Gather belt features per (t_ID, side); if multiple, keep the longest feature for that side
        by_tid_side = defaultdict(lambda: {"LEFT": None, "RIGHT": None})
        for f in belt.getFeatures():
            try:
                tid = int(f["t_ID"])
            except Exception:
                continue
            side = (str(f["side"]).strip().upper() if f["side"] is not None else "")
            if side not in ("LEFT", "RIGHT"):
                continue
            g = f.geometry()
            if not g or g.isEmpty():
                continue
            current = by_tid_side[tid][side]
            if current is None or g.length() > current.length():
                by_tid_side[tid][side] = g

        # Prepare output schema: centers + LCS/RCS/MCS
        out_fields = QgsFields(centers.fields())
        if out_fields.indexFromName("LCS") == -1:
            out_fields.append(QgsField("LCS", QVariant.Double))
        if out_fields.indexFromName("RCS") == -1:
            out_fields.append(QgsField("RCS", QVariant.Double))
        if out_fields.indexFromName("CBS") == -1:
            out_fields.append(QgsField("CBS", QVariant.Double))

        sink, dest_id = self.parameterAsSink(
            params, self.OUTPUT, context,
            out_fields, centers.wkbType(), centers.sourceCrs()
        )
        if sink is None:
            raise QgsProcessingException(self.tr("Could not create output sink."))

        total = centers.featureCount() or 1
        for i, c in enumerate(centers.getFeatures()):
            if feedback.isCanceled():
                break

            of = QgsFeature(out_fields)
            of.setGeometry(c.geometry())
            attrs = list(c.attributes())
            if len(attrs) < out_fields.count():
                attrs += [None] * (out_fields.count() - len(attrs))
            of.setAttributes(attrs)

            lcs = rcs = mcs = None
            try:
                tid = int(c["t_ID"])
            except Exception:
                sink.addFeature(of, QgsFeatureSink.FastInsert)
                continue

            left_g = by_tid_side.get(tid, {}).get("LEFT")
            right_g = by_tid_side.get(tid, {}).get("RIGHT")

            if left_g:
                lcs = self._sinuosity_from_geom(left_g)
            if right_g:
                rcs = self._sinuosity_from_geom(right_g)
            if (lcs is not None) and (rcs is not None):
                mcs = 0.5 * (lcs + rcs)

            of.setAttribute("LCS", lcs)
            of.setAttribute("RCS", rcs)
            of.setAttribute("CBS", mcs)

            sink.addFeature(of, QgsFeatureSink.FastInsert)

            if (i + 1) % 500 == 0:
                feedback.pushInfo(self.tr(f"Processed {i+1}/{total} centers..."))
            feedback.setProgress(int(100 * (i + 1) / total))

        return {self.OUTPUT: dest_id}
