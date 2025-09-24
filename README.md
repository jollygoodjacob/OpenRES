# Open Riverine Ecosystem Synthesis (OpenRES):

## A [QGIS](https://qgis.org/en/site/index.html) plugin for automated extraction of hydrogeomorphic features to support functional process zone classification of river networks
[![Open Source Love svg1](https://badges.frapsoft.com/os/v1/open-source.svg?v=103)](https://github.com/ellerbrock/open-source-badges/)
[![made-with-python](https://img.shields.io/badge/Made%20with-Python-ffd040.svg)](https://www.python.org/)
[![License: GPL v3](https://img.shields.io/badge/License-GPL%20v3-blue.svg)](https://www.gnu.org/licenses/old-licenses/gpl-3.0.html)
[![DOI]()]()
[![GitHub release](https://img.shields.io/github/v/release/jollygoodjacob/OpenRES)](https://github.com/jollygoodjacob/OpenRES/releases)
[![GitHub commits](https://img.shields.io/github/commits-since/jollygoodjacob/OpenRES/v1.0.0)](https://github.com/jollygoodjacob/OpenRES/commits)
[![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg)](https://GitHub.com/jollygoodjacob/OpenRES/graphs/commit-activity)

## Citation

If you use this plugin in your work, please cite it as:

## General Information

**OpenRES** enables QGIS users to extract nine required physical and environmental features along river segments (typically 5–10 km) to support classification of river networks into **Functional Process Zones (FPZs)**.  

**Functional Process Zone (FPZ)** classification is a method used to divide a river network into river valley scale (5-10 km) segments (or "zones") that share similar physical, hydrological, and geomorphic characteristics. Rather than treating a river as a continuous longitudinal gradient of changing physical conditions, FPZ classification recognizes that rivers are composed of a discontinuous set of hydrogeomorphic patches, each shaped by different landscape and hydrologic processes ([Hestir 2007](https://www.researchgate.net/profile/Erin-Hestir/publication/265026989_Functional_Process_Zones_and_the_River_Continuum_Concept/links/546248c00cf2c0c6aec1ade8/Functional-Process-Zones-and-the-River-Continuum-Concept.pdf)). These zones reflect how the river behaves in a given segment, including how it flows, how it transports sediment, how it interacts with its floodplain, and what types of habitats it supports. After classifying a river network in FPZs, research questions posed by the tenets of the Riverine Ecosystem Synthesis hypothesis ([Thorp et al. 2006](https://onlinelibrary.wiley.com/doi/abs/10.1002/rra.901), [Thorp et al. 2023](https://www.frontiersin.org/journals/ecology-and-evolution/articles/10.3389/fevo.2023.1184433/full)) can be explored.

## Data Prerequisites

There are five required datasets needed prior to the extraction of hydrogeomorphic features along a user's watershed of interest using **OpenRES** in QGIS:

- **A geomorphically corrected stream network (.shp)**: This is a stream network generated using Whitebox Tools or another hydrological toolbox in QGIS from a DEM, which is then manually corrected to ensure that the stream network follows the course of the river as observed from imagery during the time period of interest. The stream network should be a MultiLineString object, the river segments should be segmented to a user-defined length (usually 5km-10km for FPZs), and it is recommended that the user smooth the final river network to reduce the likelihood of erroneous transect generation prior to use in OpenRES.
- **A line layer denoting the boundaries of the valley floor and the valleys (.shp)**: This layer is a line layer that contains the boundaries of both the valley bottom and the microsheds/isobasins that intersect with the valley bottom. The general procedure for producing this layer is described fully in [Williams et al. 2013](https://link.springer.com/article/10.1007/s10661-013-3114-6); however, the steps include 1.) delineating the valley bottom using a flooding algorithm (MRVBF, FLDPLN) or slope thresholding algorithm (VBET-2, Sechu et al. 2021), 2.) manual interpretation and edits to the valley bottom output to fix holes and ensure that the valley bottoms conform to expectations, 3.) generation of 1 km2 - 2 km2 "microsheds" or "isobasins" across your DEM, and 4.) various vector opertations (intersection, difference, polygon to line) to obtain a line layer that contains both the valley floor boundaries and the boundaries of intersecting microsheds that overlap with the valley floor boundaries. Thus, this layer approximates the boundaries of the valley floor and the tops of the valley that confines the river network.
- **A mean annual precipitation layer (.geotiff)**: This is a rasterized mean annual precipitation layer. Examples include but are not limited to the PRISM dataset (800m) in the U.S. or WorldClim (5km) for global studies.
- **A Digital Elevation Model (DEM) (.geotiff)**: This is a digital elevation model of the watershed of interest, often obtained from remote sensing platforms. Common datasets include 30m SRTM (global) DEMs or the 10m 3DEP (U.S.) DEMs.
- **A geology layer (.shp)**: This is a geology polygon layer that contains geologic classification of surficial or underlying geology. Often, this layer is a simplified version of the source geology layer that is classified into bedrock, mixed, or alluvial classes. In the U.S., these can be obtained from USGS; internationally, most governments can provide a publically accessible vector dataset for this analysis.

## Core Functionality 

As of this version of the plugin, the core function of OpenRES is to provide the minimal number of required features necessary to delineate FPZs from river networks. The nine required features historically used to define Functional Process Zones along river segments (see [Williams et al. 2013](https://link.springer.com/article/10.1007/s10661-013-3114-6)) are:

-   **Elevation (ELE)**: Elevation value (often in meters), extracted from the center of each stream segment.
-   **Mean Annual Precipitation (PRE)**: Mean annual precipitation value (often in mm), extracted from the center of each stream segment.
-   **Geology (GEO)**: Geology field value, extracted from the center of each stream segment.
-   **Valley Floor Width (VFW)**: Width (in meters) between the first intersections of the transects for each stream segment on the left and right sides of the stream and the valley line layer. When correctly generated, the first intersection of the valley line layer should correspond with the boundaries of the valley floor.      
-   **Valley Width (VW)**: Width (in meters) between the second intersections of the transects for each stream segment on the left and right sides of the stream and the valley line layer. When correctly generated, the second intersection of the valley line layer should correspond with tops of hydrologically connected basins that intersect the valley floor, which approximates the tops of valleys. 
-   **Right Valley Slope (RVS)**: Slope (in degrees) between the first and second intersection of a transect with the valley line layer on the right side of the river, as defined from a downstream direction. This essentially is the slope between the tops of the valley and the valley bottom on the right side of the river.
-   **Left Valley Slope (LVS)**: Slope (in degrees) between the first and second intersection of a transect with the valley line layer on the left side of the river, as defined looking downstream. This essentially is the slope between the tops of the valley and the valley bottom on the left side of the river.
-   **Down Valley Slope (DVS)**: The slope (in degrees) between the starting point and endpoint of a given stream segment.
-   **Sinuosity (SIN)**: The ratio of the true stream distance and the straight line distance between the starting point and endpoint of a given stream segment.

These nine features can then be used to classify stream networks using hierarchical classification methods (see examples in Maasri et al 2021). These classes define stream segments that share similar physical, hydrological, and geomorphic characteristics. 

Future versions of **OpenRES** will likely extend the number of features to include optional features, such as the ratio of valley width to valley floor width (RAT), channel belt sinuosity (CBD), the valley confinement index (VCI), and other miscellaneous tools to aid users in producing the required datasets.

## Installation

> **Note:** OpenRES requires QGIS version \>=3.28.

**Offline installation from .zip file** :

-  Go to releases of this repository -\> select desired version -\>
download the .zip file. 

-   Open QGIS -\> Plugins -\> Manage and Install
Plugins... -\> install from ZIP tab --\> select the downloaded zip --\>
install plugin (ignore warnings, if any).

## Example usage

> **Note:** All the following processing steps should be done in a
> sequential manner. Sample data for hydrogeomorphic feature extraction
> is provided in [sample_data](/sample_data/) folder.

### OpenRES Application

The OpenRES plugin guides users through a step-by-step workflow to extract hydrogeomorphic features from river networks.

Before starting, ensure that:
- All required input layers (e.g., stream network, valley lines, DEM, geology, and precipitation data) are correctly prepared.
- The OpenRES plugin is installed and enabled in QGIS.
- The Processing Toolbox is open.

Once setup is complete, users can follow the steps below to generate transects and extract the nine key hydrogeomorphic features.

#### Step 1: Generate transects

Begin by generating cross-valley transects for each stream segment using the **"[1] Generate Transects"** tool under **Processing Toolbar > OpenRES > Data Extraction**.

-   Search for: "[1] Generate Transects".
-   Double-click to open the tool.
-   Fill out the input fields:
-   Select the river network layer.
-   Select the valley lines layer.
-   Optionally adjust Extension Increment and Max Length.
-   Choose where to save the Transects and Center Points outputs.

> **Note:** After transect generation, users should validate that each
> transect intersects valley bottoms and valleys properly. Due to
> geometry issues between the valley lines layer and the transects, it is possible that unexpected intersections can
> occur.

#### Step 2: Extract ELE, PRE, and GEO

#### Step 3: Extract VFW and VW

#### Step 4: Extract LVS and RVS

#### Step 5: Extract SIN and DVS

### After OpenRES: Hierarchical Classification into FPZs

## Description of Functions

Description and the details of all the core functions of this plugin are available here: [Description of Functions](help/Functions_description.md)

## Contributions
1) Contribute to the software: [Contribution guidelines for this project](help/CONTRIBUTING.md)

2) Report issues or problems with the software here: <https://github.com/jollygoodjacob/OpenRES/issues>

3) For questions about the OpenRES plugin, contact: <jnesslage@ucmerced.edu>

## References


