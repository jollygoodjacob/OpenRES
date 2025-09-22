# Open Riverine Ecosystem Synthesis (OpenRES):

## A QGIS plugin for automated extraction of hydrogeomorphic features to support functional process zone classification of river networks

### A Python based [QGIS](https://qgis.org/en/site/index.html) plugin 
[![Open Source Love svg1](https://badges.frapsoft.com/os/v1/open-source.svg?v=103)](https://github.com/ellerbrock/open-source-badges/)
[![made-with-python](https://img.shields.io/badge/Made%20with-Python-ffd040.svg)](https://www.python.org/)
[![License: GPL v2](https://img.shields.io/badge/License-GPL%20v2-blue.svg)](https://www.gnu.org/licenses/old-licenses/gpl-2.0.html)
[![DOI]()]()
[![GitHub release](https://img.shields.io/github/v/release/jollygoodjacob/OpenRES)](https://github.com/jollygoodjacob/OpenRES/releases)
[![GitHub commits](https://img.shields.io/github/commits-since/jollygoodjacob/OpenRES/v1.0.0)](https://github.com/jollygoodjacob/OpenRES/commits)
[![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg)](https://GitHub.com/jollygoodjacob/OpenRES/graphs/commit-activity)

## Citation

If you use this plugin in your work, please cite it as:

## General Information

This plugin enables extraction of nine key hydrogeomorphic features
along user-defined segments of river networks for the purpose of
functional process zone classification. These features are:

1. Elevation (ELE)
2. Mean Annual Precipitation (PRE)
3. Geology (GEO)
4. Valley Floor Width (VFW)
5. Valley Width (VW)
6. Right Valley Slope (RVS)
7. Left Valley Slope (LVS)
8. Down Valley Slope (DVS)
9. Sinuosity (SIN)

There are five required datasets needed for extraction of
hydrogeomorphic features along a user's watershed of interest:

1.  A geomorphically corrected stream network (.shp)
2.  A line layer denoting the boundaries of the valley floor and the
    valleys (.shp)
3.  A mean annual precipitation layer (.geotiff)
4.  A Digital Elevation Model (DEM) (.geotiff)
5.  A geology layer (.shp)

## Installation

> **Note:** OpenRES requires QGIS version \>=3.28.

**Offline installation from .zip file** :

Go to releases of this repository -\> select desired version -\>
download the .zip file. Open QGIS -\> Plugins -\> Manage and Install
Plugins... -\> install from ZIP tab --\> select the downloaded zip --\>
install plugin (ignore warnings, if any).

## Example usage

> **Note:** All the following processing steps should be done in a
> sequential manner. Sample data for hydrogeomorphic feature extraction
> is provided in [sample_data](/sample_data/) folder.

### General data preparation steps

Install the latest version of QGIS (with access to Processing Toolbox).
Also, install the WhiteboxTools plugin for QGIS or install WhiteboxTools
standalone via GitHub.

Download and prepare the relevant datasets from the [NRCS Geospatial
Data Gateway](https://gdg.sc.egov.usda.gov/). In my experience, this is
the best single location to obtain each of these required data sets.

1.  Go to <https://datagateway.nrcs.usda.gov/>
2.  Click **"Get Data"**
3.  Under **Search Criteria**, select your area of interest using:
    -   **By State**
    -   **By County**
    -   **By HUC (Hydrologic Unit Code)** --- ✅ *Recommended for
        watershed work*
    -   **By Custom Shapefile** --- upload your own AOI
4.  Click **Continue (Step 2: Select Data Sets)**
5.  Check the boxes for relevant datasets (see below)
6.  Click **Continue**, provide your email address, and submit
7.  You'll receive a download link via email

#### Step 0: Identify watershed of interest and acquire watershed boundary layers

**Goal:** Get HUC8 watershed shapefile.

**In QGIS:**

1.  Load the **HUC8 shapefile** (`.shp`) via
    `Layer > Add Layer > Add Vector Layer`.
2.  Use the **Select Features** tool to select your watershed of
    interest.
3.  Right-click the layer \> `Export > Save Selected Features As...` to
    create a new layer.

#### Step 1: Acquire, mosaic, and clip elevation layer to watershed of interest

**Goal:** Prepare DEM from NED/3DEP.

**In QGIS:**

1.  **Mosaic DEM tiles:**
    -   `Raster > Miscellaneous > Merge`
    -   Input: All DEM `.tif` files
2.  **Clip to watershed:**
    -   `Raster > Extraction > Clip Raster by Mask Layer`
    -   Input layer: Merged DEM
    -   Mask layer: Watershed shapefile

#### Step 2: Acquire, mosaic, and clip precipitation layer to watershed of interest

**In QGIS:**

1.  **Mosaic PRISM rasters:**
    -   `Raster > Miscellaneous > Merge`
    -   Input: PRISM `.bil`, `.tif`, or `.asc` files
2.  **Clip to watershed:**
    -   Same as DEM: `Raster > Extraction > Clip Raster by Mask Layer`

#### Step 3: Acquire, clip, and simplify geology layer for watershed of interest

**In QGIS:**

1.  Load **USGS geology shapefile**.
2.  Clip to watershed:
    -   `Vector > Geoprocessing Tools > Clip`
3.  Simplify geometry (optional):
    -   `Vector > Geometry Tools > Simplify Geometry`
    -   Choose a tolerance (e.g., 50--100 meters depending on scale)

#### Step 4: Create a geomorphically corrected stream network

**In QGIS using the WhiteboxTools plugin:**

1.  **Fill Depressions:**
    -   `WhiteboxTools > Hydrological Tools > Fill Depressions (Wang & Liu)`
2.  **Generate Flow Direction:**
    -   `WhiteboxTools > Flow Pointer > D8 Flow Pointer`
3.  **Generate Flow Accumulation:**
    -   `WhiteboxTools > Flow Accumulation > D8 Flow Accumulation`
4.  **Extract Streams:**
    -   `WhiteboxTools > Stream Network Analysis > Extract Streams`
    -   Set appropriate threshold (e.g., 50,000-100,000 cells for a 10m
        DEM works well to capture major named rivers, in my experience)
5.  **Convert Raster to Vector Streams:**
    -   `WhiteboxTools > Stream Network Analysis > Raster Streams to Vector`

#### Step 5: Create a valley floor layer

**Option 1: Manual Digitization**

1.  Load a **hillshade** layer for visual reference.
2.  Use `Add Line Layer` to draw boundaries of the valley floor.
3.  Save as a new shapefile.

**Option 2: Semi-Automated via Cost Accumulation using Slope ()**

1.  **Calculate Slope:**

    -   `Raster > Terrain Analysis > Slope`

2.  **Extract low-slope areas:**

    -   `Raster Calculator`: e.g. `slope@1 < 5`

3.  **Convert to polygon:**

    -   `Raster > Conversion > Polygonize`

4.  **Buffer stream layer** (optional):
    `Vector > Geoprocessing > Buffer`

5.  **Extract features within buffer** to isolate valley floor areas.

6.  **Convert polygons to lines** (for valley edges):

    -   `Vector > Geometry Tools > Polygon to Lines`

#### Step 6: Create microsheds / isobasins layer

#### Step 7: Create line layer denoting valley bottom and valley boundaries

### OpenRES application


#### Step 8: Generate transects
Once a user has installed OpenRES and generated all required layers, they can begin using the OpenRES application through the Processing Toolbar in QGIS.

> **Note:** After transect generation, users should validate that each
> transect intersects valley bottoms and valleys properly. Due to
> geometry issues, it is possible that unexpected intersections can
> occur.

#### Step 9: Extract ELE, PRE, and GEO

#### Step 10: Extract VFW and VW

#### Step 11: Extract LVS and RVS

#### Step 12: Extract SIN and DVS

### After OpenRES: Hierarchical Classification into FPZs

## Functions description

Description and the details of all the core functions of this plugin are available here: [Description of Functions](help/Functions_description.md)

## Contributions
1) Contribute to the software: [Contribution guidelines for this project](help/CONTRIBUTING.md)

2) Report issues or problems with the software here: <https://github.com/jollygoodjacob/OpenRES/issues>

3) Feel free to contact us: <jnesslage@ucmerced.edu> 
