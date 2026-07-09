# PXI System — First Contact Report
**Project:** Development of a Python-Based Interface for a PXI Data Acquisition System  
**Student:** Samir Elsherbiny (ID: 5581873)  
**Supervisor:** Dr. Mohammad Amayreh  
**Date:** June 2026  

---

## Overview

This report documents the first successful contact with the PXI hardware at Hahn-Schickard. All steps were performed directly on the PXI embedded PC running Windows 10.

---

## Step 1: Environment Setup on the PXI

### 1.1 Python Installation Check
The PXI embedded PC had Python pre-installed. Verified using:

```
py --version
```

**Result:**
```
Python 3.12.3
```

### 1.2 Installing the nidaqmx Python Library
The NI-DAQmx driver (version 22.5) was already installed on the PXI system. The Python wrapper was installed using:

```
py -m pip install nidaqmx
```

**Result:** Successfully installed nidaqmx and all dependencies.

### 1.3 Setting Up the Project
The project code was downloaded from GitHub directly onto the PXI Desktop:

```
https://github.com/astercc83-dev/Bachelor_Project
```

The project was opened in Visual Studio Code (already installed on the PXI).

---

## Step 2: Hardware Discovery

### 2.1 Code Used

```python
import nidaqmx.system

system = nidaqmx.system.System.local()
print(f"Driver: {system.driver_version}")

for device in system.devices:
    print(f"Device: {device.name}")
    print(f"  Channels: {[ch.name for ch in device.ai_physical_chans]}")
```

### 2.2 Results

```
Driver: DriverVersion(major_version=22, minor_version=5, update_version=0)

Device: PXI1Slot2
  Channels: []

Device: PXI1Slot3
  Channels: ['PXI1Slot3/ai0', 'PXI1Slot3/ai1', 'PXI1Slot3/ai2',
             'PXI1Slot3/ai3', 'PXI1Slot3/ai4', 'PXI1Slot3/ai5',
             'PXI1Slot3/ai6', 'PXI1Slot3/ai7']

Device: PXI1Slot4
  Channels: ['PXI1Slot4/ai0', 'PXI1Slot4/ai1', 'PXI1Slot4/ai2',
             'PXI1Slot4/ai3', 'PXI1Slot4/ai4', 'PXI1Slot4/ai5',
             'PXI1Slot4/ai6', 'PXI1Slot4/ai7']
```

### 2.3 Analysis

| Device | Type | Channels |
|--------|------|----------|
| PXI1Slot2 | Controller / AO+DIO Card | No AI channels |
| PXI1Slot3 | Analog Input Card | 8 channels (ai0–ai7) |
| PXI1Slot4 | Analog Input Card | 8 channels (ai0–ai7) |

**Total available analog input channels: 16**

> **Important note:** The device names on this system use the format `PXI1SlotX/aiY`, not the generic `Dev1/ai0` format used in example code. This must be used in all subsequent code.

---

## Step 3: First Real Voltage Reading

### 3.1 Code Used

```python
import nidaqmx

with nidaqmx.Task() as task:
    task.ai_channels.add_ai_voltage_chan("PXI1Slot3/ai0")
    value = task.read()
    print(f"Voltage: {value:.4f} V")
```

### 3.2 Result

```
Voltage: 0.8766 V
```

This was the **first successful real voltage reading** from the PXI hardware using Python.

---

## Step 4: CPU Core Discovery

To plan the multiprocessing architecture, the number of available CPU cores was determined:

```python
import multiprocessing
import platform

print(f"Cores: {multiprocessing.cpu_count()}")
print(f"Processor: {platform.processor()}")
```

**Result:**
```
Cores: 8
Processor: Intel64 Family 6 Model 94 Stepping 3, GenuineIntel
```

**The PXI embedded controller has 8 CPU cores.** This allows true parallel execution across multiple processes — one process per core.

---

## Step 5: Sampling Rate Benchmark

### 5.1 Purpose
Dr. Amayreh requested determining the maximum achievable sampling rate in Python on the PXI hardware.

### 5.2 Code Used

```python
import nidaqmx
import time
from nidaqmx.constants import AcquisitionType

sampling_rates = [20000, 100000, 1000000, 5000000, 14000000, 50000000]

for rate in sampling_rates:
    try:
        with nidaqmx.Task() as task:
            task.ai_channels.add_ai_voltage_chan("PXI1Slot3/ai0")
            task.timing.cfg_samp_clk_timing(
                rate=rate,
                sample_mode=AcquisitionType.FINITE,
                samps_per_chan=1000
            )
            start = time.time()
            data = task.read(1000)
            elapsed = time.time() - start
            print(f"Rate: {rate/1e6:.1f} MS/s → "
                  f"read 1000 samples in {elapsed*1000:.1f} ms")
    except Exception as e:
        print(f"Rate: {rate/1e6:.1f} MS/s → failed: {e}")
```

