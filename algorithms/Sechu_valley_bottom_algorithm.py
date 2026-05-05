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

from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingParameterVectorLayer,
    QgsProcessingParameterRasterLayer,
    QgsProcessingParameterNumber,
    QgsProcessingParameterFeatureSink,
    QgsProcessingParameterBoolean,
    QgsProcessingContext,
    QgsProcessingException,
    QgsProcessingOutputVectorLayer,
    QgsProcessingUtils,
    QgsRasterLayer,
    QgsFeatureSink,
    QgsProcessingParameterEnum
)
from qgis.PyQt.QtGui import QColor
import processing
import os
import math
import uuid
from osgeo import gdal
from ..icon_utils import openres_icon


class SechuCostDistanceAlgorithm(QgsProcessingAlgorithm):
    """
    Cost-distance-based valley floor delineation
    """

    # parameter keys
    PARAM_RIVER = 'RIVER'
    PARAM_DEM = 'DEM'
    PARAM_COST_THRESHOLD = 'COST_THRESHOLD'
    PARAM_GAP_FACTOR = 'GAP_FACTOR'
    PARAM_OUTPUT = 'OUTPUT'
    PARAM_SMOOTH_ITERATIONS = 'SMOOTH_ITERATIONS'
    PARAM_SMOOTH_OFFSET = 'SMOOTH_OFFSET'
    PARAM_SMOOTH_MAX_ANGLE = 'SMOOTH_MAX_ANGLE'

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return SechuCostDistanceAlgorithm()

    def name(self):
        return 'valley_floor_costdist'

    def displayName(self):
        return self.tr('Valley Floor Delineation - Sechu')

    def group(self):
        return self.tr('Geomorphology')

    def groupId(self):
        return 'geomorphology'

    def icon(self):
        return openres_icon("openres_provider.png")

    def shortHelpString(self):
        return self.tr(
            'Delineate a valley bottom by:\n'
            '1) building slope from DEM, \n'
            '2) using slope as cost surface in GRASS r.cost from a river network, \n'
            '3) taking an initial (max) cost threshold (usually [500 * (res / 10m)] is a good starting point), \n'
            '4) computing the mean cost inside that belt, \n'
            '5) re-thresholding with that mean, and \n'
            '6) cleaning/smoothing/filling skinny gaps.'
        )

    def initAlgorithm(self, config=None):
        # river network
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.PARAM_RIVER,
                self.tr('River network'),
                [QgsProcessing.TypeVectorLine]
            )
        )

        # DEM
        self.addParameter(
            QgsProcessingParameterRasterLayer(
                self.PARAM_DEM,
                self.tr('Elevation raster')
            )
        )

        # initial cost threshold
        self.addParameter(
            QgsProcessingParameterNumber(
                self.PARAM_COST_THRESHOLD,
                self.tr('Initial cost distance threshold'),
                QgsProcessingParameterNumber.Double,
                defaultValue=500.0
            )
        )

        # smoothing iterations 
        self.addParameter(
            QgsProcessingParameterNumber(
                self.PARAM_SMOOTH_ITERATIONS,
                self.tr('Smoothing iterations'),
                QgsProcessingParameterNumber.Integer,
                defaultValue=3,
                minValue=0
            )
        )

        # smoothing offset
        self.addParameter(
            QgsProcessingParameterNumber(
                self.PARAM_SMOOTH_OFFSET,
                self.tr('Smoothing offset'),
                QgsProcessingParameterNumber.Double,
                defaultValue=0.4,
                minValue=0.0
            )
        )

        # Max smoothing angle
        self.addParameter(
            QgsProcessingParameterNumber(
                self.PARAM_SMOOTH_MAX_ANGLE,
                self.tr('Maximum smoothing angle'),
                QgsProcessingParameterNumber.Double,
                defaultValue=180.0,
                minValue=0.0,
                maxValue=180.0
            )
        )

        # gap factor (how much to buffer in/out, in pixels of DEM)
        self.addParameter(
            QgsProcessingParameterNumber(
                self.PARAM_GAP_FACTOR,
                self.tr('Gap buffer factor (× DEM pixel size)'),
                QgsProcessingParameterNumber.Double,
                defaultValue=2.0
            )
        )

        # output
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.PARAM_OUTPUT,
                self.tr('Valley Floor'),
                QgsProcessing.TypeVectorPolygon
            )
        )

    def processAlgorithm(self, parameters, context: QgsProcessingContext, feedback):
        river_layer = self.parameterAsVectorLayer(parameters, self.PARAM_RIVER, context)
        dem_layer = self.parameterAsRasterLayer(parameters, self.PARAM_DEM, context)
        cost_threshold = self.parameterAsDouble(parameters, self.PARAM_COST_THRESHOLD, context)
        gap_factor = self.parameterAsDouble(parameters, self.PARAM_GAP_FACTOR, context)
        smooth_iterations = self.parameterAsInt(parameters, self.PARAM_SMOOTH_ITERATIONS, context)
        smooth_offset = self.parameterAsDouble(parameters, self.PARAM_SMOOTH_OFFSET, context)
        smooth_max_angle = self.parameterAsDouble(parameters, self.PARAM_SMOOTH_MAX_ANGLE, context)

        if river_layer is None or dem_layer is None:
            raise QgsProcessingException('River Network or DEM not valid')

        # temp dir
        temp_dir = QgsProcessingUtils.tempFolder()

        # temp rasters
        run_id = uuid.uuid4().hex[:8]

        slope_raster = os.path.join(temp_dir, f'cb_{run_id}_slope.tif')
        cond_slope_raster = os.path.join(temp_dir, f'cb_{run_id}_slope_cond.tif')
        river_raster = os.path.join(temp_dir, f'cb_{run_id}_river.tif')
        accum_cost_raster = os.path.join(temp_dir, f'cb_{run_id}_costdist.tif')
        belt_mask_raster = os.path.join(temp_dir, f'cb_{run_id}_mask_coarse.tif')
        refined_mask_raster = os.path.join(temp_dir, f'cb_{run_id}_mask_refined.tif')
        refined_poly = os.path.join(temp_dir, f'cb_{run_id}_refined_poly.gpkg')

        # DEM info
        dem_path = dem_layer.source()
        extent = dem_layer.extent()
        xmin, xmax = extent.xMinimum(), extent.xMaximum()
        ymin, ymax = extent.yMinimum(), extent.yMaximum()
        dem_xres = dem_layer.rasterUnitsPerPixelX()
        dem_yres = dem_layer.rasterUnitsPerPixelY()
        crs_auth = dem_layer.crs().authid()

        width_px = int(math.ceil((xmax - xmin) / dem_xres))
        height_px = int(math.ceil((ymax - ymin) / dem_yres))

        # 1. Slope
        feedback.pushInfo('Computing slope...')
        processing.run(
            "gdal:slope",
            {
                'INPUT': dem_path,
                'BAND': 1,
                'SCALE': 1.0,
                'AS_PERCENT': False,
                'COMPUTE_EDGES': True,
                'ZEVENBERGEN': False,
                'OPTIONS': '',
                'OUTPUT': slope_raster
            },
            context=context,
            feedback=feedback
        )

        # 2. Condition slope
        feedback.pushInfo('Conditioning slope...')
        processing.run(
            "qgis:rastercalculator",
            {
                'EXPRESSION': f'("{slope_raster}@1" * {dem_xres}) + 0.00001',
                'LAYERS': [slope_raster],
                'CELL_SIZE': dem_xres,
                'EXTENT': f"{xmin},{xmax},{ymin},{ymax}",
                'CRS': crs_auth,
                'OUTPUT': cond_slope_raster
            },
            context=context,
            feedback=feedback
        )

        # 3. Rasterize river (note: we keep your original UNITS setup here)
        feedback.pushInfo('Rasterizing river...')
        processing.run(
            "gdal:rasterize",
            {
                'INPUT': river_layer,
                'FIELD': None,
                'BURN': 1,
                'USE_Z': False,
                'UNITS': 0,
                'WIDTH': width_px,
                'HEIGHT': height_px,
                'EXTENT': f"{xmin},{xmax},{ymin},{ymax}",
                'NODATA': 0,
                'DATA_TYPE': 5,
                'INIT': 0,
                'INVERT': False,
                'OUTPUT': river_raster
            },
            context=context,
            feedback=feedback
        )

        # 4. GRASS r.cost
        feedback.pushInfo('Running GRASS r.cost...')
        processing.run(
            "grass7:r.cost",
            {
                'input': cond_slope_raster,
                'start_points': None,
                'start_raster': river_raster,
                'max_cost': 0,
                'memory': 300,
                'output': accum_cost_raster,
                'outdir': 'TEMPORARY_OUTPUT',
                'GRASS_REGION_PARAMETER': f"{xmin},{xmax},{ymin},{ymax}",
                'GRASS_REGION_CELLSIZE_PARAMETER': dem_xres,
                'GRASS_RASTER_FORMAT_OPT': '',
                'GRASS_RASTER_FORMAT_META': ''
            },
            context=context,
            feedback=feedback
        )

        # 5. coarse mask
        feedback.pushInfo('Creating coarse mask...')
        processing.run(
            "qgis:rastercalculator",
            {
                'EXPRESSION': f'if(("{accum_cost_raster}@1" > 0) AND ("{accum_cost_raster}@1" <= {cost_threshold}), 1, 0)',
                'LAYERS': [accum_cost_raster],
                'CELL_SIZE': dem_xres,
                'EXTENT': f"{xmin},{xmax},{ymin},{ymax}",
                'CRS': crs_auth,
                'OUTPUT': belt_mask_raster
            },
            context=context,
            feedback=feedback
        )

        # 5a. compute mean in Python
        feedback.pushInfo('Computing mean inside coarse mask...')
        cost_ds = gdal.Open(accum_cost_raster)
        mask_ds = gdal.Open(belt_mask_raster)
        if cost_ds is None or mask_ds is None:
            raise QgsProcessingException("Could not open cost or mask raster for reading.")
        cost_band = cost_ds.GetRasterBand(1)
        mask_band = mask_ds.GetRasterBand(1)
        cols = cost_ds.RasterXSize
        rows = cost_ds.RasterYSize

        total = 0.0
        count = 0
        for y in range(rows):
            if feedback.isCanceled():
                break
            cost_arr = cost_band.ReadAsArray(0, y, cols, 1)[0]
            mask_arr = mask_band.ReadAsArray(0, y, cols, 1)[0]
            for x in range(cols):
                if mask_arr[x] == 1 and cost_arr[x] > 0:
                    total += float(cost_arr[x])
                    count += 1

        if count == 0:
            raise QgsProcessingException("Coarse mask selected 0 pixels — increase cost threshold.")

        mean_cost = total / count
        feedback.pushInfo(f"Mean cost inside coarse mask = {mean_cost}")

        # To enable deletion after processing
        cost_band = None
        mask_band = None
        cost_ds = None
        mask_ds = None

        # 5b. refined mask
        feedback.pushInfo('Creating refined mask...')
        processing.run(
            "qgis:rastercalculator",
            {
                'EXPRESSION': f'if(("{accum_cost_raster}@1" > 0) AND ("{accum_cost_raster}@1" <= {mean_cost}), 1, 0)',
                'LAYERS': [accum_cost_raster],
                'CELL_SIZE': dem_xres,
                'EXTENT': f"{xmin},{xmax},{ymin},{ymax}",
                'CRS': crs_auth,
                'OUTPUT': refined_mask_raster
            },
            context=context,
            feedback=feedback
        )

        # 6. polygonize refined mask
        feedback.pushInfo('Polygonizing refined mask...')
        
        processing.run(
            "gdal:polygonize",
            {
                'INPUT': refined_mask_raster,
                'BAND': 1,
                'FIELD': 'DN',
                'EIGHT_CONNECTEDNESS': False,
                'OUTPUT': refined_poly
            },
            context=context,
            feedback=feedback
        )

        poly_lyr = QgsRasterLayer  # just to keep IDE happier

        # 7. Extract DN = 1
        feedback.pushInfo('Extracting DN = 1...')
        extract_result = processing.run(
            "native:extractbyattribute",
            {
                'INPUT': refined_poly,
                'FIELD': 'DN',
                'OPERATOR': 0,
                'VALUE': 1,
                'OUTPUT': 'memory:'
            },
            context=context,
            feedback=feedback
        )
        extracted = extract_result['OUTPUT']

        # 8. Delete holes
        feedback.pushInfo('Deleting holes...')
        hole_free = processing.run(
            "native:deleteholes",
            {
                'INPUT': extracted,
                'MIN_AREA': 0,
                'OUTPUT': 'memory:'
            },
            context=context,
            feedback=feedback
        )['OUTPUT']

        # 9. Smooth
        feedback.pushInfo('Smoothing...')
        smoothed = processing.run(
            "native:smoothgeometry",
            {
                'INPUT': hole_free,
                'METHOD': 0,
                'ITERATIONS': smooth_iterations,
                'OFFSET': smooth_offset,
                'MAX_ANGLE': smooth_max_angle,
                'OUTPUT': 'memory:'
            },
            context=context,
            feedback=feedback
        )['OUTPUT']

        # 10. gap-closing buffer in/out
        feedback.pushInfo('Closing narrow gaps...')
        gap_dist = dem_xres * gap_factor
        buf_out = processing.run(
            "native:buffer",
            {
                'INPUT': smoothed,
                'DISTANCE': gap_dist,
                'SEGMENTS': 8,
                'END_CAP_STYLE': 0,
                'JOIN_STYLE': 0,
                'MITER_LIMIT': 2,
                'DISSOLVE': True,
                'OUTPUT': 'memory:'
            },
            context=context,
            feedback=feedback
        )['OUTPUT']

        gaps_closed = processing.run(
            "native:buffer",
            {
                'INPUT': buf_out,
                'DISTANCE': -gap_dist,
                'SEGMENTS': 8,
                'END_CAP_STYLE': 0,
                'JOIN_STYLE': 0,
                'MITER_LIMIT': 2,
                'DISSOLVE': True,
                'OUTPUT': 'memory:'
            },
            context=context,
            feedback=feedback
        )['OUTPUT']

        # write to user output
        (sink, dest_id) = self.parameterAsSink(
            parameters,
            self.PARAM_OUTPUT,
            context,
            gaps_closed.fields(),
            gaps_closed.wkbType(),
            gaps_closed.sourceCrs()
        )

        
        
        for f in gaps_closed.getFeatures():
            if feedback.isCanceled():
                break
            sink.addFeature(f, QgsFeatureSink.FastInsert)

        to_delete = [
            slope_raster,
            cond_slope_raster,
            river_raster,
            accum_cost_raster,
            belt_mask_raster,
            refined_mask_raster,
            refined_poly  # the gpkg we used before extracting

        ]

        for p in to_delete:
            try:
                if os.path.exists(p):
                    os.remove(p)
            except Exception as e:
                # don't kill the whole algorithm if one file can't be deleted
                feedback.pushInfo(f"Could not delete temp file {p}: {e}")

        layer = context.getMapLayer(dest_id)
        if layer:
            symbol = layer.renderer().symbol()
            symbol.setColor(QColor(173, 216, 230))  # light blue (RGB)
            layer.triggerRepaint()
            feedback.pushInfo("Applied light blue symbology.")

        return {
            self.PARAM_OUTPUT: dest_id
        }
