from pathlib import Path
from qgis.PyQt.QtGui import QIcon

# This file lives in OpenRES/algorithms/, so the plugin root is two levels up
PLUGIN_ROOT = Path(__file__).resolve().parent.parent
ICON_DIR = PLUGIN_ROOT / "icons"

def openres_icon(filename: str) -> QIcon:
    path = ICON_DIR / filename
    return QIcon(str(path)) if path.is_file() else QIcon()
