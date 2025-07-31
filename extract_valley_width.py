# --- QGIS Core Imports ---
from qgis.core import (
    QgsVectorLayer,         # Layer object for vectors (lines, points, polygons)
    QgsFeature,             # A single vector feature (geometry + attributes)
    QgsGeometry,            # Provides geometry operations (e.g. intersection)
    QgsPointXY,             # Lightweight 2D point
    QgsField,               # Represents an attribute field
    QgsProject,             # Interface to the current QGIS project
    QgsSpatialIndex,        # Optimized spatial lookup for vector features
    QgsWkbTypes             # Enum for identifying geometry types (Point, Line, etc.)
)
from PyQt5.QtCore import QVariant  # Used for defining attribute types

# --- Determine which side of the transect a point lies on ---
def determine_side(start_point, direction_vector, intersect_point):
    """
    Uses the 2D cross product to determine if a point lies to the left or right
    of a vector.

    Parameters:
        start_point (QgsPointXY): Origin point of the reference vector.
        direction_vector (QgsPointXY): Direction of the transect (or stream flow).
        intersect_point (QgsPointXY): Candidate point to classify.

    Returns:
        str: "left" or "right"
    """
    # Create vector from start to intersection
    intersect_vector = QgsPointXY(
        intersect_point.x() - start_point.x(),
        intersect_point.y() - start_point.y()
    )

    # 2D cross product to determine relative side
    cross_product = (
        direction_vector.x() * intersect_vector.y() -
        direction_vector.y() * intersect_vector.x()
    )

    return "left" if cross_product > 0 else "right"

# --- Add a batch of point features to a memory layer ---
def add_points_in_batch(points, layer, side):
    """
    Adds a batch of QgsPointXY features to a given memory layer.

    Parameters:
        points (list): List of tuples (QgsPointXY, t_ID, distance)
        layer (QgsVectorLayer): Target memory layer
        side (str): "left" or "right" – assigned as an attribute
    """
    features = []
    for point, transect_id, distance in points:
        new_feature = QgsFeature()
        new_feature.setGeometry(QgsGeometry.fromPointXY(point))
        new_feature.setAttributes([side, transect_id, distance])
        features.append(new_feature)

    layer.dataProvider().addFeatures(features)

# --- Core intersection logic for identifying left/right candidates ---
def find_two_intersections_by_side(transect_layer, other_layer, split_layer, tolerance=1e-8, debug=False):
    """
    For each transect, find the two nearest intersection points on each side
    (left and right) with a reference geometry (e.g., valley walls).

    Parameters:
        transect_layer (QgsVectorLayer): Transect lines with 't_ID' field.
        other_layer (QgsVectorLayer): Intersecting lines (e.g., valley edges).
        split_layer (QgsVectorLayer): Stream network with 't_ID', used for direction.
        tolerance (float): Distance threshold to filter near-duplicate points.
        debug (bool): If True, prints intersection metadata for diagnostics.

    Returns:
        tuple: Four lists of tuples (point, t_ID, distance):
            left_first, left_second, right_first, right_second
    """

    # Preload features
    transect_features = list(transect_layer.getFeatures())
    other_features = list(other_layer.getFeatures())
    stream_segments = {f['t_ID']: f for f in split_layer.getFeatures()}
    other_index = QgsSpatialIndex(other_layer.getFeatures())  # spatial index for fast lookups

    # Output holders
    left_first, left_second = [], []
    right_first, right_second = [], []

    for transect in transect_features:
        t_id = transect['t_ID']
        transect_geom = transect.geometry()
        midpoint = transect_geom.interpolate(transect_geom.length() / 2).asPoint()

        stream_segment = stream_segments.get(t_id)
        if not stream_segment:
            continue  # Skip if no stream segment found for this transect

        # Use stream flow direction from start to midpoint
        stream_geom = stream_segment.geometry()
        stream_start = stream_geom.vertexAt(0)
        stream_mid = stream_geom.interpolate(stream_geom.length() / 2).asPoint()

        direction_vector = QgsPointXY(
            stream_mid.x() - stream_start.x(),
            stream_mid.y() - stream_start.y()
        )

        # Spatial filter
        nearby_ids = other_index.intersects(transect_geom.boundingBox())
        nearby_feats = [f for f in other_features if f.id() in nearby_ids]

        # Temporary lists for this transect
        left_candidates = []
        right_candidates = []

        for other in nearby_feats:
            other_geom = other.geometry()
            if not transect_geom.intersects(other_geom):
                continue

            # Compute intersection geometry
            intersection = transect_geom.intersection(other_geom)
            points = []

            # Handle different geometry types robustly
            if intersection.isMultipart():
                points.extend(intersection.asMultiPoint())
            elif intersection.wkbType() == QgsWkbTypes.Point:
                points.append(intersection.asPoint())
            elif intersection.wkbType() == QgsWkbTypes.MultiPoint:
                points.extend(intersection.asMultiPoint())
            elif intersection.wkbType() == QgsWkbTypes.GeometryCollection:
                for i in range(intersection.numGeometries()):
                    g = intersection.geometryN(i)
                    if g.wkbType() == QgsWkbTypes.Point:
                        points.append(g.asPoint())

            for pt in points:
                # Skip very close-to-midpoint duplicates
                if pt.distance(QgsPointXY(midpoint)) < tolerance:
                    continue

                # Vector from stream midpoint to this point
                vec = QgsPointXY(pt.x() - stream_mid.x(), pt.y() - stream_mid.y())

                # Determine side
                cross = direction_vector.x() * vec.y() - direction_vector.y() * vec.x()
                side = "left" if cross > 0 else "right"

                dist = midpoint.distance(pt)

                # Store
                if side == "left":
                    left_candidates.append((pt, t_id, dist))
                else:
                    right_candidates.append((pt, t_id, dist))

                # Optional debug info
                if debug:
                    print(f"t_ID {t_id}: side={side} | dist={dist:.2f} | cross={cross:.4f}")

        # Sort by distance and retain top 2
        left_sorted = sorted(left_candidates, key=lambda x: x[2])
        right_sorted = sorted(right_candidates, key=lambda x: x[2])

        if len(left_sorted) > 0:
            left_first.append(left_sorted[0])
        if len(left_sorted) > 1:
            left_second.append(left_sorted[1])
        if len(right_sorted) > 0:
            right_first.append(right_sorted[0])
        if len(right_sorted) > 1:
            right_second.append(right_sorted[1])

    return left_first, left_second, right_first, right_second

