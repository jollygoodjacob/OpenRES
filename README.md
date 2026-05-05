# Open Riverine Ecosystem Synthesis (OpenRES):

## A QGIS plugin for automated extraction of hydrogeomorphic features to support functional process zone classification of river networks

[![Open Source Love svg1](https://badges.frapsoft.com/os/v1/open-source.svg?v=103)](https://github.com/ellerbrock/open-source-badges/) [![made-with-python](https://img.shields.io/badge/Made%20with-Python-ffd040.svg)](https://www.python.org/) [![License: GPL v3](https://img.shields.io/badge/License-GPL%20v3-blue.svg)](%5Bhttps://www.gnu.org/licenses/old-licenses/gpl-3.0.html%5D(https://www.gnu.org/licenses/gpl-3.0.html#license-text)) [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.17196890.svg)](https://doi.org/10.5281/zenodo.17196890) [![OpenRES](https://img.shields.io/badge/QGIS%20Repo-OpenRES-589632)](https://plugins.qgis.org/plugins/OpenRES) [![GitHub release](https://img.shields.io/github/v/release/jollygoodjacob/OpenRES)](https://github.com/jollygoodjacob/OpenRES/releases) [![GitHub commits](https://img.shields.io/github/commits-since/jollygoodjacob/OpenRES/v1.4.1)](https://github.com/jollygoodjacob/OpenRES/commits) [![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg)](https://GitHub.com/jollygoodjacob/OpenRES/graphs/commit-activity)

## General Information

**OpenRES** enables QGIS users to extract up to fifteen physical and environmental features along river segments (typically 5--10 km) to support classification of river networks into **Functional Process Zones (FPZs)**.

**Functional Process Zone (FPZ)** classification is a method used to divide a river network into river valley scale (5-10 km) segments (or "zones") that share similar physical, hydrological, and geomorphic characteristics. Rather than treating a river as a continuous longitudinal gradient of changing physical conditions, FPZ classification recognizes that rivers are composed of a discontinuous set of hydrogeomorphic patches, each shaped by different landscape and hydrologic processes ([Hestir 2007](https://www.researchgate.net/profile/Erin-Hestir/publication/265026989_Functional_Process_Zones_and_the_River_Continuum_Concept/links/546248c00cf2c0c6aec1ade8/Functional-Process-Zones-and-the-River-Continuum-Concept.pdf)). These zones reflect how the river behaves in a given segment, including how it flows, how it transports sediment, how it interacts with its floodplain, and what types of habitats it supports.

After classifying a river network in FPZs, research questions posed by the tenets of the Riverine Ecosystem Synthesis hypothesis ([Thorp et al. 2006](https://onlinelibrary.wiley.com/doi/abs/10.1002/rra.901), [Thorp et al. 2023](https://www.frontiersin.org/journals/ecology-and-evolution/articles/10.3389/fevo.2023.1184433/full)) can be explored.

------------------------------------------------------------------------

## Installation

> **Note:** OpenRES requires QGIS version \>=3.28.

**Installation from QGIS:**

-   Open QGIS -\> Plugins -\> Manage and Install Plugins... -\> select All tab -\> search for OpenRES --\> select and install plugin

**Offline installation from .zip file** :

-   Go to releases of this repository -\> select desired version -\> download the .zip file (Note: use OpenRES.zip, not the source .tar).

-   Open QGIS -\> Plugins -\> Manage and Install Plugins... -\> install from ZIP tab --\> select the downloaded zip --\> install plugin (ignore warnings, if any).

------------------------------------------------------------------------

## Data Prerequisites

Users should prepare the following **six datasets** for your watershed of interest. Use consistent CRS and units (projected meters recommended, e.g., UTM) for all layers.

| Dataset | Format | Description |
|----|----|----|
| **Mean Annual Precipitation Layer** | `.tif` | Raster of mean annual precipitation for the watershed. |
| **Digital Elevation Model (DEM) Layer** | `.tif` | Elevation raster used for slopes, valley floors, and longitudinal gradients. |
| **Simplified Geology Layer** | `.shp` | Polygon layer with generalized classes (e.g., alluvial, mixed, bedrock). Typically a simplified version of a detailed map. |
| **Geomorphically Corrected Stream Network Layer** | `.shp` | Stream lines generated from the DEM and manually corrected to follow observed channel positions in imagery for the analysis period (Whitebox Workflows recommended here). |
| **Valley-Boundary Line Layer** | `.shp` | Lines delineating both the valley floor boundary and valley-edge boundary. Suggested workflow: (1) delineate valley floor, (2) edit to remove holes and unrealistic extents, (3) derive 1-2 km² microsheds/isobasins from the DEM (Whitebox Workflows recommended here), (4) apply intersection/difference/polygon-to-line to extract combined boundaries as a line feature. |
| **Channel Belt Layer** (Optional) | `.shp` | Lines delineating the channel belt (active/recent fluvial influence, including channel and depositional features). Suggested workflow: (1) OpenRES → Geomorphology Tools → Generate Channel Belt, (2) manual refinement to match meanders and depositional forms visible in imagery. |

Some of these layers may not be very common for most river systems (especially the **Valley-Boundary Line Layer** and **Channel Belt Layer**). For these less common datasets, `OpenRES` provides several geomorphology utility tools to allow users to create these datasets for their watershed of interest.

**Data quality tips**

-   Ensure all inputs share the same projected CRS and unit (meters)

-   Snap and clean linework to avoid sliver gaps that can break intersections

------------------------------------------------------------------------

## Core Functionality

**OpenRES** provides geomorphology utilities to prepare key boundary layers and a set of sequential extraction tools that produce a standard suite of **15 hydrogeomorphic attributes** for FPZ classification.

### Geomorphology Tools

Use these tools to produce your **Valley-Boundary Line Layer** and **Channel Belt** .

`OpenRES` includes geomorphology utility tools to help users prepare the valley boundaries and channel belt layers required for subsequent feature extraction \autoref{tab:geomorph-tools}:

| Tool | Purpose | Output | GIS Data Type |
|----|----|----|----|
| Generate Channel Belt | Creates lateral offsets from the stream network to approximate the channel belt extent; intended for manual refinement. | Channel belt layer | Vector (line) |
| Valley Floor Delineation – Sechu | Identifies low-relief valley floor areas from a DEM using a slope-based cost accumulation method [@sechu_2021]. | Valley floor layer | Vector (polygon) |
| Generate Microsheds | Generates microsheds using a threshold-based watershed approach (1–3 km² typical) to capture valley tops in confining valleys. | Microshed layer | Vector (polygon) |
| Create Valley Boundary | Applies a difference operation between valley floor and microsheds and converts the result to a line layer representing valley boundaries. | Valley boundary layer | Vector (line) |

### Data Extraction Tools

Run these tools in order. Together, they generate all attributes required for FPZ classification.

| Step / Tool | Features | Description | Required |
|----|----|----|----|
| [1] Generate Transects | t_ID | Generates perpendicular transects from river centerlines to valley boundaries, ensuring consistent sampling and linking outputs via a transect ID. | Yes |
| [2] Extract ELE, PRE, and GEO | ELE, PRE, GEO | Samples elevation, precipitation, and geologic class from user-provided datasets. | Yes |
| [3] Extract VW, VFW, and RAT | VW, VFW, RAT | Measures valley width and valley floor width from transects and computes their ratio. | Yes |
| [4] Extract LVS, RVS, and MVS | LVS, RVS, MVS | Computes left, right, and mean valley slopes from elevation differences along transects. | Yes |
| [5] Extract DVS and SIN | DVS, SIN | Calculates down-valley slope and river sinuosity from segment geometry. | Yes |
| [6] Extract CBW | CBW | Measures channel belt width from transect intersections with the channel belt layer. | Optional |
| [7] Extract LCS, RCS, and CBS | LCS, RCS, CBS | Quantifies within-belt channel sinuosity on each side and summarizes with a mean value. | Optional |

------------------------------------------------------------------------

## Example usage: Eerste River catchment, South Africa

> **Note:** All the following processing steps should be done in a sequential manner, following the instructions below. Sample data for hydrogeomorphic feature extraction is provided in [sample_data](/sample_data/) folder.

To demonstrate the use of OpenRES, we have provided a dataset from the Eerste River catchment, a small watershed located in the Greater Cape Floristic Region of South Africa.

::: {align="center"}
<img src="/imgs/Eerste_watershed.png" alt="Eerste River catchment, South Africa" width="600"/><br> <sub><b> Eerste River catchment, South Africa</b></sub>
:::

The Eerste River originates in the Jonkershoek Mountains, part of the Hottentots-Holland mountain range, and flows westward through the Stellenbosch area before reaching the False Bay coast near Strand. It drains a catchment area of approximately 390 km². Dominated by fynbos vegetation, the area hosts numerous endemic plant species and is under increasing pressure from urban development, invasive species, and agricultural runoff.

------------------------------------------------------------------------

### Prerequisites

Before starting the OpenRES workflow:

-   Ensure all input data are properly prepared:
    -   Mean annual precipitation (raster)
    -   Digital Elevation Model (\<= 30 m DEM, raster)
    -   Simplified geologic class layer (i.e., alluvial, non-alluvial, bedrock; vector - polygon).
    -   Stream network (vector - line)
    -   Valley-boundary layer (vector - line)
    -   (Optional) Channel belt layer (vector - line)
-   The **OpenRES** plugin is installed and enabled in QGIS.
-   The **Processing Toolbox** is open (via `Processing > Toolbox`).

::: {align="center"}
<img src="/imgs/OpenRES_processing_toolbox.png" alt="The OpenRES Processing Toolbox" width="300"/><br> <sub><b> The OpenRES Processing Toolbox</b></sub>
:::

------------------------------------------------------------------------

### Using the Geomorphology Tool to Prepare Input Data

#### Generate Channel Belt Layer

Use `"Generate Channel Belt"`\

Location: `Processing Toolbox > OpenRES > Geomorphology`

::: {align="center"}
<img src="imgs/generate_channel_belt_window.png" width="800"/>
:::

##### Inputs

-   **River Network Layer** (polyline)

##### Outputs

-   **Channel Belt Layer**

##### Notes

-   Offsets each input stream segment to LEFT (+) and RIGHT (-) by the given distance.
-   Offsets use layers CRS; use a projected CRS (e.g., meters).
-   LEFT/RIGHT are relative to the digitized direction of each line
-   Use `Round` join style for smooth banks; `Miter` for sharp corners (user will have to tune miter limit).
-   Copies `t_ID` from input if present, otherwise creates sequential `t_ID`.
-   Adds fields `t_ID` (int), `side` {'LEFT'\|'RIGHT'}, `offset` (double).

> **Note:** You must edit this layer to capture the channel belt appropriately. This means delineating areas of active/recent fluvial influence, including channel and depositional features AND removing areas with no visible channel belt.

#### Delineate Valley Floor

Use `"Valley Floor Delineation - Sechu"`

Location: `Processing Toolbox > OpenRES > Geomorphology`

::: {align="center"}
<img src="imgs/valley_floor_delin_window.png" width="800"/>
:::

##### Inputs

-   **River Network Layer** (polyline)
-   **Elevation Raster**

##### Outputs

-   **Valley Floor Layer** (MultiPolygon)

##### Notes

-   Delineates valley bottom by building slope from DEM, using slope as cost surface in GRASS r.cost from a stream network, taking an initial (max) cost threshold, computing mean cost inside that belt, re-thresholding with that mean, and cleaning, smoothing and filling skinny gaps.
-   Initial cost distance threshold: `[500*(resolution/10m)]` is a good starting point

#### Generate Microsheds

Use `"Generate Microsheds"`

Location: `Processing Toolbox > OpenRES > Geomorphology`

::: {align="center"}
<img src="imgs/generate_microsheds_window.png" width="800"/>
:::

##### Inputs

-   **Input DEM**

##### Parameters

-   **Threshold**: minimum exterior basin size in cells
-   **GRASS memory**: memory allocated to GRASS `r.watershed`, in MB

##### Outputs

-   **Output basins raster**
-   **Microsheds** polygon layer

##### Notes

-   Runs GRASS `r.watershed` to generate uniquely labeled watershed basins from an input DEM.
-   The threshold controls the minimum exterior basin size in raster cells.
-   The polygon output is created by polygonizing the labeled basin raster using `basin_id` as the output field.
-   A threshold corresponding to approximately 2–3 km² is a useful starting point, depending on DEM resolution.

#### Create Valley Boundary

Use `"Create Valley Boundary"`

Location: `Processing Toolbox > OpenRES > Geomorphology`

::: {align="center"}
<img src="imgs/create_valley_boundary_window.png" width="800"/>
:::

##### Inputs

-   **Microsheds polygons**
-   **Valley floor polygons**

##### Parameters

-   **Smoothing iterations**
-   **Smoothing offset**
-   **Maximum node angle**

##### Outputs

-   **Valley boundary lines**

##### Notes

-   Selects microshed polygons that intersect the valley floor, subtracts the valley floor polygons from those microsheds, then converts the remaining polygon boundaries to lines.
-   The resulting linework is lightly smoothed and dissolved to create a continuous valley boundary layer.
-   The output should delineate the valley floor boundary and the confining valley margins.
-   Lower smoothing values preserve sharper geomorphic breaks; higher values produce cleaner but more generalized boundaries.

------------------------------------------------------------------------

### Overview of Extracted Features

The following table summarizes the 15 geomorphic and environmental features that will be automatically derived across the Eerste River catchment using the OpenRES tool suite. Each transect, generated perpendicular to the stream network, will be assigned a unique identifier `t_ID`, and the attributes listed below will be extracted or calculated at the transect or segment level. Transects, segment centers, and the river network segments are all linked together by the `t_ID` field, enabling subsequent FPZ classification methods to link using joins and relates to the stream network, river segment centers, or transects as desired for visualization purposes.

| Feature | Name | Hydrogeomorphic role |
|----|----|----|
| ELE | Elevation | Longitudinal position and energy gradient |
| PRE | Precipitation | Hydroclimatic setting |
| GEO | Geologic class | Substrate and structural control |
| VW | Valley Width | Lateral accommodation space at the valley scale |
| VFW | Valley Floor Width | Floodplain/low relief valley floor extent |
| RAT | VW:VFW Ratio | Relative valley confinement |
| LVS | Left Valley Slope | Left side valley confinement |
| RVS | Right Valley Slope | Right side valley confinement |
| MVS | Mean Valley Slope | Overall valley confinement |
| DVS | Down Valley Slope | Longitudinal channel gradient |
| SIN | River Sinuosity | Planform complexity of the river |
| CBW | Channel Belt Width | Active channel belt extent |
| LCS | Left Channel Sinuosity | Left side within-belt planform curvature |
| RCS | Right Channel Sinuosity | Right side within-belt planform curvature |
| CBS | Channel Belt Sinuosity | Mean within-belt planform curvature |

------------------------------------------------------------------------

### Step 1: Generate Transects

Use: `"[1] Generate Transects"`\
Location: `Processing Toolbox > OpenRES > Feature Extraction`

::: {align="center"}
<img src="imgs/generate_transects_window.png" width="800"/>
:::

#### Inputs

-   **River Network Layer** (polyline)
-   **Valley Lines Layer** (line)
-   **Extension Increment** (optional, default = 250m)
-   **Max Length** (optional, default = 50000m)

#### Outputs

-   **Transects** -- Multiline layer across the valley
-   **Segment Centers** -- Points at the center of each transect

#### Notes

-   Each river segment gets a unique `t_ID`.
-   Transects are generated perpendicular to the river segment direction.
-   **Verify** that transects intersect both valley lines properly; occasional mismatches may occur due to geometry errors.
-   Stream network will also be updated to include the `t_ID` field.

------------------------------------------------------------------------

### Step 2: Extract Elevation, Precipitation, and Geology

Use: `"[2] Extract Point Data"`\
Location: `Processing Toolbox > OpenRES > Feature Extraction`

::: {align="center"}
<img src="imgs/extract_point_window.png" width="800"/>
:::

#### Inputs

-   **Segment Centers Layer** (from Step 1)
-   **Elevation Raster**
-   **Precipitation Raster**
-   **Geology Polygon Layer**
-   **Geology Field** (attribute from polygon layer, e.g., `GEO` or `LITH`)

#### Output

-   **Segment Centers with ELE, PRE, GEO** -- Updated point layer

#### Notes

-   Elevation and precipitation are sampled directly from rasters.
-   Geology is assigned from intersecting polygon based on the selected field.
-   Missing data (e.g., no polygon overlap or invalid raster) will be filled with fallback values (e.g., -9999 or "No Data").

------------------------------------------------------------------------

### Step 3: Extract Valley Width (VW), Valley Floor Width (VFW), and their ratio (RAT)

Use: `"[3] Extract VW, VFW", and RAT`\
Location: `Processing Toolbox > OpenRES > Feature Extraction`

::: {align="center"}
<img src="imgs/extract_vw_window.png" width="800"/>
:::

#### Inputs

-   **Transects Layer** (from Step 1)
-   **Segment Centers Layer** (from Step 2)
-   **Valley Lines Layer**
-   **Stream Network Layer**

#### Outputs

-   **Left/Right VFW Reference Points**
-   **Left/Right VW Reference Points**
-   **Updated Segment Centers** with:
    -   `VFW` -- Valley floor width
    -   `VW` -- Valley width

#### Notes

-   Uses intersection logic to find points where transects intersect valley floor and valley edge.
-   Then calculates distance between these intersections to compute `VFW` and `VW`.
-   Reference points (left/right) are saved as point layers for inspection or QA/QC.

------------------------------------------------------------------------

### Step 4: Extract Side Slopes (LVS, RVS, and MVS)

Use: `"[4] Extract LVS, RVS, and MVS"`\
Location: `Processing Toolbox > OpenRES > Feature Extraction`

::: {align="center"}
<img src="imgs/lvs_rvs_window.png" width="800"/>
:::

#### Inputs

-   **Segment Centers Layer** (from Step 3)
-   **Left VW / VFW Reference Points**
-   **Right VW / VFW Reference Points**
-   **Elevation Raster**

#### Output

-   **Segment Centers** updated with:
    -   `LVS` -- Left valley side slope (%)
    -   `RVS` -- Right valley side slope (%)

#### Notes

-   Slopes are computed as the elevation difference between VFW and VW reference points on each side divided by the horizontal distance.
-   All calculations are in percent slope (`rise/run * 100`).
-   Output replaces the segment center layer with updated slope fields.

------------------------------------------------------------------------

### Step 5: Extract Down-Valley Slope and Sinuosity (DVS and SIN)

Use: `"[5] Extract DVS and SIN"`\
Location: `Processing Toolbox > OpenRES > Feature Extraction`

::: {align="center"}
<img src="imgs/dvs_sin_window.png" width="800"/>
:::

#### Inputs

-   **Segment Centers Layer** (from Step 4)
-   **Stream Network Layer**
-   **Elevation Raster**

#### Output

-   **Segment Centers** updated with:
    -   `DVS` -- Down-valley slope (%)
    -   `SIN` -- Sinuosity (unitless)

#### Notes

-   For each stream segment:
    -   Elevation is sampled at start and end points.
    -   `DVS` is calculated as `(start - end) / length * 100`.
    -   `SIN` is the ratio of actual segment length to straight-line distance.
-   Features with insufficient geometry or elevation data are skipped.

### Step 6: Extract Channel Belt Width (CBW)

Use: `"[6] Extract CBW"\  Location:`Processing Toolbox \> OpenRES \> Feature Extraction\`

::: {align="center"}
<img src="imgs/extract_cbw_window.png" width="800"/>
:::

#### Inputs

-   **Transects Layer**
-   **Segment Centers Layer** (from Step 5)
-   **Channel Belt Layer** (may be generated from `Geomorphology > Generate Channel Belt`
-   **River Network Layer**

#### Output

-   **Left Channel Belt Width Reference**
-   **Right Channel Belt Width Reference**
-   **Segment Centers** updated with: - Channel belt width

#### Notes

-   Uses intersection logic to find points where transects intersect the channel belt right and left reference.
-   Then calculates distance between these intersections to compute 'CBW'.
-   Reference points (left/right) are saved as point layers for inspection or QA/QC.

### Step 7: Extract Left, Right and Center Channel Sinuosity

Use: `"[7] Extract LCS, RCS, and CBS"`\
Location: `Processing Toolbox > OpenRES > Feature Extraction`

#### Inputs

-   **Transects Layer**
-   **Segment Centers Layer** (from Step 5)
-   **Channel Belt Layer** (may be generated from `Geomorphology > Generate Channel Belt`)
-   **River Network Layer**

#### Output

-   **Left Channel Sinuoisty** (LCS)
-   **Right Channel Sinuosity** (RCS)
-   **Channel Belt Sinuosity** (CBS)
-   **Segment Centers** updated with:
    -   Left channel sinuoisty
    -   Right channel sinuoisty
    -   Channel belt sinuosity

------------------------------------------------------------------------

### Completion

At the end of Step 7, your segment center point layer will contain **all 15 hydrogeomorphic attributes**:

-   `t_ID`, `ELE`, `PRE`, `GEO`, `VFW`, `VW`, `RAT`,`LVS`, `RVS`,`MVS`, `DVS`, `SIN`, `CBW`, `LCS`, `RCS`, `CBS`

::: {align="center"}
<img src="imgs/openres_output_table.png" width="800"/>
:::

The extracted attributes from `OpenRES` can be joined to the river network output from **[1] Generate Transects:** by using `t_ID` as the joining feature, then exported to Python, R, or another software for hierarchical clustering analyses commonly used to delineate FPZs.

To assist users in this process, we developed a separate Shiny app in R, ShinyFPZ, which contains common methods for FPZ classification as well as visualization tools for OpenRES output data.

For users preferring to stay in the QGIS environment for this step, there are also QGIS plugins that contain the appropriate capabilities, such as the Attribute based clustering plugin.

------------------------------------------------------------------------

## Issues

1)  Report issues or problems with the software here: <https://github.com/jollygoodjacob/OpenRES/issues>

2)  For questions about the OpenRES plugin, contact: [jnesslage\@ucmerced.edu](mailto:jnesslage@ucmerced.edu){.email}

## References

Elgueta, Anaysa, Martin C Thoms, Konrad Górski, Gustavo Díaz, and Evelyn M Habit. 2019. "Functional Process Zones and Their Fish Communities in Temperate Andean River Networks." River Research and Applications 35 (10): 1702--11.

Hestir, Erin L. 2007. "Functional Process Zones and the River Continuum Concept." Center for Watershed Sciences, University of California, Davis, Los Angeles, USA.

Maasri, Alain, James H Thorp, Jon K Gelhaus, Flavia Tromboni, Sudeep Chandra, and Scott J Kenner. 2019. "Communities Associated with the Functional Process Zone Scale: A Case Study of Stream Macroinvertebrates in Endorheic Drainages." Science of the Total Environment 677: 184--93.

Sechu, Gasper L., Bertel Nilsson, Bo V. Iversen, Mette B. Greve, Christen D. Børgesen, and Mogens H. Greve. 2021. "A Stepwise GIS Approach for the Delineation of River Valley Bottom within Drainage Basins Using a Cost Distance Accumulation Analysis." *Water* 13 (6). <https://doi.org/10.3390/w13060827>.

Thorp, James H, Martin C Thoms, and Michael D Delong. 2006. "The Riverine Ecosystem Synthesis: Biocomplexity in River Networks across Space and Time." River Research and Applications 22 (2): 123--47.

Thorp, James H, Martin C Thoms, and Michael D Delong. 2010. The Riverine Ecosystem Synthesis: Toward Conceptual Cohesiveness in River Science. Elsevier.

Thorp, James H, Martin C Thoms, Michael D Delong, and Alain Maasri. 2023. "The Ecological Nature of Whole River Macrosystems: New Perspectives from the Riverine Ecosystem Synthesis." Frontiers in Ecology and Evolution 11: 1184433.

Williams, Bradley S, Ellen D'Amico, Jude H Kastens, James H Thorp, Joseph E Flotemersch, and Martin C Thoms. 2013. "Automated Riverine Landscape Characterization: GIS-Based Tools for Watershed-Scale Research, Assessment, and Management." Environmental Monitoring and Assessment 185: 7485--99.
