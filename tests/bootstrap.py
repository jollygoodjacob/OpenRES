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
"""Test setup shared by every test module. You do not run this file directly;
``run_tests.py`` (and each test module's ``setUpModule``) calls ``setup()``.

``setup()`` does four things, and is safe to call more than once:

1. Starts a headless QGIS application, unless QGIS is already running
   (i.e. the tests were launched from the QGIS Python Console).
2. Makes QGIS's built-in ``processing`` plugin importable and initialises it.
3. Imports *this repository's* copy of OpenRES as a Python package called
   ``openres_dev``. This is what lets the plugin's own relative imports
   (``from ..icon_utils import ...``) work outside QGIS's plugin loader.
4. Registers that copy as a Processing provider with the id ``openres_dev``,
   so tests run the code in this folder, never an installed copy of the
   plugin (which keeps the id ``openres`` and is left untouched).
"""
import importlib.util
import os
import sys
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
REPO_ROOT = TESTS_DIR.parent
PACKAGE_NAME = "openres_dev"
PROVIDER_ID = "openres_dev"

_state = {"ready": False, "started_qgis": False, "provider": None}


def alg(name):
    """Full Processing id of an OpenRES algorithm under test, e.g.
    ``alg("generate_transects") -> "openres_dev:generate_transects"``."""
    return f"{PROVIDER_ID}:{name}"


def started_qgis():
    """True if setup() had to start QGIS itself (i.e. not running inside QGIS)."""
    return _state["started_qgis"]


def setup():
    if _state["ready"]:
        return
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

    from qgis.core import QgsApplication

    # 1. QGIS application
    if QgsApplication.instance() is None:
        from qgis.testing import start_app

        start_app()
        _state["started_qgis"] = True

    # 2. Processing framework. Its folder is <QGIS data dir>/python/plugins,
    #    which standalone Python does not have on sys.path by default.
    plugins_dir = Path(QgsApplication.pkgDataPath()) / "python" / "plugins"
    for candidate in (os.environ.get("QGIS_PLUGINPATH"), str(plugins_dir)):
        if candidate and Path(candidate).is_dir() and candidate not in sys.path:
            sys.path.append(candidate)
    try:
        import processing  # noqa: F401
        from processing.core.Processing import Processing
    except ImportError as exc:  # pragma: no cover - environment problem
        raise RuntimeError(
            "Could not import QGIS's 'processing' plugin. Looked in "
            f"{plugins_dir}. Set the QGIS_PLUGINPATH environment variable to the "
            "folder that contains 'processing' (it is inside your QGIS install, "
            "under .../python/plugins) and try again."
        ) from exc
    Processing.initialize()

    # 3. This repository as an importable package
    package = _load_repo_as_package()

    # 4. Register it under its own provider id
    base = package.openres_provider.OpenRESProvider

    class DevProvider(base):
        def id(self):
            return PROVIDER_ID

        def name(self):
            return "OpenRES (development copy under test)"

    registry = QgsApplication.processingRegistry()
    if registry.providerById(PROVIDER_ID) is not None:
        registry.removeProvider(registry.providerById(PROVIDER_ID))
    provider = DevProvider()
    if not registry.addProvider(provider):
        raise RuntimeError("Could not register the OpenRES test provider")
    _state["provider"] = provider
    _state["ready"] = True


def provider():
    setup()
    return _state["provider"]


def teardown():
    """Unregister the test provider (used when running inside QGIS so repeated
    runs pick up code changes)."""
    from qgis.core import QgsApplication

    registry = QgsApplication.processingRegistry()
    if registry.providerById(PROVIDER_ID) is not None:
        registry.removeProvider(registry.providerById(PROVIDER_ID))
    _state.update(ready=False, provider=None)


def _load_repo_as_package():
    if PACKAGE_NAME in sys.modules:
        return sys.modules[PACKAGE_NAME]
    spec = importlib.util.spec_from_file_location(
        PACKAGE_NAME, REPO_ROOT / "__init__.py", submodule_search_locations=[str(REPO_ROOT)]
    )
    package = importlib.util.module_from_spec(spec)
    sys.modules[PACKAGE_NAME] = package
    spec.loader.exec_module(package)
    importlib.import_module(f"{PACKAGE_NAME}.openres_provider")
    return package


# ---- scratch files ---------------------------------------------------------
# QGIS keeps files it has opened locked on Windows until QGIS closes, so the
# tests never rely on deleting their own files. Everything goes under one
# folder in the system temp directory, e.g.
#   Windows: C:\Users\<you>\AppData\Local\Temp\openres_tests
#   macOS/Linux: /tmp/openres_tests
SCRATCH_ROOT = Path(__import__("tempfile").gettempdir()) / "openres_tests"


def scratch_dir(name):
    """A new folder for one test run's files. Folders left behind by earlier
    runs (because QGIS had them open) are cleared first where possible."""
    import shutil
    import uuid

    parent = SCRATCH_ROOT / name
    if parent.is_dir():
        for old in parent.iterdir():
            shutil.rmtree(old, ignore_errors=True)
    path = parent / uuid.uuid4().hex[:8]
    path.mkdir(parents=True, exist_ok=True)
    return path


def remove_quietly(path):
    """Delete a scratch folder if possible; leave it if QGIS still has it open."""
    import gc
    import shutil

    gc.collect()
    shutil.rmtree(path, ignore_errors=True)


def sample_data_dir():
    """The Eerste sample data, unzipped once and reused by later runs.
    It is unzipped again only if sample_data/Eerste_rivier.zip changes."""
    import zipfile

    zip_path = REPO_ROOT / "sample_data" / "Eerste_rivier.zip"
    stamp = f"{zip_path.stat().st_size}-{int(zip_path.stat().st_mtime)}"
    target = SCRATCH_ROOT / "sample_data"
    marker = target / ".extracted_from"
    if not (marker.exists() and marker.read_text() == stamp):
        target.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(zip_path) as z:
            z.extractall(target)
        marker.write_text(stamp)
    return target / "Eerste_rivier"
