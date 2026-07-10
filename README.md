# Spikeinterface pipeline

**A spike sorting pipeline for extracellular electrophysiology, built on [SpikeInterface](https://spikeinterface.readthedocs.io/).** One notebook for SpikeGLX, Open Ephys, and Multi-Channel Systems (MCS) recordings.

---

## Quick start

1. Open `Pipeline_project/main_pipeline_merged_PROTOTYPE.ipynb`
<<<<<<< HEAD
2. **Set format and paths** — in the first cell, set `FORMAT` and point the matching path variable at your data
3. **Check parameters** — in the second cell, review the sorter and filter settings, set `manual_probe_file` if your recording has no embedded geometry, and start with `test_duration_s = 3` for a quick test (use `None` for the full recording)
4. **Kernel → Restart & Run All**
=======
2. In the **PATHS** cell, set `FORMAT` and point the matching path variable to your data
3. In the **FORMAT-SPECIFIC PARAMETERS** cell, check the sorter and frequency settings, and set `manual_probe_file` if your recording has no embedded probe geometry
4. Set a `test_duration_s` to clip the first part of the recording (in seconds) or set to `None` to run the full recording
5. **Kernel → Restart & Run All**
6. Find all outputs in `base_folder/` (set in the PATHS cell)
>>>>>>> 4acf2cfabba2483cd666fcafb71834e1ae68a9ed

> Only the first two cells need editing. Everything else runs automatically, and all outputs land in `base_folder/`.

---

## Requirements

```
spikeinterface[full]
numpy  matplotlib  pandas  scipy  probeinterface
h5py          # MCS .h5 files
neo           # Open Ephys
```

**Spike sorters** (install separately): KiloSort 4, MountainSort 5, Tridesclous 2, SpykingCircus 2, HerdingSpikes.
**Optional:** `spikeinterface_gui` for the interactive unit viewer.

---

<<<<<<< HEAD
## Configure
=======
## Which cells to edit?
>>>>>>> 4acf2cfabba2483cd666fcafb71834e1ae68a9ed

Both editable cells are at the top of the notebook.

<<<<<<< HEAD
### Format and paths
=======
---

## Step 1: Set format and paths
>>>>>>> 4acf2cfabba2483cd666fcafb71834e1ae68a9ed

```python
FORMAT = 'mcs'   # 'spikeglx' | 'openephys' | 'mcs'

spikeglx_folder  = Path(r'C:\path\to\recording_g0_imec0')
openephys_folder = Path(r'C:\path\to\openephys_session')
mcs_file         = Path(r'C:\path\to\recording.h5')
```

<<<<<<< HEAD
`base_folder` (where outputs are saved) is set per format just below the paths.
=======
`base_folder` (where all outputs are saved) is set per-format just below the paths.

---

## Step 2: Check parameters

### Test clipping

```python
test_duration_s = 120    # i.e. clips to 120 s for a quick test, set to None to run the full recording (default)
```
>>>>>>> 4acf2cfabba2483cd666fcafb71834e1ae68a9ed

### Format-specific settings

| Format | `sorter` | `freq_min` | Notes |
|---|---|---|---|
| SpikeGLX | `kilosort4` | 400 | `stream_name = 'imec0.ap'` — geometry read from the file automatically |
| Open Ephys | `tridesclous2` | 300 | set `stream_name` to your recording node |
| MCS | `mountainsort5` | 200 | `use_raw = False` for `.h5`, `True` for `.raw` |

To list Open Ephys streams: `si.get_neo_streams('openephysbinary', openephys_folder)`.

### Probe geometry

<<<<<<< HEAD
SpikeGLX files carry their geometry and it is used automatically. MCS and Open Ephys recordings often do not — set `manual_probe_file` to provide it:
=======
Neuropixels recordings contain embedded probe geometry and the pipeline uses it automatically. MCS and Open Ephys recordings often do not, in that case the PROBE SETUP cell prints:

```
[probe] Dummy probe (fallback): N channels spaced 1000 um apart.
```

This means the sorter cannot use spatial information between channels. To provide the real geometry, set `manual_probe_file`:
>>>>>>> 4acf2cfabba2483cd666fcafb71834e1ae68a9ed

```python
manual_probe_file = r'C:\path\to\my_probe.npy'
```

| Format | Notes |
|---|---|
| `.json` | Native probeinterface — full probe info and wiring included |
| `.prb` | Legacy klusta / spyking-circus format — wiring included |
| `.csv` | Two-column (x, y) positions in µm, rows ordered to match the channels |
| `.npy` | `(n_channels, 2)` array of (x, y) positions in µm, same row order |

If no file is given and none is embedded, the pipeline builds a **dummy probe** so the sorter can still run. Choose its layout with `dummy_probe_type` (`'linear'`, `'tetrode'`, or `'grid'`); channels are then treated with no meaningful spatial relationship. The PROBE SETUP cell prints the channel → position mapping so you can check it before sorting.

To label channels by electrode name instead of hardware ID, set `channel_label_csv` (columns: `channel_index, electrode_label`).

### Quality filtering

Units are kept only if they pass every threshold:

| Parameter | Default | Meaning |
|---|---|---|
| `amplitude_cutoff_thresh` | `0.1` | Amplitudes not clipped by the detection threshold. Lower = stricter. |
| `isi_violations_ratio_thresh` | `1.0` | Few refractory-period violations. Lower = stricter. |
| `presence_ratio_thresh` | `0.6` | Unit fires throughout the recording. Lower for short/noisy data. |

<<<<<<< HEAD
For short recordings, `amplitude_cutoff` and `presence_ratio` may be NaN — those checks are skipped automatically.

=======
>>>>>>> 4acf2cfabba2483cd666fcafb71834e1ae68a9ed
---

## Outputs

Everything is written inside `base_folder/`:

```
preprocess/            # cached preprocessed binary (reused on re-runs)
<sorter>_output/       # raw sorter output
analyzer/              # SortingAnalyzer: waveforms, templates, metrics
quality_metrics.csv    # one row per unit
bad_channels.csv       # channels removed during preprocessing
pipeline_run_log.json  # parameters used and unit counts
```

Delete `preprocess/` to force reprocessing from scratch. To reopen a saved result in the viewer:

```python
import spikeinterface.full as si, spikeinterface_gui
analyzer = si.load_sorting_analyzer(r'C:\path\to\base_folder\analyzer')
spikeinterface_gui.run_mainwindow(analyzer)
```

---

## Troubleshooting

<<<<<<< HEAD
**All units removed after filtering** — open `quality_metrics.csv` and loosen the thresholds (e.g. `amplitude_cutoff_thresh = 0.2`, `isi_violations_ratio_thresh = 2.0`).

**Sorter not found** — check `si.get_installed_sorters()`.
=======
**All units removed after quality filtering**
Open `quality_metrics.csv` and inspect the values. Common causes:
- Short recording (< 1 min): `presence_ratio` is NaN — skipped automatically, not the issue
- Very noisy data: try loosening `amplitude_cutoff_thresh` (e.g. `0.2`) or `isi_violations_ratio_thresh` (e.g. `2.0`)
>>>>>>> 4acf2cfabba2483cd666fcafb71834e1ae68a9ed

**Dummy probe used** — the PROBE SETUP cell reports a dummy probe when no geometry was found. Set `manual_probe_file` and re-run from the LOAD cell.

**WinError 32 (file locked)** — a sorter process from a previous run is still holding the output files. End leftover `python.exe` processes in Task Manager, then re-run the sorting cell.