### 5.3 Results

```
Rate: 0.02 MS/s  → read 1000 samples in  50.0 ms ✓
Rate: 0.1  MS/s  → read 1000 samples in  10.0 ms ✓
Rate: 1.0  MS/s  → read 1000 samples in  40.0 ms ✓
Rate: 5.0  MS/s  → read 1000 samples in  30.0 ms ✓
Rate: 14.0 MS/s  → read 1000 samples in  30.0 ms ✓
```

### 5.4 Hardware Limits Discovered

The NI-DAQmx driver reported the following limits for this hardware:

```
Minimum Sampling Rate: 20,000 S/s  (20 kS/s)
Maximum Sampling Rate: 50,000,000 S/s  (50 MS/s)
```

> **Important note:** Any sampling rate below 20 kS/s will cause an error on this hardware. All future code must use rates between 20 kS/s and 50 MS/s.

---

## Step 6: Continuous Reading into Shared Memory

### 6.1 Architecture Decision

Based on the discussion with Dr. Amayreh, the architecture was changed from Queue-based to **Shared Memory**:

| | Queue | Shared Memory |
|--|-------|--------------|
| Speed | Requires copying data | No copying — direct access |
| Memory | Each process has its own copy | One array, all processes see it |
| Suitable for | Small data, I/O tasks | Large data, high-speed DAQ |

For 50 MS/s × 16 channels, Shared Memory is significantly more efficient.

### 6.2 The reader.py File

```python
import nidaqmx
import numpy as np
from multiprocessing import shared_memory

# ── Configuration ──────────────────────────────────────────
CHANNEL = "PXI1Slot3/ai0"
SAMPLE_RATE = 1000000       # 1 MS/s
BUFFER_SIZE = 1000          # 1000 samples per read

# ── Create Shared Memory ───────────────────────────────────
buffer_size_bytes = BUFFER_SIZE * np.float64().itemsize

shm = shared_memory.SharedMemory(
    name="pxi_buffer",
    create=True,
    size=buffer_size_bytes
)

buffer = np.ndarray(
    shape=(BUFFER_SIZE,),
    dtype=np.float64,
    buffer=shm.buf
)

# ── Reader Function ────────────────────────────────────────
def read_from_pxi():
    with nidaqmx.Task() as task:
        task.ai_channels.add_ai_voltage_chan(CHANNEL)
        task.timing.cfg_samp_clk_timing(
            rate=SAMPLE_RATE,
            sample_mode=nidaqmx.constants.AcquisitionType.CONTINUOUS
        )
        task.start()
        print("Reader started...")

        while True:
            data = task.read(
                number_of_samples_per_channel=BUFFER_SIZE
            )
            buffer[:] = data
            print(f"Read {BUFFER_SIZE} samples, "
                  f"first value: {buffer[0]:.4f} V")

# ── Entry Point ────────────────────────────────────────────
if __name__ == "__main__":
    try:
        read_from_pxi()
    except KeyboardInterrupt:
        print("Reader stopped by user.")
    finally:
        shm.close()
        shm.unlink()
        print("Shared memory cleaned up.")
```

### 6.3 Result

```
Reader started...
Read 1000 samples, first value: 0.8766 V
Read 1000 samples, first value: 0.8812 V
Read 1000 samples, first value: 0.8791 V
...
(hundreds of lines per second)
```

The reader successfully:
- Connected to the PXI hardware
- Read 1000 samples per loop at 1 MS/s
- Wrote data into Shared Memory continuously
- Stopped cleanly when Ctrl+C was pressed
- Released the Shared Memory after stopping

---

## Summary of Hardware Specifications Discovered

| Property | Value |
|----------|-------|
| NI-DAQmx Driver | Version 22.5 |
| AI Card 1 | PXI1Slot3 (8 channels: ai0–ai7) |
| AI Card 2 | PXI1Slot4 (8 channels: ai0–ai7) |
| Total AI Channels | 16 |
| Minimum Sampling Rate | 20 kS/s |
| Maximum Sampling Rate | 50 MS/s |
| CPU | Intel Core (Family 6, Model 94) |
| CPU Cores | 8 |
| Operating System | Windows 10 |
| Python Version | 3.12.3 |

---

## Next Steps

1. **Build `processor.py`** — a separate process that reads from the Shared Memory and displays data in real-time using PyQtgraph.
2. **Build `saver.py`** — a separate process that reads from Shared Memory and saves data to ABF format.
3. **Build `main.py`** — launches all processes together using `multiprocessing.Process`.
4. **Implement Double Buffering** — two alternating buffers (Buffer A and Buffer B) to prevent data loss during processing.
5. **Measure processing delay** — benchmark how long the Processor takes compared to the Reader.
