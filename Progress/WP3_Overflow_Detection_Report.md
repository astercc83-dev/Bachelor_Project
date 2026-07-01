# WP3 — Real-Time Acquisition and Overflow Detection Report

**Author:** Samir Elsherbiny
**Project:** Development of a Python-Based Interface for a PXI Data Acquisition System
**Supervisors:** Prof. Dr. Oliver Amft, Dr. Mohammad Amayreh
**Card used:** NI PXIe-6386 (Slot 3), single channel `ai0`
**Work Package:** WP3 — Real-Time Acquisition and Visualization

---

## 1. Goal of this stage

The goal of WP3 is to read analog signals from the PXI card in real time, display
them live in Python, and study **buffer overflow and data loss**. The key
question from Dr. Amayreh was:

> Does data loss actually happen on the real hardware, and what causes it — the
> card, the bus, or the software?

To answer this, we built the software step by step on a **single channel**, and
deliberately searched for the point where data is lost. This report documents
every step and the final result.

---

## 2. Background: the two buffers (why overflow can happen)

Before the software, we need to understand where data can be lost. Data travels
from the card to Python through two buffers:

```
Card (ADC) → [FIFO on card] → DMA → [Host buffer in RAM] → Python reads
              small (~12,000)        large (~1,000,000)
```

- The **FIFO** is a small memory on the card. It overflows if the *bus* cannot
  drain it fast enough (a hardware limit).
- The **Host buffer** is a large memory in the PC's RAM. It overflows if
  *Python* cannot read it fast enough (a software limit).

The overflow we study in WP3 is the **host buffer overflow** — a software limit.
It has the error code **-200279**.

---

## 3. Method: step-by-step build

We did not write the final program in one step. We built it in small stages, and
tested each stage on the real hardware before moving on. This made every part
easy to understand and confirm.

### Stage 1 — Simplest read (one channel, finite)

We wrote the simplest possible program: read a fixed number of samples once and
print them.

```python
import nidaqmx
from nidaqmx.constants import AcquisitionType

with nidaqmx.Task() as task:
    task.ai_channels.add_ai_voltage_chan("PXI1Slot3/ai0")
    task.timing.cfg_samp_clk_timing(rate=20000, sample_mode=AcquisitionType.FINITE, samps_per_chan=100)
    data = task.read(number_of_samples_per_channel=100)
    print(data)
```

**What we learned:**
- A *task* is the measurement job. It has channels + timing + settings.
- `add_ai_voltage_chan` selects the physical channel (`ai0` on the Slot 3 card).
- `cfg_samp_clk_timing` sets the speed (`rate`) and how many samples.
- `FINITE` means "take a fixed number of samples, then stop by itself."

**Important discovery — minimum sample rate:**
When we first tried `rate=1000`, the card returned error **-200077**:

```
Property: DAQmx_SampClk_Rate
Requested Value: 1.0e3
Maximum Value: 50.0e6
Minimum Value: 20.0e3
```

This confirmed **on the real hardware** that the card has a minimum sample rate
of **20,000 S/s** (20 kS/s), matching the official NI specification. We then used
`rate=20000` and the read worked, returning 100 samples of noise (~0.006 V,
because nothing was connected to the channel).

### Stage 2 — Continuous reading in a loop

We changed the mode to `CONTINUOUS` (take samples forever until stopped) and read
repeatedly in a loop.

```python
task.timing.cfg_samp_clk_timing(rate=20000, sample_mode=AcquisitionType.CONTINUOUS)
task.start()
for i in range(10):
    data = task.read(number_of_samples_per_channel=1000)
    print("Read", i, "- got", len(data), "samples")
task.stop()
```

**What we learned:**
- `CONTINUOUS` needs an explicit `task.start()` before the loop and
  `task.stop()` after it. This matches the NI manual, which says starting the
  task once before the loop (instead of letting each read start/stop it) is much
  more efficient.
- All 10 loops returned 1000 samples each. Python was **faster** than the card,
  so the host buffer never filled up. No overflow.

### Stage 3 — Searching for overflow by raising the sample rate

We wanted to see the host buffer overflow **naturally** — not by artificially
slowing Python (for example with `sleep`), but by making the card produce data
faster than Python can read it. So we raised the sample rate step by step, with
Python only reading (no extra work yet).

