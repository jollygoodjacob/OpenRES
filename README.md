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

**OpenRES** enables QGIS users to extract nine required physical and environmental features along river segments (typically 5–10 km) to support **Functional Process Zone (FPZ)** classification. 

**Functional Process Zone (FPZ)** classification is a method used to divide a river network into segments (or "zones") that share similar physical, hydrological, and geomorphic characteristics. Rather than treating a river as a continuum, FPZ classification recognizes that rivers are composed of a diverse set of reaches, each shaped by different landscape and hydrologic processes. These zones reflect how the river behaves in a given segment, including how it flows, how it transports sediment, how it interacts with its floodplain, and what types of habitats it supports.

The nine features historically used to define Functional Process Zones are:

  **1.  Elevation (ELE)**: Elevation value (often in meters), extracted from the center of each stream segment.    
  
  **2.  Mean Annual Precipitation (PRE)**: Mean annual precipitation value (often in mm), extracted from the center of each stream segment.    
  
  **3.  Geology (GEO)**: Geology field value, extracted from the center of each stream segment.      
  
  **4.  Valley Floor Width (VFW)**: Width (in meters) between the first intersections of the transects for each stream segment on the left and right sides of the stream and the valley line layer. When correctly generated, the first intersection of the valley line layer should correspond with the boundaries of the valley floor.      
  
  **5.  Valley Width (VW)**: Width (in meters) between the second intersections of the transects for each stream segment on the left and right sides of the stream and the valley line layer. When correctly generated, the second intersection of the valley line layer should correspond with tops of hydrologically connected basins that intersect the valley floor, which approximates the tops of valleys. 
  
  **6.  Right Valley Slope (RVS)**: Slope (in degrees) between the first and second intersection of a transect with the valley line layer on the right side of the river, as defined from a downstream direction. This essentially is the slope between the tops of the valley and the valley bottom on the right side of the river.
  
  **7.  Left Valley Slope (LVS)**: Slope (in degrees) between the first and second intersection of a transect with the valley line layer on the left side of the river, as defined looking downstream. This essentially is the slope between the tops of the valley and the valley bottom on the left side of the river. 
  
  **8.  Down Valley Slope (DVS)**: The slope (in degrees) between the starting point and endpoint of a given stream segment.
  
  **9.  Sinuosity (SIN)**: The ratio of the true stream distance and the straight line distance between the starting point and endpoint of a given stream segment.

These nine features can then be used to classify stream networks using hierarchical classification methods (see examples in Maasri et al 2021). These classes define stream segments that share similar physical, hydrological, and geomorphic characteristics. By integrating hydrology, topography, geology, and climate, FPZs can inform decisions in watershed management, restoration planning, and ecological conservation.

## Data Prerequisites

To extract these features using `OpenRES` in QGIS, there are five required datasets needed prior to the extraction of
hydrogeomorphic features along a user's watershed of interest:

**1.  A geomorphically corrected stream network (.shp)**: This is a stream network generated using Whitebox Tools or another hydrological toolbox in QGIS from a DEM, which is then manually corrected to ensure that the stream network follows the course of the river as observed from imagery during the time period of interest.    

**2.  A line layer denoting the boundaries of the valley floor and the valleys (.shp)**: This layer is a line layer that contains the boundaries of both the valley bottom and the microsheds/isobasins that intersect with the valley bottom. The general procedure for producing this layer is described in Williams et al. 2013; however, the general steps include 1.) delineating the valley bottom using a flooding algorithm (MRVBF, FLDPLN) or slope thresholding algorithm (VBET-2, Sechu et al 2021), 2.) manual interpretation and edits to the valley bottom output to fix holes and ensure that the valley bottoms conform to expectations, 3.) generation of 1 km2 - 2 km2 "microsheds" or "isobasins" across your DEM, and 4.) various vector opertations (intersection, differemce, polygon to line) to obtain a line layer that contains both the valley floor boundaries and the boundaries of intersecting microsheds that overlap with the valley floor boundaries. This layer approxiamtes the boundaries of the valley floor and the tops of the valley that confines the river network.

**3.  A mean annual precipitation layer (.geotiff)**:

**4.  A Digital Elevation Model (DEM) (.geotiff)**: This is a digital elevation model of the watershed of interest, often obtained from remote sensing platforms. Common datasets include 30m SRTM (global) DEMs or the 10m 3DEP (U.S.) DEMs.

**5.  A geology layer (.shp)**: This is a geology polygon layer that contains geologic classification of surficial or underlying geology. Often, this layer is a simplified version of the source geology layer that is classified into bedrock, mixed, or alluvial classes. In the U.S., these can be obtained from USGS; internationally, most governments can provide a publically accessible vector dataset for this analysis.


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



### OpenRES Application


#### Step 1: Generate transects
Once a user has installed OpenRES and generated all required layers, they can begin using the OpenRES application through the Processing Toolbar in QGIS.

> **Note:** After transect generation, users should validate that each
> transect intersects valley bottoms and valleys properly. Due to
> geometry issues, it is possible that unexpected intersections can
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


