# WizTree Analyst

Personal disk-space monitoring tool. Tracks what's growing on my drives over time
by diffing periodic [WizTree](https://diskanalyzer.com/) CSV exports.

## Structure

```
WizTreeAnalyst
|- WizTreeReports        (gitignored — created on first run)
|   |- <drive letter>
|       |- *.csv
|       |- results/*.txt
|- Scripts
|   |- compare_reports.py
|   |- wiztree_analyst_gui.py
|   |- find_python.ps1     (locates a usable Python, ignoring the Store stub)
|   |- install_python.ps1  (winget, else silent python.org installer)
|- App.bat               (double-click to launch the GUI)
|- README.md
```

`WizTreeReports/` holds your personal scan data and comparison results — it's
gitignored, not part of the repo. On a fresh clone/install there are no drive
folders yet; use the GUI's **Add drive** button (or just export a report) to
create them. This keeps the tool itself portable: clone it anywhere, add
whichever drives exist on that machine.

Reports are exported from WizTree (folder-level only, see below) into the matching
drive letter folder, named with their export timestamp.

## Requirements

Nothing needs to be installed by hand — `App.bat` sets up what's missing.

**Python 3 with Tkinter.** No third-party packages — everything used is
stdlib, so no venv/uv/pip install is needed. If Python isn't found, `App.bat`
installs it: `winget` if available, otherwise the official python.org
installer is downloaded and run silently (per-user, so no UAC prompt). Note
that `where python` can match the Microsoft Store stub in `WindowsApps`, which
isn't a real Python — detection probes by actually importing `sys` and
`tkinter`, so that stub and any Tk-less Python are correctly skipped.

**WizTree** (`wiztree64.exe` on PATH). If it's missing, clicking **Export
report** offers to install it via [Scoop](https://scoop.sh/) — installing
Scoop first if needed (to a folder you choose, so it can live off C:), plus
git for bucket access, then `scoop bucket add extras` and `scoop install
wiztree`. Scoop may pull in 7zip on its own as a dependency; that's expected.

After a fresh Python install you may need to close the window and run
`App.bat` once more, since PATH doesn't refresh in an already-open session.

## Export settings

Export **folders only** (`/exportfolders=1 /exportfiles=0`, or in the GUI dialog
untick "Export Files"). File-level export balloons to hundreds of MB and is
unnecessary — folder rollups are enough to spot what's eating space, and stay
small enough to diff quickly and open anywhere.

## GUI

Double click APP.bat to run the GUI.

- Click **Add drive** to register a new drive letter (e.g. `R` for a new SSD)
  — creates `WizTreeReports/R/results/` and adds it to the dropdown.
- Pick a drive, click **Export report** to run WizTree and drop a timestamped
  CSV into `WizTreeReports/<drive>/` (requires `wiztree64.exe` on PATH — edit
  `WIZTREE_EXE` in the script if it isn't, or use the install prompt if
  WizTree isn't installed at all).
- The list shows all CSVs for the selected drive. Double-click a report to
  drop it into a compare slot (up to 2), then click **Compare**.
- Results print in the window and save to
  `WizTreeReports/<drive>/results/compare_<old>_vs_<new>.txt`.

## CLI
#### Getting a CSV

```
wiztree64.exe "C:" /export="WizTreeReports\C\WizTree_%d_%t.csv" /admin=1 /exportfolders=1 /exportfiles=0
```

- `/admin=1` — needed for a full C: scan (still triggers a UAC prompt; scanning
  itself can't be run elevated silently without disabling UAC).
- `%d` / `%t` expand to date/time, matching the existing report file naming.
- Swap `"C:"` and the output folder for `"D:"` etc. per drive.

#### Comparing two reports

```
python Scripts/compare_reports.py WizTreeReports/C/old.csv WizTreeReports/C/new.csv
```

Prints the top 50 folders by size change, largest growth first, tagged `NEW` /
`GONE` where a folder appeared or disappeared entirely.


