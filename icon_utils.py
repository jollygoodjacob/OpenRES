from pathlib import Path
from qgis.PyQt.QtGui import QIcon

def openres_icon(filename: str) -> QIcon:
    """
    Load an OpenRES icon by filename.
    1) Try disk: <plugin_root>/icons/<filename>
    2) Fallback qrc: :/openres/icons/<filename>
    """
    plugin_root = Path(__file__).resolve().parent  # .../OpenRES
    disk_path = plugin_root / "icons" / filename
    if disk_path.exists():
        icon = QIcon(str(disk_path))
        if not icon.isNull():
            return icon

    # fallback to Qt resources
    try:
        from . import resources_rc  # registers :/openres/...
        qrc_path = f":/openres/icons/{filename}"
        icon = QIcon(qrc_path)
        if not icon.isNull():
            return icon
    except Exception:
        pass

    return QIcon()
