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


