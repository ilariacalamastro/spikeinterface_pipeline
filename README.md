# spikeinterface_pipeline

A flexible spike sorting pipeline for extracellular electrophysiology recordings, built on [SpikeInterface](https://spikeinterface.readthedocs.io/). Supports SpikeGLX, Open Ephys, and Multi-Channel Systems (MCS) data formats.

---

## Table of Contents

- [Overview](#overview)
- [Requirements](#requirements)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Pipeline Structure](#pipeline-structure)
- [Format-Specific Guides](#format-specific-guides)
  - [SpikeGLX (Neuropixels)](#spikeg lx-neuropixels)
  - [Open Ephys](#open-ephys)
  - [Multi-Channel Systems (MCS)](#multi-channel-systems-mcs)
- [Configuration Reference](#configuration-reference)
- [Output Files](#output-files)
- [Troubleshooting](#troubleshooting)

---

## Overview

This pipeline takes raw neural recordings and produces spike-sorted, quality-controlled units ready for analysis. Given a recording folder, it will:

1. Load the recording and attach probe geometry
2. Preprocess (filter, remove artifacts, detect and exclude bad channels, apply common reference)
3. Run a spike sorter
4. Compute waveforms, templates, and quality metrics
5. Filter units by quality thresholds
6. Save a `SortingAnalyzer` object and a `quality_metrics.csv` summary
7. Optionally open an interactive Qt viewer

---

## Requirements

### Python Packages

```
spikeinterface[full]   # core library + all extras
numpy
matplotlib
pandas
scipy
h5py                   # MCS .h5 files only
neo                    # Open Ephys support
probeinterface
```

### Spike Sorters (install separately based on your needs)

| Sorter | Recommended for | Install |
|---|---|---|
| KiloSort 4 | SpikeGLX, Open Ephys | see [KiloSort docs](https://github.com/MouseLand/Kilosort) |
| KiloSort 2.5 | SpikeGLX, Open Ephys | see [KiloSort docs](https://github.com/MouseLand/Kilosort) |
| SpykingCircus 2 | MCS MEA (default) | `pip install spykingcircus2` |
| MountainSort 5 | MCS MEA (alternative) | `pip install mountainsort5` |
| HerdingSpikes | MCS MEA (alternative) | `pip install herdingspikes` |

### Optional

```
spikeinterface_gui     # interactive Qt viewer
huggingface_hub        # UnitRefine classifier (MCS only)
skops                  # UnitRefine classifier (MCS only)
```

### System

- Python 3.9+
- 16 GB RAM recommended (8 GB minimum)
- Multi-core CPU (parallelization is used automatically)
- GPU optional — used by KiloSort if available

---

## Installation

```bash
git clone https://github.com/<your-username>/spikeinterface_pipeline.git
cd spikeinterface_pipeline

pip install spikeinterface[full] numpy matplotlib pandas scipy h5py neo probeinterface
# Then install your sorter of choice (see table above)
```

---

## Quick Start

All pipelines are run as Jupyter notebooks. Open `Pipeline_project/main_pipeline.ipynb` and set three things at the top:

```python
FORMAT = 'spikeglx'          # 'spikeglx', 'openephys', or 'mcs'
SORTER_KS = 'kilosort4'      # for SpikeGLX / Open Ephys
SORTER_MCS = 'spykingcircus2'  # for MCS

spikeglx_folder = Path(r'C:\path\to\your\recording_g0')
base_folder = Path(r'C:\path\to\output')
```

Then run all cells. The notebook will dispatch to the correct format-specific notebook automatically.

To test the pipeline on synthetic data before using real recordings, run `make_dummy_mcs.py` to generate a dummy MCS file:

```bash
python "Pipeline_project/first tests (ignore)/make_dummy_mcs.py"
# Generates: dummy_mcs/dummy_recording.h5
```

---

## Pipeline Structure

```
Pipeline_project/
├── main_pipeline.ipynb       ← start here: set FORMAT and paths, run all
├── load_spikeglx.ipynb       ← SpikeGLX / Neuropixels pipeline
├── load_openephys.ipynb      ← Open Ephys pipeline
├── load_mcs.ipynb            ← Multi-Channel Systems pipeline
└── code test/
    ├── load_spikeglx_test.ipynb   ← standalone SpikeGLX test
    ├── load_mcs_test.ipynb        ← standalone MCS test
    └── load_openephys2.ipynb      ← Open Ephys with tetrode support
```

Each format-specific notebook is a complete, self-contained pipeline. You can also open and run them directly, without going through `main_pipeline.ipynb`.

### Processing Steps (all formats)

```
Raw Recording
    ↓
Load + Probe Geometry Attachment
    ↓
Preprocessing:
  - Highpass filter
  - Artifact blanking (optional)
  - Bad channel detection + removal
  - Common median reference
    ↓
Save Preprocessed Binary (cached for re-use)
    ↓
Spike Sorting
    ↓
SortingAnalyzer: waveforms, templates, noise,
  correlograms, locations, quality metrics
    ↓
Quality-Based Unit Filtering
    ↓
Save Analyzer + quality_metrics.csv
    ↓
Interactive Viewer (optional)
```

---

## Format-Specific Guides

### SpikeGLX (Neuropixels)

**Notebook:** `load_spikeglx.ipynb`

**Input:** A SpikeGLX folder containing `.bin` and `.meta` files (e.g., `recording_g0_imec0/`).

**Key parameters to set:**

```python
spikeglx_folder = Path(r'C:\path\to\recording_g0_imec0')
base_folder     = Path(r'C:\path\to\output')
stream_name     = 'imec0.ap'    # adjust if using multiple probes (imec1.ap, etc.)
sorter          = 'kilosort4'   # or 'kilosort2_5'

# Preprocessing
freq_min = 400                  # highpass cutoff (Hz) — 300–400 typical for Neuropixels
cref_operator  = 'median'       # common reference method
cref_reference = 'global'       # use all channels for reference

# Optional: restrict to specific channels
manual_channel_ids    = None    # e.g. ['CH0', 'CH1', 'CH5'] to use only these
extra_bad_channel_ids = []      # manually add channels to exclude

# Optional: artifact removal (e.g., light pulses, stimulation)
artifact_timestamps_s = []      # list of artifact times in seconds, e.g. [10.5, 25.3]
artifact_ms_before    = 1.0
artifact_ms_after     = 2.0

# Quality filtering thresholds
amplitude_cutoff_thresh    = 0.1
isi_violations_ratio_thresh = 1.0
presence_ratio_thresh       = 0.9
```

**Notes:**
- Probe geometry is read automatically from the `.meta` file.
- Phase-shift correction is applied automatically (Neuropixels ADC multiplexing artifact).
- The preprocessed binary is cached in `base_folder/preprocess/`; re-running skips recomputing it.

---

### Open Ephys

**Notebook:** `load_openephys.ipynb`

**Input:** An Open Ephys session folder (containing `Record Node XXX/` subdirectories).

To find the correct stream name for your recording, run this before the pipeline:
```python
import spikeinterface as si
streams = si.get_neo_streams('openephys', '/path/to/session_folder')
print(streams)
```

**Key parameters to set:**

```python
openephys_folder = Path(r'C:\path\to\openephys_session')
base_folder      = Path(r'C:\path\to\output')
stream_name      = 'Signals CH'   # replace with your actual stream name

freq_min = 300   # highpass cutoff (Hz) — 300 Hz typical for Open Ephys

# Probe geometry (if not embedded in recording)
contact_pitch_um = 20   # spacing between channels in µm; adjust to match your probe

# TTL artifact removal (for recordings with stimulation)
use_ttl_artifacts = False          # set True if you have stimulation pulses
ttl_channel_id    = 'Rhythm FPGA TTL Input'   # name of TTL digital input channel

# Manual artifact removal (for any remaining noise)
artifact_timestamps_s = []
artifact_ms_before    = 1.0
artifact_ms_after     = 2.0
```

**Notes:**
- If the recording has no embedded probe geometry, a linear probe is generated automatically (channels spaced `contact_pitch_um` µm apart). Update `contact_pitch_um` to match your actual probe.
- TTL artifact removal (Pass 1) blanks windows around detected digital pulses. Manual removal (Pass 2) interpolates over any remaining transients. You can enable both together.
- For tetrode arrays, use `code test/load_openephys2.ipynb` which includes a tetrode probe builder and two-pass artifact removal.

---

### Multi-Channel Systems (MCS)

**Notebook:** `load_mcs.ipynb`

**Input:** Either an MCS `.h5` file (HDF5 export from Multi Channel DataManager) or an `.raw` binary.

**Key parameters to set:**

```python
mcs_file  = Path(r'C:\path\to\recording.h5')   # or .raw
base_folder = Path(r'C:\path\to\output')
use_raw   = False    # True for .raw binary, False for .h5 HDF5
sorter    = 'spykingcircus2'   # or 'mountainsort5', 'herdingspikes'

freq_min = 200   # highpass cutoff (Hz) — 200 Hz typical for MEA

# Probe geometry (if not embedded in .h5 file)
xpitch = 200    # horizontal pitch in µm — UPDATE to match your MEA
ypitch = 200    # vertical pitch in µm   — UPDATE to match your MEA

# UnitRefine automatic unit classification (SUA / MUA / noise)
_run_ur = False   # set True to enable; requires huggingface_hub and skops
```

**Notes:**
- If the `.h5` file contains electrode positions they are read automatically; otherwise a rectangular grid probe is generated using `xpitch` / `ypitch`. **Make sure these match your MEA geometry.**
- On Windows, preprocessing uses `n_jobs=1` to avoid HDF5 file locking errors. This is slower but necessary.
- If more than one-third of channels are detected as bad, a warning is issued but sorting continues. Review the channel plot carefully before proceeding.
- UnitRefine (if enabled) adds a second stage that classifies units as SUA, MUA, or noise using a pretrained deep learning model. Labels are saved to `curation_labels.csv`.

---

## Configuration Reference

### Universal Preprocessing Parameters

| Parameter | Default | Description |
|---|---|---|
| `freq_min` | format-dependent | Highpass filter cutoff (Hz). 400 for Neuropixels, 300 for Open Ephys, 200 for MEA. |
| `cref_operator` | `'median'` | Common reference method: `'median'` (CMR) or `'average'`. |
| `cref_reference` | `'global'` | Reference scope: `'global'` (all channels) or `'local'` (neighboring channels). |
| `waveform_ms_before` | `1.5` | Pre-spike window for waveform extraction (ms). |
| `waveform_ms_after` | `2.0` | Post-spike window for waveform extraction (ms). |
| `max_spikes_per_unit` | `500` | Maximum spikes used for waveform extraction per unit. Lower for faster testing. |

### Quality Filtering Thresholds

Units are kept only if **all three** conditions are met:

| Metric | Default threshold | Meaning |
|---|---|---|
| `amplitude_cutoff` | `< 0.1` | Low probability that spikes are cut off by the detection threshold (good SNR). |
| `isi_violations_ratio` | `< 1.0` | Fewer than 1 refractory period violation per spike on average. |
| `presence_ratio` | `> 0.9` | Unit is active in more than 90% of the recording duration. |

Adjust these thresholds in the quality filtering cell if your recording is short (< 1 min) or particularly noisy.

---

## Output Files

Each pipeline run produces the following structure in `base_folder/`:

```
base_folder/
├── preprocess/                  # Preprocessed binary recording (cached)
│   ├── traces_seg_0.bin
│   └── [SpikeInterface metadata]
├── sorting_<sorter>/            # Raw spike sorter output
│   └── sorter_output/
├── analyzer/                    # SortingAnalyzer: waveforms, metrics, all extensions
│   ├── extensions/
│   └── [SpikeInterface metadata]
├── quality_metrics.csv          # Per-unit quality table (firing rate, SNR, ISI, etc.)
├── curation_labels.csv          # MCS only, if UnitRefine enabled: SUA / MUA / noise labels
└── channel_map_*.csv            # Open Ephys tetrode variant only: probe mapping validation
```

To open the interactive viewer on a saved analyzer later:

```python
import spikeinterface.widgets as sw
analyzer = si.load_sorting_analyzer('path/to/base_folder/analyzer')
sw.plot_sorting_summary(analyzer, backend='spikeinterface_gui')
```

---

## Troubleshooting

**Windows file locking errors during preprocessing**
Close the interactive viewer (`spikeinterface_gui`) before re-running any cell that writes to `preprocess/`. If the folder is corrupted, delete it and re-run; the pipeline will regenerate it.

**All units removed after quality filtering**
Open `quality_metrics.csv` and check the actual values for your units. If the recording is short (< 1 min), `presence_ratio` may be artificially low — lower `presence_ratio_thresh`. If noise is high, loosen `amplitude_cutoff_thresh`.

**Sorter not found**
```python
import spikeinterface as si
si.get_installed_sorters()   # lists all sorters currently installed
```
Install the missing sorter (see [Requirements](#requirements)) and restart the kernel.

**More than one-third of channels detected as bad (MCS)**
This is common with MEA recordings that have damaged or disconnected electrodes. The pipeline continues but you should inspect the channel plot. To manually override: add known-good channels to `manual_channel_ids` or known-bad channels to `extra_bad_channel_ids`.

**Probe geometry incorrect or missing**
- SpikeGLX: geometry is read from the `.meta` file automatically.
- Open Ephys: if no geometry is embedded, set `contact_pitch_um` to match your probe's channel spacing.
- MCS: if the `.h5` file has no electrode positions, set `xpitch` and `ypitch` to your MEA's inter-electrode distance in µm.

**Open Ephys stream name not found**
```python
import spikeinterface as si
si.get_neo_streams('openephys', '/path/to/session')
```
Copy the correct stream name from the output into `stream_name`.
