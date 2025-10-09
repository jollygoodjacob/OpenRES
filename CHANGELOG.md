# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com),
and this project adheres to [Semantic Versioning](https://semver.org).

---
## [1.0.1] - 2025-10-09
### Added
- CRS information for Extract VW and VFW now appends to outputs - ref: Issue #21 by @jollygoodjacob in https://github.com/jollygoodjacob/OpenRES/pull/22
- Fix for icon referencing issue, which often slows down or crashes QGIS - ref: Issue #19 by @jollygoodjacob in https://github.com/jollygoodjacob/OpenRES/pull/23

### Known Issues
The plugin works on Windows and Mac operating systems using versions QGIS 3.28-3.34. However, further testing is needed across multiple systems and with the lastest QGIS versions to ensure compatibility.

---

## [1.0.0] - 2025-09-24
### Added
- Initial public release of the OpenRES plugin
- Support for QGIS 3.28 only
- Core functionality enables automated extraction of nine features for each stream segment in a river network: 
elevation, precipitation, geology, valley width, valley floor width, left valley slope, right valley slope,
down valley slope, and sinuosity. See OpenRES/help/Functions_description.md for full description of each function.

### Known Issues
- No testing on QGIS versions > 3.28
- No testing outside of Windows operating systems



