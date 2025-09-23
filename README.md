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

`OpenRES` enables QGIS users to extract nine required physical and environmental features along river segments (typically 5–10 km) to support Functional Process Zone (FPZ) classification. FPZ classification groups parts of a river that share similar physical and hydrological characteristics. This helps scientists and managers better understand river behavior, plan restoration efforts, and support ecological assessments.

These nine features are:

  **1.  Elevation (ELE)**: Elevation value (often in meters), extracted from the center of each stream segment.    
  
  **2.  Mean Annual Precipitation (PRE)**: Mean annual precipitation value (often in mm), extracted from the center of each stream segment.    
  
  **3.  Geology (GEO)**: Geology field value, extracted from the center of each stream segment.      
  
  **4.  Valley Floor Width (VFW)**: Width (in meters) between the first intersections of the transects for each stream segment on the left and right sides of the stream and the valley line layer. When correctly generated, the first intersection of the valley line layer should correspond with the boundaries of the valley floor.      
  
  **5.  Valley Width (VW)**: Width (in meters) between the second intersections of the transects for each stream segment on the left and right sides of the stream and the valley line layer. When correctly generated, the second intersection of the valley line layer should correspond with tops of hydrologically connected basins that intersect the valley floor, which approximates the tops of valleys. 
  
  **6.  Right Valley Slope (RVS)**: Slope (in degrees) between the first and second intersection of a transect with the valley line layer on the right side of the river, as defined from a downstream direction. This essentially is the slope between the tops of the valley and the valley bottom on the right side of the river.
  
  **7.  Left Valley Slope (LVS)**: Slope (in degrees) between the first and second intersection of a transect with the valley line layer on the left side of the river, as defined looking downstream. This essentially is the slope between the tops of the valley and the valley bottom on the left side of the river. 
  
  **8.  Down Valley Slope (DVS)**: The slope (in degrees) between the starting point and endpoint of a given stream segment.
  
  **9.  Sinuosity (SIN)**: The ratio of the true stream distance and the straight line distance between the starting point and endpoint of a given stream segment.

## Data Prerequisites

To extract these features using `OpenRES` in QGIS, there are five required datasets needed prior to the extraction of
hydrogeomorphic features along a user's watershed of interest:

**1.  A geomorphically corrected stream network (.shp)**: This is a stream network generated using Whitebox Tools or another hydrological toolbox in QGIS from a DEM, which is then manually corrected to ensure that the stream network follows the course of the river as observed from imagery during the time period of interest.    

**2.  A line layer denoting the boundaries of the valley floor and the valleys (.shp)**: This layer is a line layer that contains the boundaries of both the valley bottom and the microsheds/isobasins that intersect with the valley bottom. The general procedure for producing this layer is described in Williams et al. 2013; however, the general steps include delineating the valley bottom using a flooding algorithm (MRVBF, FLDPLN) or slope thresholding algorithm (VBET-2,, manual interpretation and edits to the valley bottom output to fix holes and ensure that the valley bottoms conform to expectations, generation of 1 km2 - 2 km2 "microsheds" or "isobasins" across your DEM, and vector opertations (intersection, differemce, polygon to line) to obtain a line layer that 

**3.  A mean annual precipitation layer (.geotiff)**

**4.  A Digital Elevation Model (DEM) (.geotiff)**

**5.  A geology layer (.shp)**

`OpenRES`  

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

## Functions Description

Description and the details of all the core functions of this plugin are available here: [Description of Functions](help/Functions_description.md)

## Contributions
1) Contribute to the software: [Contribution guidelines for this project](help/CONTRIBUTING.md)

2) Report issues or problems with the software here: <https://github.com/jollygoodjacob/OpenRES/issues>

3) Feel free to contact us: <jnesslage@ucmerced.edu> 
