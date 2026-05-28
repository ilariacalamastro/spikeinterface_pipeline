"""
Generate a synthetic MCS HDF5 dummy recording for testing load_mcs.ipynb.
Output: dummy_mcs/dummy_recording.h5  (next to this script)

Run once before opening the notebook:
    python make_dummy_mcs.py
"""
import numpy as np
import h5py
from pathlib import Path

# ── Parameters ───────────────────────────────────────────────────────────────
N_CHANNELS    = 16        # 4×4 MEA grid
SAMPLING_RATE = 25_000    # Hz  (Tick = 40 µs)
DURATION_S    = 30        # seconds — short enough to sort quickly
NOISE_STD     = 15        # ADC units ≈ µV RMS (gain = 1 → 1 ADC = 1 µV)
SEED          = 42

N_SAMPLES = int(DURATION_S * SAMPLING_RATE)
TICK_US   = int(1e6 / SAMPLING_RATE)   # 40 µs → 25 kHz

rng = np.random.default_rng(SEED)

# ── Background noise ─────────────────────────────────────────────────────────
data = (rng.standard_normal((N_CHANNELS, N_SAMPLES)) * NOISE_STD).astype(np.int16)

# ── Spike waveform template (40 samples, negative peak at sample 10) ─────────
_t  = np.arange(40, dtype=np.float32)
_wf = (-120 * np.exp(-(_t - 10) ** 2 / 8.0) + 30 * np.exp(-(_t - 25) ** 2 / 20.0))

def _add_unit(data, ch, firing_rate_hz):
    n_spikes = int(DURATION_S * firing_rate_hz)
    times = np.sort(rng.integers(50, N_SAMPLES - 50, size=n_spikes))
    # enforce 0.8 ms refractory period (20 samples)
    times = times[np.concatenate([[True], np.diff(times) > 20])]
    for t in times:
        seg = data[ch, t : t + 40].astype(np.float32) + _wf
        data[ch, t : t + 40] = np.clip(seg, -32768, 32767).astype(np.int16)

# 4 synthetic units on distinct channels with varied firing rates
_add_unit(data,  2, 20)
_add_unit(data,  5, 35)
_add_unit(data,  9, 12)
_add_unit(data, 13, 50)

# ── InfoChannel compound dataset ─────────────────────────────────────────────
# Fields used by SpikeInterface (mcsh5extractors.py):
#   Unit, Tick, Exponent, ConversionFactor, ADZero, ChannelID, Label
# gain_uV   = 1e6 * ConversionFactor * 10^Exponent   → with CF=1, exp=-6: gain=1.0 µV/ADC
# offset_uV = -1e6 * ADZero * 10^Exponent * gain_uV  → ADZero=0: offset=0
info_dtype = np.dtype([
    ('ChannelID',                       np.int32),
    ('Label',                           'S32'),
    ('RawDataType',                     'S8'),
    ('Unit',                            'S8'),
    ('Exponent',                        np.int32),
    ('ADCBits',                         np.int32),
    ('HighPassFilterType',              'S16'),
    ('HighPassFilterCutOffFrequency',   'S16'),
    ('HighPassFilterOrder',             'S8'),
    ('LowPassFilterType',               'S16'),
    ('LowPassFilterCutOffFrequency',    'S16'),
    ('LowPassFilterOrder',              'S8'),
    ('Tick',                            np.int64),
    ('ConversionFactor',                np.int64),
    ('ADZero',                          np.int32),
])

info = np.zeros(N_CHANNELS, dtype=info_dtype)
for i in range(N_CHANNELS):
    info[i]['ChannelID']        = i + 1
    info[i]['Label']            = f'E{i+1:03d}'.encode()
    info[i]['RawDataType']      = b'INT_16'
    info[i]['Unit']             = b'V'
    info[i]['Exponent']         = -6      # gain_uV = 1e6 * 1 * 1e-6 = 1.0
    info[i]['ConversionFactor'] = 1
    info[i]['Tick']             = TICK_US  # 40 → 25 kHz
    info[i]['ADZero']           = 0

# ── ChannelDataTimeStamps ────────────────────────────────────────────────────
# Shape (1, 3): [first_tick, step, last_tick]
# SpikeInterface computes: TimeVals = arange(col0, col2+1) * (Tick/1e6)
timestamps = np.array([[0, 1, N_SAMPLES - 1]], dtype=np.int64)

# ── Write HDF5 ───────────────────────────────────────────────────────────────
out_dir  = Path(__file__).parent / 'dummy_mcs'
out_dir.mkdir(exist_ok=True)
out_path = out_dir / 'dummy_recording.h5'

with h5py.File(out_path, 'w') as f:
    stream = f.require_group('/Data/Recording_0/AnalogStream/Stream_0')
    stream.create_dataset('ChannelData',            data=data)
    stream.create_dataset('InfoChannel',            data=info)
    stream.create_dataset('ChannelDataTimeStamps',  data=timestamps)

print(f"Done: {out_path}")
print(f"  {N_CHANNELS} channels  |  {N_SAMPLES:,} samples  |  {DURATION_S} s  |  {SAMPLING_RATE} Hz")
print(f"  {out_path.stat().st_size / 1e6:.1f} MB")
print(f"  4 synthetic units on channels 2, 5, 9, 13")
