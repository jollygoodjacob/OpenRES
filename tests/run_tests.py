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
"""Run the OpenRES test suite. This is the only file you need to run.

From the QGIS Python Console (Plugins > Python Console), paste one line,
replacing the path with where your OpenRES folder is:

    import runpy; _ = runpy.run_path(r"C:\\path\\to\\OpenRES\\tests\\run_tests.py", run_name="__main__")

From a terminal, using the Python that comes with QGIS (see tests/README.md):

    python tests/run_tests.py                         # all tests
    python tests/run_tests.py test_synthetic_valley   # one test file

Uses only the Python standard library and QGIS; nothing to install.
"""
import sys
import unittest
from pathlib import Path


def _tests_dir():
    try:
        return Path(__file__).resolve().parent
    except NameError:  # pasted/exec'd without a file name
        raise RuntimeError(
            "Run this file with runpy so Python knows where it is, e.g.\n"
            '  import runpy; _ = runpy.run_path(r"C:\\path\\to\\OpenRES\\tests\\run_tests.py", '
            'run_name="__main__")'
        ) from None


def _forget_cached_modules(tests_dir):
    """Inside QGIS the Python session persists between runs; drop modules from
    earlier runs so edits to the plugin or tests are picked up."""
    for name, module in list(sys.modules.items()):
        path = getattr(module, "__file__", None) or ""
        if name == "openres_dev" or name.startswith("openres_dev."):
            del sys.modules[name]
        elif path and Path(path).resolve().parent == tests_dir:
            del sys.modules[name]


def main(names=()):
    tests_dir = _tests_dir()
    _forget_cached_modules(tests_dir)
    if str(tests_dir) not in sys.path:
        sys.path.insert(0, str(tests_dir))  # lets test files import each other

    import bootstrap

    bootstrap.setup()
    from qgis.core import Qgis

    print(f"QGIS {Qgis.version()} | Python {sys.version.split()[0]}")
    print(f"Testing OpenRES from: {bootstrap.REPO_ROOT}\n")

    loader = unittest.defaultTestLoader
    if names:
        suite = loader.loadTestsFromNames([n.removesuffix(".py") for n in names])
    else:
        suite = loader.discover(str(tests_dir), pattern="test_*.py", top_level_dir=str(tests_dir))

    result = unittest.TextTestRunner(stream=sys.stdout, verbosity=2).run(suite)
    if not bootstrap.started_qgis():
        bootstrap.teardown()  # leave a running QGIS as we found it
    if not result.wasSuccessful():
        print("\nSOME TESTS FAILED (see above)")
    elif result.skipped:
        print(f"\nNo failures, but {len(result.skipped)} test(s) were SKIPPED (see above)")
    else:
        print("\nALL TESTS PASSED")
    return result


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("-")] if Path(sys.argv[0]).name == "run_tests.py" else []
    outcome = main(args)
    import bootstrap

    if bootstrap.started_qgis():  # running from a terminal, not inside QGIS
        sys.exit(0 if outcome.wasSuccessful() else 1)
