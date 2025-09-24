# OpenRES Function Description

## [1] Generate Transects

- **Algorithm class:** `GenerateTransectsAlgorithm`
- **Input layers:**
  - `RIVER_LAYER` – Polyline river network layer
  - `LINE_LAYER` – Valley boundary lines (polyline)
- **Outputs:**
  - `TRANSECTS` – MultiLineString transect lines
  - `CENTER_POINTS` – Point layer representing transect midpoints
- **Logic:**
  - For each river feature:
    - Compute the midpoint along the river line geometry.
    - Calculate perpendicular angle at the midpoint using neighboring vertices.
    - Extend lines iteratively from midpoint in left and right perpendicular directions until two intersection points with `LINE_LAYER` are found on each side.
    - Combine left and right line extensions into a single transect line.
    - Create a transect feature and a midpoint point feature, each assigned a unique `t_ID`.
    - Update the original river layer features with this `t_ID` for referencing.
- **Optimizations:**
  - Utilizes `QgsSpatialIndex` on valley boundary lines to quickly find intersections.
  - Handles multi-part geometries and geometry collections robustly.
  - Deduplicates intersection points to prevent errors.
  - Incremental extension approach for precise intersection discovery.

---

## [2] Extract Point Data (ELE, PRE, GEO)

- **Algorithm class:** `ExtractPointDataAlgorithm`  
- **Input layers and data:**
  - `POINTS` – Segment centers (point vector)
  - `RASTER1` – Elevation raster
  - `RASTER2` – Precipitation raster
  - `POLYGONS` – Geology polygons
  - `POLY_FIELD` – Geometry attribute field name from polygons  
- **Outputs:**
  - `OUTPUT` – Point layer of segment centers enriched with new attributes (ELE, PRE, GEO)  
- **Logic:**
  - Create an in‐memory copy of the input point layer.
  - Add new fields if not present: `ELE` (Double), `PRE` (Double), `GEO` (String).
  - For each point:
    - Sample `RASTER1` to get elevation → store in `ELE`.
    - Sample `RASTER2` to get precipitation → store in `PRE`.
    - Use a spatial index on polygons to find the containing geology polygon and fetch its `POLY_FIELD` → store in `GEO`.
  - Handle missing raster values or absent polygon matches by supplying default values (e.g. `-9999` or `"No Data"`).
  - Commit changes and write the enriched point layer to the destination sink.  
- **Technical Notes:**
  - Uses `QgsRasterLayer.dataProvider().identify()` for raster sampling.
  - Builds `QgsSpatialIndex` for polygons to speed containment tests.
  - Supports single- and multipart point geometries.
  - Attribute updating is done in batch inside an editing session.
  - Progress is reported periodically via `QgsProcessingFeedback`.

---

## [3] Extract Valley Width (VW) and Valley Floor Width (VFW)

- **Algorithm class:** `ExtractValleyWidthsAlgorithm`
- **Input layers:**
  - `TRANSECTS` – MultiLineString transect lines with `t_ID`
  - `CENTER_POINTS` – Point layer (segment centers)
  - `VALLEY_LINES` – Polyline valley boundary lines
  - `STREAMS` – River network polyline layer
- **Outputs:**
  - `LEFT_VW`, `RIGHT_VW` – Point layers representing left and right valley width reference points
  - `LEFT_VFW`, `RIGHT_VFW` – Point layers representing left and right valley floor width reference points
  - Updated segment centers with VW and VFW attributes
- **Logic:**
  - For each transect:
    - Intersect with valley boundary lines and streams to locate intersection points on both sides (left and right).
    - From intersection points, derive valley width (VW) and valley floor width (VFW) as distances between left-right pairs.
    - Create and store reference points with attributes `side` (left/right), `t_ID`, and distance measurements.
    - Assign valley width attributes back to segment centers using `t_ID` as linkage.
- **Technical Details:**
  - Employs geometric intersection methods to find points.
  - Uses in-memory `QgsVectorLayer` for temporary storage of reference points.
  - Attribute management includes `QgsField` and careful indexing.
  - Output layers saved via `QgsFeatureSink`.
  - CRS inheritance maintained from transect inputs.

---

## [4] Extract Left and Right Valley Side Slopes (LVS, RVS)

- **Algorithm class:** `ExtractSideSlopesAlgorithm`
- **Input layers:**
  - `CENTER` – Point layer of segment centers
  - `LEFT_VW`, `LEFT_VFW` – Left valley width and valley floor width reference point layers
  - `RIGHT_VW`, `RIGHT_VFW` – Right valley width and valley floor width reference point layers
  - `RASTER` – Elevation raster layer
- **Outputs:**
  - Updated segment center points with LVS and RVS attributes
- **Logic:**
  - Make a safe in-memory copy of the segment centers for editing.
  - For each pair of valley width and valley floor width points on left and right sides:
    - Sample elevation raster at these points.
    - Compute side slope as elevation difference divided by horizontal distance.
  - Store computed LVS and RVS back into the segment centers.
- **Technical Details:**
  - Raster sampling performed with `QgsRasterLayer` and `identify` method.
  - Calculation delegated to helper function `calculate_side_slopes_from_pairs`.
  - Vector layers managed with QgsVectorLayer and QgsFeatureSink for output.
  - Attribute update done inside editing session.

---

## [5] Extract Down Valley Slope (DVS) and Sinuosity (SIN)

- **Algorithm class:** `ExtractDVSAlgorithm`
- **Input layers:**
  - `CENTER_POINTS` – Point layer of segment centers with `t_ID`
  - `STREAM_SEGMENTS` – River network polyline layer with matching `t_ID`
  - `ELEVATION` – Elevation raster layer
- **Outputs:**
  - Updated segment center points enriched with `DVS` and `SIN` attributes
- **Logic:**
  - Create an editable in-memory copy of segment centers.
  - Add missing fields for DVS and SIN.
  - Build dictionary mapping `t_ID` to stream segment features for quick access.
  - For each center point:
    - Retrieve corresponding stream segment.
    - Extract start and end points of stream geometry.
    - Sample elevation raster at start and end points.
    - Calculate:
      - **DVS:** Percent slope along the stream segment (elevation drop / stream length * 100).
      - **SIN:** Sinuosity as ratio of stream length to straight-line distance between segment endpoints.
    - Update attributes with computed values.
  - Commit edits and write output.
- **Technical Details:**
  - Uses `QgsRasterLayer.identify` for raster sampling.
  - Geometry handled using `QgsGeometry` and `QgsPointXY`.
  - Attribute updates managed within a QgsVectorLayer editing session.
  - Progress reported periodically via `QgsProcessingFeedback`.
  - Robust handling of missing elevation or geometry data.

---



*End of description*
