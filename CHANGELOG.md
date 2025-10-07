# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com),
and this project adheres to [Semantic Versioning](https://semver.org).

---
## [1.0.1] - 2025-10-07
### Added
- Fixed an issue with the Extract VW and VFW algorithm where CRS information was not properly attributed to the vector outputs.
- Tested plugin across various computer systems. The plugin works on Windows and Mac operating systems using versions QGIS 3.28-3.34.

### Known issues
- Running OpenRES algorithms can sometimes cause QGIS to unexpectedly crash, although the outputs are generated as expected and saved to assigned path, if the file isn't a temp file. This behavior is inconsistent between runs and further tests are needed to resolve the crash errors.
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



