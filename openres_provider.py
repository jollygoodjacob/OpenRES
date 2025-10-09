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

from .algorithms.generate_transects_algorithm import GenerateTransectsAlgorithm
from .algorithms.extract_vw_algorithm import ExtractVWAlgorithm
from .algorithms.extract_point_data_algorithm import ExtractPointDataAlgorithm
from .algorithms.extract_dvs_sin_algorithm import ExtractDVSAlgorithm
from .algorithms.extract_side_slopes_algorithm import ExtractSideSlopesAlgorithm


#To use log, type OPENRES_DEBUG=1 qgis in bash, then check Log Messages Panel → OpenRES tab for messages

DEBUG = os.environ.get("OPENRES_DEBUG") == "1"
def _log(msg, level=Qgis.Info):
    if DEBUG:
        QgsMessageLog.logMessage(msg, "OpenRES", level)

class OpenRESProvider(QgsProcessingProvider):
    def __init__(self):
        super().__init__()
        self._icon = None
       
        # 1.) Try install from filesystem path
        pkg_root = Path(__file__).resolve().parent       # .../OpenRES
        disk_icon = pkg_root / "icons" / "openres_provider.png"
        _log(f"Provider looking for icon at: {disk_icon}")
        if disk_icon.exists():
            self._icon = QIcon(str(disk_icon))
            if not self._icon.isNull():
                _log("Loaded provider icon from disk.")
            else:
                _log("Disk icon found but QIcon is NULL (format issue?).", Qgis.Warning)
        else:
            _log("Disk icon NOT found. Check packaging/install.", Qgis.Warning)

        # 2.) Try install from resources_rc.py
        if self._icon.isNull():
            try:
                from . import resources_rc  # registers :/ namespace if present
                qrc_path = ":/openres/icons/openres_provider.png"
                _log(f"Trying Qt resource path: {qrc_path}")
                icon = QIcon(qrc_path)
                if not icon.isNull():
                    self._icon = icon
                    _log("Loaded provider icon from Qt resource.")
                else:
                    _log("Qt resource path resolved but icon is NULL.", Qgis.Warning)
            except Exception as e:
                _log(f"Qt resource import failed: {e}", Qgis.Warning)



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
        return self._icon


