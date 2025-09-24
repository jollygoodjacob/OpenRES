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


from qgis.core import QgsProcessingProvider
from .algorithms.generate_transects_algorithm import GenerateTransectsAlgorithm
from .algorithms.extract_vw_algorithm import ExtractVWAlgorithm
from .algorithms.extract_point_data_algorithm import ExtractPointDataAlgorithm
from .algorithms.extract_dvs_sin_algorithm import ExtractDVSAlgorithm
from .algorithms.extract_side_slopes_algorithm import ExtractSideSlopesAlgorithm
import os
from qgis.PyQt.QtGui import QIcon
class OpenRESProvider(QgsProcessingProvider):
    def loadAlgorithms(self):
        self.addAlgorithm(GenerateTransectsAlgorithm())
        self.addAlgorithm(ExtractVWAlgorithm())
        self.addAlgorithm(ExtractPointDataAlgorithm())
        self.addAlgorithm(ExtractDVSAlgorithm())
        self.addAlgorithm(ExtractSideSlopesAlgorithm())

    def id(self):
        return "openres"

    def name(self):
        return "OpenRES"

    def longName(self):
        return "Open Riverine Ecosystem Synthesis"
    
    def icon(self):
        plugin_dir = os.path.dirname(os.path.dirname(__file__))  # Go up to plugin root
        icon_path = os.path.join(plugin_dir,'OpenRES', 'icons', 'openres_provider.png')
        print(f"[OpenRES] ✅ Looking for icon at: {icon_path}")
        if not os.path.exists(icon_path):
            print("[OpenRES] ❌ Icon file not found!")
        return QIcon(icon_path)


