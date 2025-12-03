---
title: 'Open Riverine Ecosystem Synthesis (OpenRES): A QGIS plugin for automated extraction of hydrogeomorphic features to support Functional Process Zone classification of river networks'
tags:
  - QGIS
  - river network classification
  - Riverine Ecosystem Synthesis
  - Functional Process Zones
  - hydrogeomorphology
authors:
  - name: Jacob Nesslage
    orcid: 0000-0001-9219-8365
    affiliation: 1 
    corresponding: true
  - name: Erin L. Hestir
    orcid: 0000-0002-4673-5745
    affiliation: 1

affiliations:
 - name: Department of Civil and Environmental Engineering, University of California, Merced, Merced, CA, USA
   index: 1

date: 1 Dec 2025
bibliography: paper.bib
---

# Statement of need

Functional Process Zones (FPZs) represent recurring hydrogeomorphic units within river corridors that operate at the reach-to-valley scale. Accurate classification and mapping of these zones are essential for evaluating how spatial variations in hydrogeomorphic structure influence ecological communities and ecosystem functioning within the Riverine Ecosystem Synthesis (RES) framework (@thorp_2006). However, the delineation and classification of FPZs have been constrained by the deprecation of standardized GIS tools (e.g., RESonate for ArcMap; @williams_2013) and by the absence of open-source alternatives capable of extracting the diverse hydrogeomorphic features required for FPZ classification across entire river networks. This limitation has hindered reproducibility and comparability across studies seeking to test or extend the RES framework. 

**Open Riverine Ecosystem Synthesis**, or `OpenRES`, addresses this gap by providing an open-source, modular, and GUI-accessible QGIS plugin that automates the extraction of key hydrogeomorphic features necessary for FPZ classification. By integrating reproducible methods within a widely adopted open-source GIS platform, `OpenRES` promotes standardization, accessibility, and scalability in riverine ecosystem analyses.

# Background

The Riverine Ecosystem Synthesis (RES) reconceptualizes rivers as downstream mosaics of large, discrete, and repeating hydrogeomorphic patches rather than continuous longitudinal gradients (in contrast with the River Continuum Concept; @vannote_1980). These hydrogeomorphic patches, termed Functional Process Zones, arise from interactions between catchment geomorphology, hydrology, and climate and typically span 5–10 km of river valley (@thorp_2010). FPZs describe differences in channel and valley structure, floodplain connectivity, and sediment and flow dynamics across watersheds (@hestir_2007), and have been linked to variation in ecological communities and ecosystem properties in rivers across five continents (@thorp_2023).

FPZ classification requires spatially consistent measures of climatic, geologic, and geomorphic features, yet collecting these data in the field is often impractical. Automated geospatial tools therefore play a critical role in enabling watershed scale classification. `OpenRES` was developed to meet this need by offering a unified, reproducible, and open-source workflow for extracting the hydrogeomorphic features required for FPZ delineation.

# OpenRES Audience

`OpenRES` is intended for students, instructors, researchers, and practitioners in river science, geomorphology, hydrology, and ecosystem management who use QGIS and need a standardized, open-source tool to delineate FPZs and conduct studies of riverine ecosystems. 

# OpenRES Functionality

## Data Preparation
There are six required datasets needed prior to the extraction of hydrogeomorphic features along a user's watershed of interest using OpenRES in QGIS:

- A rasterized mean annual precipitation layer

- A digital elevation model (DEM) layer

- A simplified geology polygon layer

- A geomorphically corrected stream network layer

- A valley-boundary line layer delimiting valley bottoms and confining slopes

- A channel-belt line layer defining the active or recently active channel zone

## Using OpenRES

### Geomorphology Tools

OpenRES includes optional tools to help users prepare valley and channel-belt boundaries:

-   **Generate Channel Belt** creates lateral offsets from the stream network to approximate the channel belt extent, which users should manually refine to capture the active or recently active channel zone.

-   **Valley Floor Delineation – Sechu** implements a slope-based cost accumulation method (@sechu_2021) to identify low relief valley floor areas from a DEM, serving as a starting point for defining valley boundaries.

These tools assist in constructing the line layers required for subsequent feature extraction.

### Data Extraction Tools
The core functionality of `OpenRES` is contained in seven data extraction tools, each of which is intended to be used sequentially to automate the extraction of fifteen hydrogeomorphic features.

-   **[1] Generate Transects**: Perpendicular transects are generated from each river segment centerline to the valley boundaries. The tool iteratively extends transects until two intersections with both left and right valley boundary lines are found, providing a consistent sampling framework for valley geometry.

-   **[2] Extract ELE, PRE, and GEO**: Elevation (ELE), precipitation (PRE), and geology class (GEO) are sampled directly from user-provided raster and polygon datasets for each stream segment.

-   **[3] Extract VW, VFW, and RAT**: Valley Floor Width (VFW) is measured using the first left and right transect intersections with the valley boundary. Valley Width (VW) uses the second intersections. The ratio VW:VFW (RAT) provides a measure of valley confinement.

-   **[4] Extract LVS, RVS, and MVS**: Left and Right Valley Slope (LVS, RVS) are computed using elevation differences between valley bottom and valley top intersections along each transect on each side. Mean Valley Slope (MVS) averages the two, providing an index of valley asymmetry.

-   **[5] Extract DVS and SIN**: Down-Valley Slope (DVS) is calculated from the difference in elevation and distance between each segment start and end point in the stream network. River Sinuosity (SIN) compares each segments true length to its straight line distance between start and end points.

-   **[6] Extract CBW**: Channel Belt Width (CBW) is extracted by intersecting transects with the channel belt line layer and measuring the distance between the first left and right intersections.

-   **[7] Extract LCS, RCS, and CBS**: Left and Right Channel Sinuosity (LCS, RCS) quantify within-belt planform curvature by comparing traced channel paths to straight-line distances across each half of the belt. Channel Belt Sinuosity (CBS) summarizes these values by taking their mean.

The resulting dataset contains standardized metrics that collectively describe longitudinal and lateral hydrogeomorphic variation along the river corridor.

## After OpenRES: Unsupervised Classification

The extracted attributes can be exported to Python, R, or another software for clustering analyses commonly used to delineate FPZs (e.g., hierarchical clustering; @maasri_2019; @elgueta_2019). The resulting FPZ classes can be joined back to the river network for visualization and spatial analysis within QGIS. This workflow enables reproducible, cross-watershed FPZ classification and supports testing of RES hypotheses regarding linkages among hydrogeomorphic structure, ecological composition, and ecosystem function (@thorp_2023).

# Acknowledgements
`OpenRES` was developed by members of the Earth Observation and Remote Sensing Laboratory at the University of California, Merced. The authors would like to thank Matthew Rossi, Rachel S. Meyer, E. Natasha Stavros, Madeline Slimp, and Meghan T. Hayden for their feedback, suggestions, and support during the development of OpenRES.

# References
