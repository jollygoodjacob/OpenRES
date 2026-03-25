# OpenRES: Open Riverine Ecosystem Synthesis
# Copyright (C) 2025  Jacob Nesslage
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

from qgis.PyQt.QtCore import QCoreApplication, QVariant
from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingParameterRasterLayer,
    QgsProcessingParameterNumber,
    QgsProcessingParameterRasterDestination,
    QgsProcessingParameterVectorDestination,
    QgsProcessingException,
    QgsField
)
import processing
from ..icon_utils import openres_icon

class GenerateMicroshedsAlgorithm(QgsProcessingAlgorithm):
    DEM = "DEM"
    THRESHOLD = "THRESHOLD"
    MEMORY = "MEMORY"
    BASINS = "BASINS"
    BASINS_POLY = "BASINS_POLY"

    def tr(self, string):
        return QCoreApplication.translate("Processing", string)

    def createInstance(self):
        return GenerateMicroshedsAlgorithm()

    def name(self):
        return "GenerateMicroshedsAlgorithm"

    def displayName(self):
        return self.tr("Generate Microsheds")

    def group(self):
        return self.tr("Geomorphology")

    def groupId(self):
        return "geomorphology"

    def icon(self):
        return openres_icon("openres_provider.png")

    def shortHelpString(self):
        return self.tr(
            "Runs GRASS r.watershed and outputs only uniquely labeled watershed basins at the specified threshold, "
            "similar to WhiteboxTools Isobasins. Threshold is the minimum exterior basin size in cells (recommendation: should equal 2-3 sqkm."
        )

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterRasterLayer(
                self.DEM,
                self.tr("Input DEM")
            )
        )

        self.addParameter(
            QgsProcessingParameterNumber(
                self.THRESHOLD,
                self.tr("Threshold (minimum exterior basin size in cells)"),
                type=QgsProcessingParameterNumber.Integer,
                defaultValue=1000,
                minValue=1
            )
        )

        self.addParameter(
            QgsProcessingParameterNumber(
                self.MEMORY,
                self.tr("GRASS memory (MB)"),
                type=QgsProcessingParameterNumber.Integer,
                defaultValue=300,
                minValue=1
            )
        )

        self.addParameter(
            QgsProcessingParameterRasterDestination(
                self.BASINS,
                self.tr("Output basins raster")
            )
        )

        self.addParameter(
            QgsProcessingParameterVectorDestination(
                self.BASINS_POLY,
                self.tr("Microsheds"),
                type=QgsProcessing.TypeVectorPolygon,
                optional=True
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        dem = self.parameterAsRasterLayer(parameters, self.DEM, context)
        threshold = self.parameterAsInt(parameters, self.THRESHOLD, context)
        memory = self.parameterAsInt(parameters, self.MEMORY, context)
        basins_out = self.parameterAsOutputLayer(parameters, self.BASINS, context)
        basins_poly_out = self.parameterAsOutputLayer(parameters, self.BASINS_POLY, context)

        if dem is None:
            raise QgsProcessingException("Invalid DEM input.")

        feedback.pushInfo("Running GRASS r.watershed...")

        # Depending on QGIS install, provider id is usually grass7:r.watershed.
        # If needed, confirm in the Processing Toolbox tooltip or with:
        # processing.algorithmHelp('grass7:r.watershed')
        grass_result = processing.run(
            "grass7:r.watershed",
            {
                "elevation": dem,
                "threshold": threshold,
                "memory": memory,
                "basin": basins_out,

                # leave the other optional outputs empty
                "accumulation": None,
                "drainage": None,
                "stream": None,
                "half_basin": None,
                "length_slope": None,
                "slope_steepness": None,
                "tci": None,
                "spi": None,

                # common GRASS/QGIS wrapper params
                "-s": False,   # False = MFD default; set True if you want D8/SFD behavior
                "-4": False,
                "-a": False,
                "-b": False,
                "-m": False,
                "GRASS_REGION_PARAMETER": None,
                "GRASS_REGION_CELLSIZE_PARAMETER": 0,
                "GRASS_RASTER_FORMAT_OPT": "",
                "GRASS_RASTER_FORMAT_META": ""
            },
            context=context,
            feedback=feedback
        )

        results = {
            self.BASINS: grass_result["basin"]
        }

        if basins_poly_out:
            feedback.pushInfo("Polygonizing basins raster...")

            poly_result = processing.run(
                "gdal:polygonize",
                {
                    "INPUT": grass_result["basin"],
                    "BAND": 1,
                    "FIELD": "basin_id",
                    "EIGHT_CONNECTEDNESS": False,
                    "EXTRA": "",
                    "OUTPUT": basins_poly_out
                },
                context=context,
                feedback=feedback
            )

            results[self.BASINS_POLY] = poly_result["OUTPUT"]

        return results
