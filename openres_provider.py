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

from pathlib import Path
from qgis.core import QgsProcessingProvider,QgsMessageLog,Qgis
import os
from qgis.PyQt.QtGui import QIcon

# Icon utility (to give OpenRES an icon)
from .icon_utils import openres_icon

# Feature Extraction Tools
from .algorithms.generate_transects_algorithm import GenerateTransectsAlgorithm
from .algorithms.extract_vw_algorithm import ExtractVWAlgorithm
from .algorithms.extract_point_data_algorithm import ExtractPointDataAlgorithm
from .algorithms.extract_dvs_sin_algorithm import ExtractDVSAlgorithm
from .algorithms.extract_side_slopes_algorithm import ExtractSideSlopesAlgorithm
from .algorithms.extract_cbw_algorithm import ExtractCBWAlgorithm
from .algorithms.extract_cbs_algorithm import ExtractCBSAlgorithm

# Geomorphology Tools
from .algorithms.Sechu_valley_bottom_algorithm import SechuCostDistanceAlgorithm
from .algorithms.generate_channel_belt_algorithm import GenerateChannelBeltAlgorithm
from .algorithms.generate_microsheds_algorithm import GenerateMicroshedsAlgorithm
from .algorithms.create_valley_boundary_algorithm import CreateValleyBoundary

#To use log, type OPENRES_DEBUG=1 qgis in bash, then check Log Messages Panel → OpenRES tab for messages

DEBUG = os.environ.get("OPENRES_DEBUG") == "1"
def _log(msg, level=Qgis.Info):
    if DEBUG:
        QgsMessageLog.logMessage(msg, "OpenRES", level)



class OpenRESProvider(QgsProcessingProvider):
    def __init__(self):
        super().__init__()
        self._icon = openres_icon("openres_provider.png")

    def loadAlgorithms(self):
        # Feature Extraction Tools
        self.addAlgorithm(GenerateTransectsAlgorithm())
        self.addAlgorithm(ExtractVWAlgorithm())
        self.addAlgorithm(ExtractPointDataAlgorithm())
        self.addAlgorithm(ExtractDVSAlgorithm())
        self.addAlgorithm(ExtractSideSlopesAlgorithm())
        self.addAlgorithm(ExtractCBWAlgorithm())
        self.addAlgorithm(ExtractCBSAlgorithm())
        # Geomorphology Tools
        self.addAlgorithm(SechuCostDistanceAlgorithm())
        self.addAlgorithm(GenerateChannelBeltAlgorithm())
        self.addAlgorithm(GenerateMicroshedsAlgorithm())
        self.addAlgorithm(CreateValleyBoundary())

    def id(self):
        return "openres"

    def name(self):
        return "OpenRES"

    def longName(self):
        return "Open Riverine Ecosystem Synthesis"
    
    def icon(self):
        return self._icon