# --- Compute valley width by summing left and right distances ---
from qgis.core import (
    QgsVectorLayer, QgsFeature, QgsField, QgsFeatureRequest,
    QgsWkbTypes, QgsProject, QgsGeometry, QgsPointXY, QgsFields
)
from PyQt5.QtCore import QVariant

def compute_valley_width(center_layer, left_points, right_points, out_field="VW"):
    """
    Calculates total valley width by summing distances from center point
    to the nearest left and right intersections.

    Returns a new QgsVectorLayer with the calculated values.
    """
    # Clone layer
    provider = center_layer.dataProvider()
    fields = center_layer.fields()
    crs = center_layer.sourceCrs()
    cloned_layer = QgsVectorLayer(f"Point?crs={crs.authid()}", "updated_centers", "memory")
    cloned_layer_data = cloned_layer.dataProvider()
    cloned_layer_data.addAttributes(fields)
    cloned_layer.updateFields()

    # Add output field if missing
    if cloned_layer.fields().indexFromName(out_field) == -1:
        cloned_layer_data.addAttributes([QgsField(out_field, QVariant.Double)])
        cloned_layer.updateFields()

    # Build distance dictionaries
    def build_distance_dict(points):
        distance_dict = {}
        for point, tid, distance in points:
            distance_dict[tid] = distance_dict.get(tid, 0) + distance
        return distance_dict

    left_distances = build_distance_dict(left_points)
    right_distances = build_distance_dict(right_points)

    features = []
    for feat in center_layer.getFeatures():
        new_feat = QgsFeature(cloned_layer.fields())
        new_feat.setGeometry(feat.geometry())
        new_feat.setAttributes(feat.attributes())

        tid = feat["t_ID"]
        lw = left_distances.get(tid, 0)
        rw = right_distances.get(tid, 0)

        new_attrs = new_feat.attributes()
        if out_field in center_layer.fields().names():
            new_attrs[cloned_layer.fields().indexFromName(out_field)] = lw + rw
        else:
            new_attrs.append(lw + rw)
        new_feat.setAttributes(new_attrs)

        features.append(new_feat)

    cloned_layer.startEditing()
    cloned_layer.addFeatures(features)
    cloned_layer.commitChanges()

    return cloned_layer

