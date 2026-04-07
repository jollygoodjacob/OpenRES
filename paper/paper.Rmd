---
title: 'Open Riverine Ecosystem Synthesis (OpenRES): A QGIS plugin for automated extraction of hydrogeomorphic features to support Functional Process Zone classification of river networks'
tags:
  - QGIS
  - river classification
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

date: 7 Apr 2026
bibliography: paper.bib
---

# Summary

Open Riverine Ecosystem Synthesis (`OpenRES`) is an open-source, modular, and GUI-accessible QGIS plugin that automates the extraction of key hydrogeomorphic features needed for Functional Process Zone (FPZ) classification of river networks. FPZs represent recurring hydrogeomorphic units within river corridors that operate at the reach-to-valley scale. Accurate classification and mapping of these zones are essential for evaluating how spatial variations in hydrogeomorphic structure influence ecological communities and ecosystem functioning within the Riverine Ecosystem Synthesis (RES) framework [@thorp_2006]. However, classification of FPZs has been constrained by the deprecation of standardized GIS tools such as RESonate [@williams_2013] built for this purpose and by the absence of open-source alternatives capable of extracting the diverse hydrogeomorphic features required for FPZ classification across river networks at scale. This limitation has hindered reproducibility and comparability across studies seeking to test or extend the RES framework. By integrating reproducible methods within a widely adopted open-source GIS platform, `OpenRES` promotes standardization, accessibility, and scalability in riverine ecosystem analyses.

# Statement of need

The Riverine Ecosystem Synthesis (RES) reconceptualizes rivers as downstream mosaics of large, discrete, and repeating hydrogeomorphic patches [@thorp_2010] rather than continuous longitudinal gradients, such as those described by the popular River Continuum Concept [@vannote_1980]. These hydrogeomorphic patches, termed Functional Process Zones, arise from interactions between catchment geomorphology, hydrology, and climate and typically span 5–10 km sections of river [@thorp_2010]. FPZs describe differences in channel and valley structure, floodplain connectivity, and sediment and flow dynamics across watersheds [@hestir_2007], and have been linked to variation in fish and macroinvertebrate communities and ecosystem properties in rivers across five continents [@thorp_2023].

FPZ classification requires spatially consistent measures of climatic, geologic, and geomorphic features across a watershed, yet collecting these data in the field using “bottom-up” approaches is often impractical. Automated geospatial tools (i.e., “top-down” approaches) therefore play a critical role in enabling watershed scale classification of river networks. `OpenRES` was developed to meet this need by offering a unified, reproducible, and open-source workflow for extracting the hydrogeomorphic features required for FPZ delineation. `OpenRES` is intended for students, instructors, researchers, and practitioners in river science, geomorphology, hydrology, and ecosystem management who use QGIS and need a standardized, open-source tool to delineate FPZs and conduct studies of riverine ecosystems.

# State of the field

Early operationalization of the RES framework was advanced through the development of the RESonate toolbox by the U.S. Environmental Protection Agency (EPA) [@flotemersch_2010], which provided a workflow for deriving hydrogeomorphic attributes used to delineate FPZs [@williams_2013]. RESonate represented an important step toward translating RES theory into reproducible spatial analysis, enabling early applications of FPZ classification in large river systems. However, the tool was not broadly accessible to many researchers due to software availability constraints and reliance on proprietary ArcGIS environments.

OpenRES builds on this foundation by providing an open-source, publicly available implementation designed for the QGIS ecosystem. At present, it is the only openly available software specifically designed to extract the hydrogeomorphic variables required for FPZ classification within a modern, maintained geospatial platform. By lowering technical barriers to applying RES concepts, OpenRES facilitates broader evaluation of the ecological hypotheses proposed by the Riverine Ecosystem Synthesis, many of which remain underexplored due in part to the historical lack of accessible computational tools..

# Software design

