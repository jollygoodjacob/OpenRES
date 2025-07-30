from qgis.core import QgsApplication
from .openres_provider import OpenRESProvider

class OpenRESPlugin:
    def __init__(self):
        self.provider = None

    def initProcessing(self):
        self.provider = OpenRESProvider()
        QgsApplication.processingRegistry().addProvider(self.provider)

    def initGui(self):
        self.initProcessing()

    def unload(self):
        QgsApplication.processingRegistry().removeProvider(self.provider)