**Result:** even at **14 MS/s** (the card's realistic maximum on one channel),
there was **no overflow**. Python kept up easily.

**Why?** With one channel at 14 MS/s, the data rate is only:
```
1 channel × 14,000,000 samples/s × 2 bytes = 28 MB/s
```
The bus can carry 250 MB/s, so it was almost empty. And when Python asks for 1000
samples, it simply *waits* for the card — it is never behind. So on a single
channel, with reading only, no overflow occurs within the card's real limits.

*(An overflow did appear at ~16.67 MS/s, but that rate is above the card's real
maximum of 14.29 MS/s per channel, so it is not a realistic case.)*

**Conclusion of this stage:** On one channel, plain reading is not enough to
cause overflow. The overflow must come from Python being busy with *real work*
between reads — which is exactly what the project requires (live visualization).

### Stage 4 — Adding real processing (simple calculations)

We added simple calculations after each read (average, maximum, minimum), because
in the real project we read data and then process it.

```python
average = sum(data) / len(data)
highest = max(data)
lowest  = min(data)
```

**Result:** at 14 MS/s, all 50 loops finished with **no overflow**. Simple
calculations are too fast to slow Python down enough. This is a useful result: it
shows Python is fast enough for light processing.

### Stage 5 — Adding live plotting (the real, heavy work)

The project (WP3) explicitly requires **live visualization** of the signal.
Drawing a graph and updating it on screen is a heavy operation. This is the
realistic task that can slow Python down.

We built the live plot properly, so that only the signal line updates while the
axes stay fixed (a true live plot, not a series of redrawn images):

```python
import matplotlib.pyplot as plt

plt.ion()  # interactive mode: update the plot without stopping the program

# Create the plot ONCE before the loop
figure, axis = plt.subplots()
line, = axis.plot(range(1000), [0] * 1000)
axis.set_ylim(-0.1, 0.1)      # fix the Y-axis so it does not jump
axis.set_xlabel("Sample number")
axis.set_ylabel("Voltage (V)")

with nidaqmx.Task() as task:
    task.ai_channels.add_ai_voltage_chan("PXI1Slot3/ai0")
    task.timing.cfg_samp_clk_timing(rate=rate, sample_mode=AcquisitionType.CONTINUOUS)
    task.start()
    for i in range(200):
        data = task.read(number_of_samples_per_channel=1000)
        line.set_ydata(data)   # update the existing line (do not redraw everything)
        plt.pause(0.01)        # let matplotlib draw the update on screen
    task.stop()

plt.ioff()
plt.show()
```

**Key idea:** instead of clearing and redrawing the whole figure every loop
(which makes the axes jump and is slow), we update the data of one existing line
with `line.set_ydata(data)` and keep the axes fixed. This is the correct, smooth
way to do live plotting.

---

## 4. The main result: overflow with live plotting

With live plotting active, we raised the sample rate step by step on **one
channel**, and found the exact point where the host buffer overflows.

**Result:** overflow (error **-200279**) started at approximately
**45,000 samples/second (45 kS/s)**, after about **193 read loops**.

The error message itself explained the cause:

> The application was unable to keep up with the hardware acquisition. Increasing
> the buffer size, reading the data more frequently, or specifying a fixed number
> of samples to read instead of reading all available samples might correct the
> problem. (Status Code: -200279)

---

## 5. Comparison and interpretation (the important finding)

The comparison below is the core scientific result of this stage:

| Situation | Overflow happens at |
|-----------|---------------------|
| Reading only (no plotting) | not within the real limit — Python kept up to 14 MS/s |
| Reading + **live plotting** | **~45 kS/s** |

This is a very large difference. Without plotting, Python kept up at 14 million
samples per second. With live plotting, Python could only keep up to about 45
thousand samples per second — roughly **300 times slower**.

**Interpretation:**
- The card is **not** the bottleneck. It can sample far faster than this.
- The **bus** is not the bottleneck either. At one channel the bus is almost
  empty (28 MB/s out of 250 MB/s).
- The real bottleneck is the **software**: updating the live plot on screen is
  slow, so Python cannot empty the host buffer fast enough, and the buffer
  overflows.

This directly answers Dr. Amayreh's question: the bus speed is not the problem.
The problem is that the program cannot process (visualize) the incoming samples
fast enough — exactly the situation described in the WP3 task definition.

---

## 6. What each NI-DAQmx term means (glossary)

For clarity, here is what each software term we used means:

- **Task** — the measurement job: one or more channels plus timing and settings.
- **Channel (`ai0`)** — one physical analog input on the card (two wires,
  differential).
- **`cfg_samp_clk_timing`** — sets the sample clock: the `rate` (samples per
  second) and how the acquisition runs.
- **`rate`** — how many samples per second the card takes. Limited to
  20 kS/s (minimum) up to 14.29 MS/s (maximum on one channel, internal clock).
- **FINITE** — take a fixed number of samples, then stop automatically. Used for
  a single read.
- **CONTINUOUS** — take samples forever until stopped. Used for a read loop, and
  needs explicit `start()` / `stop()`.
- **`task.read(number_of_samples_per_channel=N)`** — read N samples from the host
  buffer into Python.
- **Host buffer** — the large memory in PC RAM that holds samples until Python
  reads them. It overflows if Python is too slow (error -200279).
- **Error -200279** — host buffer overflow: the application could not keep up
  with the hardware.
- **Error -200077** — requested sample rate is outside the allowed range (below
  the 20 kS/s minimum or above the maximum).

---

## 7. Conclusion and next step

We proved, on the real hardware and on a single channel, that:

1. Data loss (host buffer overflow, error -200279) **does happen naturally**.
2. It is caused by the **software being too slow** (live plotting), not by the
   card or the bus.
3. On one channel it starts at about **45 kS/s** when live plotting is active,
   compared to no overflow up to 14 MS/s without plotting.

**Next steps (as defined in WP3):**
- Increase the number of channels step by step and repeat the measurement.
- Apply performance techniques suggested in the project description
  (multithreading, multiprocessing, queue-based data handling) to prevent the
  overflow and keep the live visualization running without data loss.

The error message itself pointed to these solutions (increase buffer size, read
more frequently, read a fixed number of samples), which we will apply and
evaluate in the next stage.

---

*All hardware limits (20 kS/s minimum, 14.29 MS/s maximum, 250 MB/s bus, FIFO and
host buffer roles) are based on the official NI PXIe-6386 documentation and were
confirmed empirically on the real hardware during this work.*
