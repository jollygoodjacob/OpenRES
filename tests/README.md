# Testing OpenRES

OpenRES ships with an automated test suite that checks the plugin's tools give correct answers. Run it after changing any algorithm, or to confirm OpenRES works with your version of QGIS.

**Everything runs from one file, `tests/run_tests.py`.** It needs only QGIS: there is nothing to install and no Python setup. The tests run the code in your copy of this repository, never the copy of OpenRES installed in QGIS.

## What the tests check

| File | What it checks |
|---|---|
| `test_provider.py` | All 11 OpenRES tools load and have help text; `metadata.txt` and `CITATION.cff` agree on the version. |
| `test_synthetic_valley.py` | Runs tools [1]–[7] on a small artificial valley whose answers can be worked out by hand (described in `synthetic.py`), and checks every one of the 15 features against them. Includes checks for open-sided valleys and a meandering reach. |
| `test_eerste_sample.py` | Runs the full README walkthrough on the bundled Eerste River sample data and checks that every output is produced and physically sensible (e.g. 0 < VFW ≤ VW, sinuosity ≥ 1, slopes ≥ 0). |

The whole suite takes under a minute.

---

## Option 1: from the QGIS Python Console (easiest, any operating system)

1. Download or clone this repository (the tests are not included in the plugin installed from the QGIS plugin manager).
2. Open QGIS and go to **Plugins → Python Console**.
3. Paste this line, replacing the path with the location of your OpenRES folder, and press Enter:

   ```python
   import runpy; _ = runpy.run_path(r"C:\Users\you\Documents\OpenRES\tests\run_tests.py", run_name="__main__")
   ```

   On macOS or Linux the path looks like `r"/Users/you/Documents/OpenRES/tests/run_tests.py"`.

(The `_ =` stops the console from printing a long list of internal variables after the results.)

QGIS may pause for about 30 seconds while the tests run. Results are printed in the console. You can edit the plugin or the tests and paste the same line again: each run uses the current files, and you do not need to restart QGIS.

> Why `runpy` and not the console's *Run script* button? `runpy` tells Python where the file lives, which the tests need in order to find the rest of the repository.

## Option 2: from a terminal

Use the Python that comes with QGIS, because an ordinary Python installation cannot `import qgis`. From inside the OpenRES folder:

- **Windows**: open the **OSGeo4W Shell** (installed with QGIS; find it in the Start menu), `cd` to the OpenRES folder, and run:
  ```
  python-qgis-ltr tests\run_tests.py
  ```
  (Use `python-qgis` instead if you installed the latest release rather than the LTR.)
- **Linux** (QGIS from your package manager):
  ```
  python3 tests/run_tests.py
  ```
- **macOS**: use the Python bundled inside the QGIS app, e.g.
  ```
  /Applications/QGIS-LTR.app/Contents/MacOS/bin/python3 tests/run_tests.py
  ```
  The app name may differ (e.g. `QGIS.app`). If this is fiddly, use Option 1.

To run a single test file, add its name: `... tests/run_tests.py test_synthetic_valley`.

The command exits with code 0 if every test passes and 1 otherwise.

## Option 3: with Docker (exactly what GitHub runs)

If you have Docker installed, run this from the OpenRES folder. It does not need QGIS installed:

```
docker run --rm -v "$PWD":/OpenRES -w /OpenRES -e QT_QPA_PLATFORM=offscreen qgis/qgis:ltr python3 tests/run_tests.py
```

Replace `ltr` with `stable` to test the newest QGIS release. In Windows PowerShell, use `${PWD}` instead of `"$PWD"`.

## Automatically on GitHub

Every push and pull request runs the suite on the QGIS LTR and latest stable releases (`.github/workflows/tests.yml`). Results appear as a check on the pull request and under the repository's **Actions** tab.

---

## Reading the output

Each test prints one line ending in `ok`, `FAIL`, `ERROR` or `skipped`, followed by a summary:

```
QGIS 3.44.15-Solothurn | Python 3.12.3
Testing OpenRES from: C:\Users\you\Documents\OpenRES

test_all_fifteen_features (test_synthetic_valley.TestSyntheticValleyWorkflow.test_all_fifteen_features) ... ok
...
Ran 14 tests in 6.2s

ALL TESTS PASSED
```

A `FAIL` means a tool gave an unexpected value, and the message shows which feature, the value produced and the value expected. An `ERROR` means a tool crashed, and the traceback shows where.

## Troubleshooting

| Message | Fix |
|---|---|
| `ModuleNotFoundError: No module named 'qgis'` | You are using an ordinary Python. Use QGIS's Python (Option 2) or the QGIS Python Console (Option 1). |
| `Could not import QGIS's 'processing' plugin` | Set the `QGIS_PLUGINPATH` environment variable to the `python/plugins` folder inside your QGIS installation (the one that contains `processing`), then run again. |
| `Run this file with runpy so Python knows where it is` | You pasted the script's contents or used *Run script*. Use the `runpy` line from Option 1. |
| `PermissionError ... being used by another process` (Windows) | QGIS locks files it has opened. The tests are written to avoid this; if you still see it, close QGIS and delete the `openres_tests` folder in your temp directory (see below). |
| `test_citation_version_matches_metadata` fails | Update `version:` in `CITATION.cff` to match `version=` in `metadata.txt`. |

## How it works (for contributors)

- `run_tests.py` adds the `tests/` folder to Python's search path, which is how the test files can `import synthetic` and `import bootstrap` from each other. It then finds every `test_*.py` file and runs it with Python's built-in `unittest`.
- `bootstrap.py` starts QGIS without a window (if it is not already running) and loads the Processing framework. It imports this repository as a package named `openres_dev`, which is what makes the plugin's internal imports (`from ..icon_utils import ...`) work outside the QGIS plugin manager. It then registers the tools under the Processing id `openres_dev`, so tests call `processing.run("openres_dev:generate_transects", ...)` (written `alg("generate_transects")` in the tests). Your installed plugin keeps the id `openres` and is not touched.
- Files the tests create (the unzipped sample data and the synthetic rasters) go in an `openres_tests` folder in your system temp directory (on Windows, `%TEMP%\openres_tests`). The sample data is unzipped once and reused. You can delete this folder at any time when QGIS is closed.
- `synthetic.py` builds the artificial valley (river, valley lines, channel belt, geology, DEM and precipitation rasters) in memory and holds the expected values in `EXPECTED`.

### Adding a test

Add a method starting with `test_` to a class in one of the `test_*.py` files, or create a new `test_<something>.py` file with the same structure:

```python
import unittest
import bootstrap
from bootstrap import alg


def setUpModule():
    bootstrap.setup()


class TestMyTool(unittest.TestCase):
    def test_something(self):
        import processing
        result = processing.run(alg("extract_cbw"), {...})
        self.assertEqual(...)
```

For a new metric, extend the synthetic valley in `synthetic.py` so the correct value can be calculated by hand, and add it to `EXPECTED`.
