# Open Riverine Ecosystem Synthesis (OpenRES): 
## A QGIS plugin for automated extraction of hydrogeomorphic features to support functional process zone classification of river networks

### A Python based [QGIS](https://qgis.org/en/site/index.html) plugin 
[![status]()]()
[![Documentation Status]()]()
[![License: GPL 2.0](https://img.shields.io/badge/License-GPL_2.0-green.svg)](https://opensource.org/licenses/gpl-license)
[![Open Source Love svg1](https://badges.frapsoft.com/os/v1/open-source.svg?v=103)](https://github.com/ellerbrock/open-source-badges/)
[![DOI]()]()
[![made-with-python](https://img.shields.io/badge/Made%20with-Python-ffd040.svg)](https://www.python.org/)
[![GitHub release]()]()
[![GitHub commits](https://img.shields.io/github/commits-since/jollygoodjacob/OpenRES)](https://GitHub.com/jollygoodjacob/OpenRES/commit/)
[![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg)](https://GitHub.com/jollygoodjacob/OpenRES/graphs/commit-activity)

## Citation
If you use this plugin in your work, please cite it as:

## General Information
-------------------
This plugin enables extraction of nine key hydrogeomorphic features along user-defined segments of river networks for the purpose of functional process zone classification. 

There are five required datasets needed for hydrogeomorphic extraction of features along a user's watershed of interest:

1. A geomorphically corrected stream network (.shp)  
2. A line layer denoting the boundaries of the valley floor and the valleys (.shp)  
3. A mean annual precipitation layer (.geotiff)  
4. A Digital Elevation Model (DEM) (.geotiff)  
5. A geology layer (.shp) 

## Installation
> **__Note:__** OpenRES requires QGIS version >=3.28.

**Official QGIS Plugin Installation** :

Open QGIS -> Plugins -> Manage and Install Plugins... -> select All tab -> search for OpenRES --> select and install plugin

**Alternative way (offline installation)** :

Go to releases of this repository -> select desired version -> download the .zip file.
Open QGIS -> Plugins -> Manage and Install Plugins... -> install from ZIP tab --> select the downloaded zip --> install plugin (ignore warnings, if any).

## Functionality:
-----------------------------


## Example usage
> **__Note:__** All the following processing steps should be done in a sequential manner. Sample data for hydrogeomorphic feature extraction is provided in [sample_data](/sample_data/) folder.

### Data preparation steps

#### Step 0: Identify watershed of interest and acquire watershed boundary layers

#### Step 1: Acquire, mosaic, and clip elevation layer to watershed of interest
We will also need to obtain a Digital Elevation Model over our watershed of interest.

- In the U.S., this data can be obtained from the 3DEP program at 3m, 10m, and 30m resolution, depending on your region.
- Global datasets are often 30m and include NASA's SRTM mission and the Copernicus

You will want to acquire the data over your watershed of interest. If you have multiple raster files, these will need to be mosaicked create a single raster. Then you will want to clip the data to
the watershed of interest.

#### Step 2: Acquire, mosaic, and clip precipitation layer to watershed of interest

- In the U.S., this data can be obtained from PRISM (800m).
- In South Africa, 
- Global datasets include WorldClim (4km), TerraClimate (4km)
- 
#### Step 3: Acquire, clip, and simplify geology layer for watershed of interest

#### Step 4: Create a geomorphically corrected stream network

#### Step 5: Create a line layer denoting the boundaries of the valley floor and the valleys

### OpenRES application

#### Step 6: Generate transects

> **__Note:__** After transect generation, users should validate that each transect intersects valley bottoms and valleys properly. Due to geometry issues, it is possible that unexpected intersections can occur.

#### Step 7: Extract ELE, PRE, and GEO

#### Step 8: Extract VFW and VW

#### Step 9: Extract LVS and RVS

#### Step 10: Extract SIN and DVS

### After OpenRES: Hierarchical Classification into FPZs

