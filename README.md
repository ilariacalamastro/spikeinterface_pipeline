# Spikeinterface pipeline

A spike sorting pipeline for extracellular electrophysiology, built on [SpikeInterface](https://spikeinterface.readthedocs.io/). Supports SpikeGLX, Open Ephys, and Multi-Channel Systems (MCS) data formats.

---

## Quick start

1. Open `Pipeline_project/main_pipeline_merged_PROTOTYPE.ipynb`
2. In the **PATHS** cell, set `FORMAT` and point the matching path variable to your data
3. In the **FORMAT-SPECIFIC PARAMETERS** cell, check the sorter and frequency settings, and set `manual_probe_file` if your recording has no embedded probe geometry
4. Set a `test_duration_s` to clip the first part of the recording (in seconds) or set to `None` to run the full recording
5. **Kernel → Restart & Run All**
6. Find all outputs in `base_folder/` (set in the PATHS cell)

> **Only the first two cells need editing.** Everything else runs automatically.

---

## Requirements

```
spikeinterface[full]
numpy  matplotlib  pandas  scipy  probeinterface
h5py          # MCS .h5 files
neo           # Open Ephys
```

**Spike sorters** (install separately):

| Sorter | Recommended for |
|---|---|
| KiloSort 4 | SpikeGLX (Neuropixels) |
| HerdingSpikes | MCS MEA |
| SpykingCircus 2, MountainSort 5, Tridesclous 2 | MCS, Open Ephys |

**Optional:** `spikeinterface_gui` for the interactive unit viewer.

---

## Which cells to edit?

| Cell | What it does | Edit? |
|---|---|---|
| **PATHS** | Data format, file locations, output folder | **Yes — every run** |
| **FORMAT-SPECIFIC PARAMETERS** | Sorter, filter, probe map, thresholds | **Yes — check each run** |
| LOAD | Reads the recording from disk | No |
| PROBE SETUP | Attaches electrode geometry | No |
| PREPROCESSING | Highpass filter, bad channel removal, common reference | No |
| SPIKE SORTING | Runs the sorter | No |
| SORTING ANALYZER | Computes waveforms, templates, metrics | No |
| QUALITY METRICS / FILTERING | Filters units by quality | No |
| SAVE / VIEWER | Saves results, opens interactive viewer | No |

---

## Step 1: Set format and paths

```python
FORMAT = 'mcs'   # 'spikeglx' | 'openephys' | 'mcs'

spikeglx_folder  = Path(r'C:\path\to\recording_g0_imec0')
openephys_folder = Path(r'C:\path\to\openephys_session')
mcs_file         = Path(r'C:\path\to\recording.h5')
```

`base_folder` (where all outputs are saved) is set per-format just below the paths.

---

## Step 2: Check parameters

### Test clipping

```python
test_duration_s = 120    # i.e. clips to 120 s for a quick test, set to None to run the full recording (default)
```

### Format-specific settings

**SpikeGLX**
```python
stream_name    = 'imec0.ap'   # change to imec1.ap etc. for other probes
sorter         = 'kilosort4'
freq_min       = 400          # highpass cutoff (Hz)
cref_reference = 'global'
```

**Open Ephys**
```python
stream_name = 'Signals CH'   # run si.get_neo_streams() to list your streams
sorter      = 'tridesclous2'
freq_min    = 300
```

**MCS**
```python
use_raw        = False           # False = .h5 export from Multi Channel DataManager; True = .raw binary
sorter         = 'herdingspikes' # or 'spykingcircus2', 'mountainsort5'
freq_min       = 200
cref_reference = 'local'
```

### Probe geometry

Neuropixels recordings contain embedded probe geometry and the pipeline uses it automatically. MCS and Open Ephys recordings often do not, in that case the PROBE SETUP cell prints:

```
[probe] Dummy probe (fallback): N channels spaced 1000 um apart.
```

This means the sorter cannot use spatial information between channels. To provide the real geometry, set `manual_probe_file`:

```python
manual_probe_file = r'C:\path\to\my_probe.npy'   # see supported formats below
```

Supported formats:

| Format | Notes |
|---|---|
| `.json` | Native probeinterface format — full probe info and wiring included. [Docs](https://probeinterface.readthedocs.io/en/main/format_spec.html) |
| `.prb` | Legacy klusta / spyking-circus format — wiring included. [Docs](https://probeinterface.readthedocs.io/en/main/examples/ex_06_import_export_to_file.html) |
| `.csv` | Two-column (x, y) position table in µm, rows ordered to match recording channels. [Docs](https://probeinterface.readthedocs.io/en/main/examples/ex_06_import_export_to_file.html) |
| `.npy` | NumPy array of shape `(n_channels, 2)` with (x, y) positions in µm, rows ordered to match recording channels |

When the file is loaded, the PROBE SETUP cell prints the full channel → position mapping so you can verify it looks correct before sorting.

**Optional channel labelling:** if you want channels labelled by electrode name rather than hardware ID, add:
```python
channel_label_csv = r'C:\path\to\labels.csv'   # columns: channel_index, electrode_label
```
This prints `channel_id → electrode_label` for verification and renames channels throughout the pipeline.

### Quality filtering

After sorting, units are kept only if they pass all three thresholds:

| Parameter | Default | Meaning |
|---|---|---|
| `amplitude_cutoff_thresh` | `0.1` | Spike amplitudes are not cut off by the detection threshold. Lower = stricter. |
| `isi_violations_ratio_thresh` | `1.0` | Few refractory period violations. Lower = stricter. |
| `presence_ratio_thresh` | `0.6` | Unit fires throughout the recording. Lower if recording is short or noisy. |

---

## Output files

Everything is saved inside `base_folder/`:

```
base_folder/
├── preprocess/              # preprocessed binary (cached — re-running reloads this)
├── <sorter>_output/         # raw sorter output files
├── analyzer/                # SortingAnalyzer with waveforms, templates, and metrics
├── quality_metrics.csv      # one row per unit: firing rate, SNR, ISI violations, etc.
├── bad_channels.csv         # channels removed during preprocessing
└── pipeline_run_log.json    # record of parameters used and unit counts
```

To reopen the interactive viewer on a saved result:
```python
import spikeinterface.full as si, spikeinterface_gui
analyzer = si.load_sorting_analyzer(r'C:\path\to\base_folder\analyzer')
spikeinterface_gui.run_mainwindow(analyzer)
```

The `preprocess/` folder is reused automatically on re-runs to skip the preprocessing step. Delete it to force reprocessing from scratch.

---

## Troubleshooting

**All units removed after quality filtering**
Open `quality_metrics.csv` and inspect the values. Common causes:
- Short recording (< 1 min): `presence_ratio` is NaN — skipped automatically, not the issue
- Very noisy data: try loosening `amplitude_cutoff_thresh` (e.g. `0.2`) or `isi_violations_ratio_thresh` (e.g. `2.0`)

**Sorter not found**
```python
import spikeinterface as si
si.get_installed_sorters()
```

**Open Ephys stream name not found**
```python
import spikeinterface as si
si.get_neo_streams('openephys', r'C:\path\to\session')
```

**Probe not attached / dummy probe used**
The PROBE SETUP cell prints `[probe] Dummy probe (fallback)` if no geometry was found. Set `manual_probe_file` in the parameters cell and re-run from the LOAD cell downward.