`OpenRES` borrows from the software design and philosophy of the ``RESonate`` toolbox described in @williams_2013, with the intent of providing users with comparable functionality for extraction and calculation of hydrogeomorphic features \autoref{fig:1}. However, OpenRES was developed specifically for the free and open-source QGIS ecosystem, relying only on core QGIS libraries and the natively available GRASS 7 geospatial processing engine. The software adopts a modular design in which individual tools are implemented as QGIS Processing algorithms, allowing users to execute components independently, integrate them into custom workflows, or adapt individual steps for alternative hydrogeomorphic feature definitions. By leveraging the QGIS Processing framework, OpenRES interoperates with other geospatial tools available within QGIS while maintaining minimal external dependencies, improving reproducibility and accessibility.

![Flow chart summarizing processing steps in functional process zone classification using OpenRES and the data inputs used and data products produced in each step.\label{fig:1}](JOSS_diagram.png)

## Data preparation

There are five required datasets and one optional dataset needed prior to the extraction of hydrogeomorphic features along a user's watershed of interest using `OpenRES` in QGIS:

-   A rasterized mean annual precipitation layer.
-   A digital elevation model (DEM) layer (usually 10m-30m resolution).
-   A simplified geologic class polygon layer (i.e., alluvial, non-alluvial, bedrock).
-   A geomorphically corrected stream network layer (edited to follow the river’s path).
-   A valley-boundary line layer defining the boundaries of the valley floor and confining slopes.
-   (Optional) A channel-belt line layer defining the active or recently active channel zone.

Here, there are two notable differences from `RESonate`. First, the stream network does not need to be “inverted” (i.e., stream direction moving from confluence to headwaters rather than the standard headwaters to confluence), which makes it much easier to use publicly available stream networks, such as the NHDPlus dataset available in the United States. Second, the valley floor polygon and microsheds polygon layers needed for `RESonate` are replaced with a single valley-boundaries line layer to reduce the risk of erroneous calculations in the valley widths and side slopes calculation. `OpenRES` provides the tools to generate this layer, which is covered in the next section.

## OpenRES functionality

`OpenRES` includes geomorphology utility tools to help users prepare the valley boundaries and channel belt layers required for subsequent feature extraction:

-   **Generate Channel Belt** creates lateral offsets from the stream network to approximate the channel belt extent, which users should manually edit to capture the active or recently active channel zone.
-   **Valley Floor Delineation – Sechu** implements a slope-based cost accumulation method [@sechu_2021] to identify low relief valley floor areas from a DEM, serving as a starting point for defining valley floor boundaries.
-   **Generate Microsheds** implements a simplified version of GRASS 7’s watershed algorithm with a threshold to generate microsheds across a user’s watershed of interest. With a threshold set for 1-3 km2, users can reliably generate microsheds that capture the valley tops of confining valleys, which are needed for the valley boundaries line layer.
-   **Create Valley Boundary** applies an optimized difference operation to the input valley floor and microsheds polygons and converts the output to a line feature that denotes the boundaries of the valley floor and tops of the confining valleys across the watershed of interest.

The core functionality of `OpenRES` is contained in seven data extraction tools, each of which is intended to be used sequentially to automate the extraction of fifteen hydrogeomorphic features.

-   **[1] Generate Transects:** Perpendicular transects are generated from each river segment centerline to the second intersection on each side of the river with the valley boundaries. The tool iteratively extends transects until two intersections with both left and right valley boundary lines are found, providing a consistent sampling framework for valley width, valley floor width, and valley side slope calculations. This step links all outputs together using a transect ID (`t_ID`), enabling easy troubleshooting and enabling the use of joins and relates in QGIS.

-   **[2] Extract ELE, PRE, and GEO:** Elevation (ELE), precipitation (PRE), and geologic class (GEO) are sampled directly from user-provided raster and vector datasets from the center of each stream segment.

