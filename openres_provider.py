###############################################################################
#                                                                             #
#                     OpenRES: Open Riverine Ecosytem Synthesis               #
#                                                                             #
#      A QGIS plugin for automated extraction of hydrogeomorphic features to  #
#       support functional process zone classification of river networks      #
#                                                                             #
#                         Developed by Jacob Nesslage                         #
#                             © 2025 Jacob Nesslage                           #
#                                                                             #
#                             MIT License Notice                              #
#                                                                             #
# Permission is hereby granted, free of charge, to any person obtaining a     #
# copy of this software and associated documentation files (the "Software"),  #
# to deal in the Software without restriction, including without limitation   #
# the rights to use, copy, modify, merge, publish, distribute, sublicense,    #
# and/or sell copies of the Software, and to permit persons to whom the       #
# Software is furnished to do so, subject to the following conditions:        #
#                                                                             #
# The above copyright notice and this permission notice shall be included in  #
# all copies or substantial portions of the Software.                         #
#                                                                             #
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR  #
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,    #
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL     #
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER  #
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING     #
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER         #
# DEALINGS IN THE SOFTWARE.                                                   #
#                                                                             #
###############################################################################


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


