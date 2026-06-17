# spikeinterface_pipeline

A spike sorting pipeline for extracellular electrophysiology, built on [SpikeInterface](https://spikeinterface.readthedocs.io/). Supports SpikeGLX, Open Ephys, and Multi-Channel Systems (MCS) data formats.

---

## Overview

Open `Pipeline_project/main_pipeline_merged_PROTOTYPE.ipynb` and set the format and file paths at the top. Run all cells. The pipeline will:

1. Load the recording and attach probe geometry
2. Preprocess (highpass filter, bad channel removal, common reference)
3. Run spike sorting
4. Compute waveforms, templates, and quality metrics
5. Filter units by quality thresholds
6. Save results to `base_folder`

---

## Requirements

```
spikeinterface[full]
numpy  matplotlib  pandas  scipy  probeinterface
h5py          # MCS .h5 files
neo           # Open Ephys
```

**Spike sorters** (install separately):

| Sorter | Format |
|---|---|
| KiloSort 4 / 2.5 | SpikeGLX, Open Ephys |
| HerdingSpikes, SpykingCircus 2, MountainSort 5 | MCS MEA |

**Optional:** `spikeinterface_gui` for the interactive viewer.

---

## Setup

Set these two things in the first cells of the notebook:

### 1. Choose your format and file paths

```python
FORMAT = 'mcs'   # 'spikeglx' | 'openephys' | 'mcs'

spikeglx_folder  = Path(r'C:\path\to\recording_g0_imec0')
openephys_folder = Path(r'C:\path\to\openephys_session')
mcs_file         = Path(r'C:\path\to\recording.h5')
```

`base_folder` (where outputs are saved) is set per-format just below the paths.

### 2. Format-specific parameters

**SpikeGLX**
```python
stream_name = 'imec0.ap'   # change to imec1.ap etc. for other probes
sorter      = 'kilosort4'
freq_min    = 400          # highpass cutoff (Hz)
cref_reference = 'global'  # common reference scope
```

**Open Ephys**
```python
stream_name = 'Signals CH'   # run si.get_neo_streams() to find yours
sorter      = 'tridesclous2'
freq_min    = 300
```

**MCS**
```python
use_raw  = False             # False = .h5 export; True = .raw binary
sorter   = 'herdingspikes'   # or 'spykingcircus2', 'mountainsort5'
freq_min = 200
cref_reference = 'local'
```

---

## Parameters to tune

### Probe geometry (MCS)
If the `.h5` file has no embedded electrode positions, the pipeline falls back to a dummy probe that spaces every channel very far apart. This means the sorter cannot use spatial information. To fix this, provide either:

```python
manual_probe_map = {'Ch0': (0, 0), 'Ch1': (200, 0), ...}   # {channel_id: (x_um, y_um)}
manual_probe_csv = Path(r'C:\path\to\probe.csv')             # CSV with columns: channel_id, x, y
```

### Artifact removal
To blank windows around known noise events (e.g. stimulation pulses, light flashes):
```python
artifact_timestamps_s = [10.5, 25.3]   # times in seconds; [] to skip
artifact_ms_before    = 2.0
artifact_ms_after     = 5.0
```

### Bad channels
Channels are detected and removed automatically. To add extra ones manually:
```python
extra_bad_channel_ids = ['CH5', 'CH12']   # add known-bad channels here
```

### Quality filtering
After sorting, units are kept only if they pass all three thresholds:

| Parameter | Default | What it means |
|---|---|---|
| `amplitude_cutoff_thresh` | `0.1` | Spike amplitudes are not cut off by the detection threshold. Lower = stricter. |
| `isi_violations_ratio_thresh` | `1.0` | Few refractory period violations. Lower = stricter. |
| `presence_ratio_thresh` | `0.9` | Unit fires throughout at least 90% of the recording. Lower if recording is short or noisy. |

---

## Output files

Everything is saved inside `base_folder/`:

```
base_folder/
├── preprocess/              # preprocessed binary (cached — re-running reloads this)
├── <sorter>_output/         # raw sorter output files
├── analyzer/                # SortingAnalyzer with all extensions (waveforms, templates, metrics)
├── quality_metrics.csv      # one row per unit: firing rate, SNR, ISI violations, etc.
├── bad_channels.csv         # channels removed during preprocessing
├── spike_times/             # one CSV per unit with spike times in seconds
│   └── unit_<id>.csv
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

**WinError 32 — file locked during sorting**
The sorter process (especially HerdingSpikes) can keep output files open even after the kernel is restarted. Open Task Manager → Details tab, find any leftover `python.exe` processes from the previous session, and end them. Then re-run the sorting cell.

**All units removed after quality filtering**
Open `quality_metrics.csv` and check the values. For short recordings (< 1 min), `presence_ratio` is often low — set `presence_ratio_thresh = 0.5` or lower. For very noisy data, loosen `amplitude_cutoff_thresh`.

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