-   **[3] Extract VW, VFW, and RAT:** Valley Floor Width (VFW) is measured using the first left and right transect intersections with the valley boundary, referenced from the river centerline. Valley Width (VW) uses the second intersection, which captures the tops of the confining valley. The ratio VW:VFW (RAT) provides a measure of valley confinement.

-   **[4] Extract LVS, RVS, and MVS:** Left and Right Valley Slope (LVS, RVS) are computed using elevation differences between valley floor and valley top intersections along each transect on each side. Mean Valley Slope (MVS) averages the two, providing an index of valley asymmetry.

-   **[5] Extract DVS and SIN:** Down-Valley Slope (DVS) is calculated from the difference in elevation and distance between each segment start and end point in the stream network. River Sinuosity (SIN) compares each segments true length to its straight-line distance between start and end points.

-   **[6] Extract CBW:** Channel Belt Width (CBW) is extracted by intersecting transects with the channel belt line layer and measuring the distance between the left and right intersections. This step is optional but can add useful information for FPZ classification.

-   **[7] Extract LCS, RCS, and CBS:** Left and Right Channel Sinuosity (LCS, RCS) quantify within-belt planform curvature by comparing traced channel paths to straight-line distances across each half of the belt (similar to `RESonate`). Channel Belt Sinuosity (CBS) summarizes these two values by taking their mean. This step is optional but can add useful information for FPZ classification.

The resulting dataset contains standardized metrics that collectively describe longitudinal and lateral hydrogeomorphic variation along the river corridor.

## After OpenRES: unsupervised classification

The extracted attributes can be joined to the river network, then exported to Python, R, or another software for hierarchical clustering analyses commonly used to delineate FPZs [@maasri_2019; @elgueta_2019]. To assist users in this process, we developed a separate Shiny app in R, ShinyFPZ, which contains common methods for FPZ classification as well as visualization tools for OpenRES output data [@nesslage_2026]. This workflow enables reproducible, cross-watershed FPZ classification and supports testing of RES hypotheses regarding linkages among hydrogeomorphic structure, ecological composition, and ecosystem function [@thorp_2023].

# Research impact statement

`OpenRES` is the first free and open-source implementation of a complete hydrogeomorphic feature extraction workflow for FPZ classification. Unlike legacy tools such as `RESonate`, which depend on commercial GIS software, `OpenRES`:

-   operates in a modern, actively maintained FOSS GIS platform,
-   provides a modular and extensible architecture, and
-   enables complete and reproducible workflows across watersheds


By lowering technical and software barriers, `OpenRES` facilitates broader adoption of the RES framework in river science and ecosystem studies. `OpenRES` has supported growing adoption of standardized workflows for extracting hydrogeomorphic features used in FPZ classification under the RES framework. Since its release, the software has been downloaded thousands of times from the official QGIS repository and has been cloned hundreds of times from the GitHub repository. On the applications side, `OpenRES` is being utilized in environmental DNA-based watershed studies across the state of California [@stavros_2023, @nesslage_2024], as well as in South Africa's Greater Cape Floristic Region as part of NASA's Biodiversity Survey of the Cape (BioSCape) [@cardoso_2025]. These applications indicate demand for reproducible, open-source tools capable of supporting consistent FPZ analyses across river networks.

# AI usage disclosure

AI (specifically, ChatGPT 4 and 5) was used to aid in development of the `OpenRES` source code. 

AI-assisted language editing was used to improve wording in parts of the manuscript.

All code and text generated or modified by AI was proofread by the authors and AI generated
code was also tested comprehensively.

# Acknowledgements

`OpenRES` was developed by members of the Earth Observation and Remote Sensing Laboratory at the University of California, Merced. The authors would like to thank Matthew Rossi, Rachel S. Meyer, E. Natasha Stavros, Madeline Slimp, Meghan T. Hayden, Will Varela, and Martin C. Thoms for their feedback, suggestions, and support during the development of `OpenRES`.

# References
