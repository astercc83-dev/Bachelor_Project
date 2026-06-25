# Hardware Overview — PXIe-6386 DAQ Card (Detailed Guide)

**Author:** Samir Elsherbiny
**Project:** Development of a Python-Based Interface for a PXI Data Acquisition System
**Supervisors:** Prof. Dr. Oliver Amft, Dr. Mohammad Amayreh
**Card model:** NI PXIe-6386 (confirmed on the real hardware via `device.product_type`)

---

## About this document

This is a complete, beginner-friendly explanation of how the card turns a real
voltage from a chip into a number inside Python. It follows one example signal
from beginning to end. Every step has the real specification number behind it,
and simple everyday examples to make each idea easy to picture.

> **Official sources (for citation):**
>
> 1. PXIe-6386 Specifications, National Instruments.
>    https://www.ni.com/docs/en-US/bundle/pxie-6386-specs/page/specs.html
> 2. NI PXIe-6386 and PXIe-6396 Supplementary Information and Caveats.
>    https://www.ni.com/en/support/documentation/supplemental/19/ni-pxie-6386-and-ni-pxie-6396-supplementary-information-and-cave.html
> 3. Specifications Explained: NI Multifunction I/O (MIO) DAQ, National Instruments.

---

## The example we will follow

A chip outputs **0.5 volts** on one wire pair.
We want to capture this and see the number `0.5` in Python.

Here is the full journey, step by step.

---

# STEP 1 — The signal enters the card (differential input)

## What happens

The card has **8 analog input channels**. We connect the chip to one of them.
Each channel uses **two wires**: AI+ and AI−.

The card does **not** measure one wire alone. It measures the **difference**
between the two wires:

```
Result = voltage on AI+   minus   voltage on AI-
```

## Why two wires? (removing noise)

This is called a *differential* measurement, and its job is to remove noise.

**Simple example:**

Our real signal is 0.5 V.
- Wire AI+ carries: `0.5`
- Wire AI− carries: `0`
- The card subtracts: `0.5 − 0 = 0.5` ✅ Correct.

Now imagine noise of 0.2 V lands on the wires. Noise always lands on **both**
wires equally, because they run side by side.
- Wire AI+ now carries: `0.5 + 0.2 = 0.7`
- Wire AI− now carries: `0 + 0.2 = 0.2`
- The card subtracts: `0.7 − 0.2 = 0.5` ✅ Still correct!

The noise (0.2) was on both wires, so subtraction **cancelled it out**. If the
card had measured one wire only, it would have read `0.7` (wrong). This is why
differential measurement gives a much cleaner signal.

## The specifications behind this step

- The card barely "pulls" on the chip. Input impedance is **>100 GΩ**, and it
  draws only about **±10 pA** of bias current (a tiny fraction of a millionth of
  an amp). So it does not disturb the chip being measured.
- How well it cancels noise is the **CMRR (DC to 60 Hz): 70 dB** — common-mode
  noise is attenuated by about 3,000×.

---

# STEP 2 — We choose the range

## What happens

Before measuring, we tell the card which voltage range to use. The card offers
four ranges:

```
±1 V   |   ±2 V   |   ±5 V   |   ±10 V
```

## Simple example (the ruler)

Think of a ruler. A short ruler (1 metre) shows fine detail. A long ruler
(10 metres) measures big things but misses small detail.

A smaller range gives finer detail. Because our signal is small (0.5 V), we
choose the smallest range **±1 V** for the best precision.

---

# STEP 3 — Simultaneous sampling (the card's special feature)

## What happens

**Every channel has its own converter (ADC).** All 8 channels capture their
voltage at the *exact same instant*. This is called **simultaneous sampling**.

## Why this matters

Cheaper cards use **one shared converter** that jumps between channels one by
one. The problem: channel 7 gets captured slightly later than channel 0, so
there is a tiny time difference between channels.

Our card has no such problem — **zero timing difference between channels**. This
is important for our project, where the measured signal and the command voltage
must line up perfectly in time.

## The specification behind this step

The PXIe-6386 is described by NI as a **simultaneous sampling** multifunction
DAQ device.

---

# STEP 4 — The ADC turns voltage into a number

## What happens

The converter is called an **ADC** (Analog-to-Digital Converter). On our card it
is **16 bits**, which means it splits the range into **65,536 tiny steps**.

## How fine is one step?

On the ±1 V range, the total span is 2 V (from −1 to +1):

```
2 V ÷ 65,536 steps ≈ 0.0000305 V  =  about 30.5 microvolts per step
```

So the smallest change the card can detect is about 30.5 µV — very precise.

## The mechanism: how does the ADC actually convert? (Successive Approximation)

This is the most important idea. The ADC works like the game **"guess my
number"**, where the smartest strategy is to always guess the middle.

Inside the ADC there are two parts:
- A **voltage generator** (we control it, so we always *know* its output).
- A **comparator** — it answers one question only: *"Is the incoming voltage
  bigger or smaller than my guess?"*

**Worked example — converting 0.5 V (using a simple 3-bit ADC, range 0 to 1 V):**

3 bits means 8 steps: `0, 0.125, 0.25, 0.375, 0.5, 0.625, 0.75, 0.875`

- **Guess 1 (the middle):** try **0.5**. Is the signal ≥ 0.5? → **Yes** → bit = 1
- **Guess 2:** try **0.75**. Is the signal ≥ 0.75? → **No** → bit = 0
- **Guess 3:** try **0.625**. Is the signal ≥ 0.625? → **No** → bit = 0

Result: `100` in binary = step number **4**.
Convert to volts: `4 × 0.125 = 0.5 V` ✅

With just 3 yes/no questions, the ADC found 0.5. Our real card asks **16
questions** (16 bits), giving 65,536 possible steps — far more precise.

## Why multiply by the step size?

The ADC outputs a **step number**, not volts. To convert it to volts we multiply
by the size of one step:

```
volts = step number × step size
4 × 0.125 = 0.5 V
```

The step size itself is `range ÷ number of steps`. On our real card:
`2 V ÷ 65,536 = 30.5 µV` per step.

## The key insight: how does it "know" the signal is 0.5?

The incoming signal is analog — there is no number written on it. The ADC never
"reads" it directly. Instead, it **compares** the unknown signal against
voltages it generates itself and already knows. Each comparison says "bigger or
smaller", and from those answers it builds the number.

It is like guessing an object's weight using a balance scale: you hold a known
weight on one side and the unknown on the other, and compare. You do not need a
number written on the object — you need a known reference to compare against.

## Where does the "known voltage" come from?

From a **Voltage Reference** inside the card — a very stable, fixed voltage
source, like an official "master ruler" for volts. The voltage generator (DAC)
divides this reference into the known guess values.

> **Honest note for the thesis:** NI does **not** publish the exact internal
> voltage reference value — it is a proprietary design detail. What NI publishes
> for the user is the **input ranges** (±1, ±2, ±5, ±10 V), and those are the
> values we use in all resolution calculations.

## How accurate is the final reading?

On the ±1 V range, the absolute accuracy at full scale is about **219 µV** — well
under a millivolt.

---

# STEP 5 — The sample clock (the "take a sample now" tick)

## What is a clock?

A clock here is **not** a wall clock that tells the time. It is something that
produces a **pulse** at a perfectly steady rhythm:

```
tick ... tick ... tick ... tick ...
 (each tick is the same time apart as the next, exactly)
```

Picture a drum beating a perfectly steady rhythm. Each beat means "take a sample
now!"

## What does it do?

The clock decides **when** the ADC takes each sample. Each tick tells all 8
channels: "freeze the voltage now and convert it to a number!"

The number of ticks per second = the **sample rate**. So the clock controls the
speed of measurement.

## Why steady timing matters

Think of filming a video. If the camera captured frames at uneven time gaps, the
video would look shaky and wrong. The same is true here: to rebuild the signal
correctly, samples must be taken at perfectly equal moments.

The specs for how steady the clock is:
- **Timing accuracy: 50 ppm of sample rate** (error of only 50 parts per million)
- **Timing resolution: 10 ns** (it can set the gap between ticks to a precision
  of 10 nanoseconds — a billionth of a second)

## Where the clock comes from, and how it works

There is one fast **master clock** inside the card, and everything is built from
it:

- **Master clock = 100 MHz** (100 million ticks per second). This is the main
  drum (the "100 MHz Timebase").
- For slower speeds, the card **divides** the 100 MHz down ("divide down").

This is exactly why our maximum is **14.29 MS/s**, not 15. NI explains: the
maximum with the internal/backplane clock is **14.29 MS/s/ch due to the divide
down from 100 MHz clocks**. To reach the full **15 MS/s** you need an **external
sample clock**.

The minimum is **20 kS/s** — going slower causes error **-200077** (a hardware
limit we already observed).

## The key point: the clock is in hardware, not in Python

The clock runs in the electronics themselves — not in Windows, not in Python.

**Proof:** when we paused Python for half a second, samples kept arriving
perfectly spaced. The hardware drum never stopped. Windows can lag, Python can
freeze, but the clock keeps beating. This is what makes the timing reliable.

```
Python sleeps 😴  →  the drum keeps beating ✅  →  samples stay evenly spaced ✅
```

---

# STEP 6 — The onboard FIFO (a small shock absorber)

## What it is

The FIFO is a **small memory (a box)** on the card itself, located right after
the ADC. As soon as the ADC produces a number, the number waits in this box.

FIFO stands for **First In, First Out** — the first sample in is the first
sample out.

## What "First In, First Out" means

Picture a **queue at a bakery**. The first person to join the queue is the first
to get bread and leave. Nobody cuts in line.

The FIFO keeps the samples in the exact same order they arrived. This matters: if
the order got mixed up, the signal would be wrong (sample 5 arriving before
sample 3). The FIFO preserves the correct order.

```
In:   1 → 2 → 3 → 4 → 5
Out:  1 → 2 → 3 → 4 → 5   ✅ same order
```

## Why the box exists

Picture a **tap dripping** steadily into a cup, and you must empty the cup every
now and then. The tap (the ADC) drips at a perfectly steady rate, but emptying
the cup (sending to the PC) happens in bursts and can be slightly delayed.

The FIFO **holds the water** during those tiny delays. It is a **shock
absorber** between the steady ADC and the bursty transfer to the PC. Without it,
any tiny delay would lose a sample instantly.

## The size of the box on our card

From the official NI specification:

```
Input FIFO size:
  8,191 samples shared among channels used
  +  4,096 samples dedicated per channel
```

This is a smart design:
- **Each channel** has its **own private box** = 4,096 samples
- **On top of that** there is a **shared box** = 8,191 samples for all

Why is this good? Each channel is guaranteed its own space. A busy channel
cannot eat the space of the other channels.

**Note — matching the real measurement:** on the PXI you measured a FIFO of
about **12,000–12,287 samples** for a single channel. That matches the spec:
`4,096 (private) + 8,191 (shared) = 12,287` for one channel. A small difference
is normal because the card reserves a few samples for internal use. Your
measurement confirms the official numbers on the real hardware.

## Is the box big or small?

Small — on purpose! Let's calculate how long it can hold data per channel at top
speed:

```
4,096 samples ÷ 14.29 million samples/second ≈ 0.29 milliseconds
```

That is only about **a third of a thousandth of a second**! Why so small? Because
it is **not** meant to be storage — it is only a shock absorber. The next step
(DMA) empties it constantly and very fast, so it does not need to be large.

Picture a **sink basin**, not a water tank. The basin holds water for a moment
until it drains. It is not designed to store.

## What if the box fills up?

If the computer falls behind for longer than the box can hold, the box
**overflows**, and new samples have nowhere to go → they are **lost**.

This is error **-200279** — the exact error we triggered on purpose to test it.
Now we know what it means: "the box filled up and samples were lost because
nothing emptied it fast enough."

---

# STEP 7 — DMA (the smart delivery truck)

## The problem DMA solves

Every computer has a **brain** called the **CPU** (the processor). It does all
the calculations — think of it as a smart but very busy manager.

Now, samples come out of the card at a crazy speed — up to 14 million per second
— and they must be moved from the small box (FIFO) on the card to the computer's
RAM.

**Who moves them?**

## The old, bad way: the CPU moves them itself

Imagine the CPU carrying every sample by hand. For each sample it must:
1. Stop what it is doing
2. Take the sample from the box
3. Put it in RAM
4. Go back to its work
5. ...repeat a microsecond later

At 14 million samples per second, the CPU would do this 14 million times per
second! It would be **busy all the time** with a silly job (moving data) and
could not run Python, draw the graph, or do anything else. The computer would
nearly freeze. This method is called **Programmed I/O**, and it is slow and
wasteful for high speeds.

## The clever solution: DMA

People asked: why should the CPU waste itself on moving data? Let's make a
**special delivery truck** whose only job is moving data, and let the CPU go do
its important work.

This truck is called **DMA = Direct Memory Access**.

The word **"Direct"** is the secret: the truck moves data from the card to RAM
**directly, without going through the CPU at all**.

> NI spec: **Data transfers: DMA (scatter-gather), programmed I/O (SW timed)**.
> The card supports both, but DMA is the fast, smart one.

## What "Direct Memory Access" means, word by word

- **Memory** = the computer's RAM
- **Access** = reaching / entering
- **Direct** = without a middle-man

So: *direct access to RAM*. The truck reaches RAM itself and places the data
there, without asking the CPU each time.

Picture an office with a manager (CPU) and a courier (DMA). Instead of the
manager getting up every minute to file papers, the courier files them. The
manager keeps working; the courier handles all the carrying.

## How DMA works, step by step

**Step 1 — Setup (once, at the start)**
When you start the measurement in Python, the CPU tells the DMA once: "Data will
come from this card; put it in this place in RAM." Then the CPU's job is almost
done.

**Step 2 — Automatic work (runs by itself)**
The DMA watches the FIFO on the card. As soon as the box has gathered enough
samples, the DMA moves on its own:
- takes a block of samples from the box
- moves it straight to RAM
- goes back to watching

This happens millions of times per second without ever bothering the CPU.

**Step 3 — It notifies the CPU only after a big chunk**
The DMA does not talk to the CPU for every sample. It keeps moving quietly, and
when it finishes a large block it tells the CPU "this part is done, the data is
ready in RAM." So the CPU steps in once instead of millions of times.

```
Without DMA:  CPU interrupted 14 million times/second 😫
With DMA:     CPU interrupted only a few times/second 😎
```

## What "Scatter-Gather" means

RAM is not always free in one big connected block. Sometimes the free space is
**scattered** in separate places.

- **Scatter** = spread out / distribute
- **Gather** = collect

A smart DMA can spread data into these scattered places, or collect it from
them, **without the CPU's help**. So it does not need one big connected block —
it handles scattered spaces. Like a clever postman who can deliver to scattered
addresses all over the city, not just one building.

## How many trucks do we have?

From the spec:

```
DMA channels: 8
(usable for analog input, analog output, digital input, digital output,
 and counter/timers 0, 1, 2, 3)
```

You have **8 DMA channels** — separate transfer paths for different jobs. So if
you measure inputs and generate outputs at the same time, each has its own path,
and they do not block each other.

## Important: DMA has no storage size

A common confusion: the DMA is **not a box** and has **no storage capacity**. It
is a **delivery truck** (a transfer method), measured by **how fast it moves**,
not by how much it holds.

- The **FIFO** is storage → measured in samples (e.g. 4,096).
- The **DMA** is transport → measured in speed (MB per second).

Asking "how many samples does the DMA hold?" is like asking "how much fuel does
a car carry per kilometre?" — the wrong kind of question. The right question is
its speed, which is limited by the road (the bus) in the next step.

## The key role of DMA

Without DMA, measuring 14 million samples per second would be **impossible** —
the CPU would freeze. DMA is the reason:
- the CPU stays free to run Python and draw the graph,
- data moves at high speed in the background,
- the small FIFO box gets emptied fast enough that it does not overflow.

---

# STEP 8 — The bus (the road — the real bottleneck)

## What a bus is

A **bus** is the **road** that data travels on, from one place to another.

Picture a highway between two cities:
- City 1 = the **card** (PXIe-6386)
- City 2 = the **computer** (RAM and CPU)

All the data the DMA truck carries drives on this road to reach the computer.

## The name and type of our road

The card connects to the computer through a type of road called **PXI Express**.

```
Form factor: x1 PXI Express peripheral module
```

The **x1** is the key to the whole story.

## What "x1" means — the number of lanes

A highway can have 1 lane, 4 lanes, 8, or 16. More lanes = more cars pass at
once = higher transfer speed.

- **x1** = 1 lane
- **x4** = 4 lanes
- **x8** = 8 lanes
- **x16** = 16 lanes

Our card is **x1 — only one lane**. This is the slowest type.

> NI spec: **Slot compatibility: x1 and x4 PXI Express or PXI Express hybrid
> slots.** You can plug it into an x4 slot, but it still uses only one lane,
> because that is its design.

## The road's maximum speed

This is the most important number in the whole topic. NI states it directly:

```
theoretical bandwidth specification of 250 MB/s
```

So the road (one lane) can carry at most **250 megabytes per second**. That is
the ceiling. No matter what you do, it will not move faster than this.

Picture a tap with a maximum flow. However wide you open it, it cannot exceed a
certain amount per second.

## Is that enough? Let's calculate

Each sample is **2 bytes** (because the ADC is 16-bit).

**Scenario 1 — one channel at top speed**
```
1 channel × 14.29 million samples/s × 2 bytes = 28.6 MB/s
```
The road holds 250. We use only 28.6. **No problem at all** ✅ (road mostly empty)

**Scenario 2 — all 8 channels at top speed**
```
8 channels × 14.29 million samples/s × 2 bytes = 228.6 MB/s
```
The road holds 250. We use 228.6. **This nearly fills the whole road!** ⚠️

With 8 channels we are right at the edge of the ceiling. Any extra load and the
road chokes, and data starts to be lost.

## This is why NI itself warns you

This is not my opinion — it is NI's official text:

> **Tasks using multiple channels at higher sample rates may experience buffer
> errors.**

And a reassuring note:

> **In general, the application areas that would require 15 MS/s do not require
> continuous streaming.**

So if you need the maximum speed, you usually record for a short time, not for
hours.

## The core point for the project

This is the most important sentence to remember for the defense:

> **At high speeds with many channels, the limit is not my Python code — the
> limit is the road (the bus) itself, because it is physically one lane at
> 250 MB/s.**

This separates two kinds of data loss:
- If the road chokes → that is a **physical / hardware** limit; no code can fix it.
- If Python lags while the road is free → that is a **software** limit; code can
  improve it.

## Why the bus is the bottleneck

Everything before the road is fast, and everything after it is wide — but the
road itself is narrow:

```
ADC very fast ✅
FIFO absorbs shocks ✅
DMA fast truck ✅
        ↓
   but... 🚦
        ↓
the road (bus) = one lane, 250 MB/s  ← the traffic jam is here!
        ↓
RAM is large ✅
```

Like a wide highway that suddenly narrows to one lane at a bridge — the jam
happens at the bridge.

## If you ever use several cards

NI gives a useful warning for multiple cards: if you had 5 PXIe-6386 modules all
sampling at 12.5 MS/s, that would add up to about 1 GB/s — maxing out the shared
link back to the controller. You have **two** 6386 cards in the chassis, so keep
this in mind if you ever run both at maximum speed at the same time, since they
share the larger road back to the CPU.

---

# STEP 9 — The host buffer (the big box in RAM)

## What it is

"Host" means the **computer itself** (the PXI PC). So the **Host Buffer** is the
**big box in the computer's RAM**.

We now have **two different boxes** in the journey — do not mix them up:

| Box | Location | Your measured size |
|-----|----------|--------------------|
| **FIFO** | on the card | ~12,000 samples |
| **Host Buffer** | in the PC's RAM | ~1,000,000 samples |

## Why two boxes? Why not one?

Each box solves a different problem:

```
Card → [FIFO] → DMA truck → [Host Buffer] → Python
        small box   the road    big box
        on card                 in RAM
```

- The **small box (FIFO)** absorbs the timing of the **road (bus)** — tiny
  delays of the DMA. Small because transfer is fast.
- The **big box (Host Buffer)** absorbs the timing of **Windows and Python** —
  and this is the one that must be large.

## Why the host buffer is so big (a million samples)

Windows is **not** a real-time system. It can be **late** for a moment because it
went to do something else (an update, another program). Python can also pause for
a moment.

During the moment Python is not reading, the data must go **somewhere** to wait.
That somewhere is the big Host Buffer.

How long does a million samples cover?

```
At 1 million samples/second:
1,000,000 ÷ 1,000,000 = 1 full second!
```

So the big box gives Python **a whole second** of breathing room — compared to
the tiny FIFO's third of a thousandth of a second.

## Simple comparison of the two boxes

Picture a factory:
- **FIFO** = a small basin next to the machine. Holds products for a moment until
  the truck takes them.
- **Host Buffer** = a large warehouse in the factory. Stores products for a long
  time until the workers can process them.

Both are needed. The small basin keeps the machine from stalling; the large
warehouse covers the case where the workers fall behind.

## Who sets the host buffer size?

**You do!** In Python (the `nidaqmx` library) you can make the host buffer larger
or smaller.

- Bigger box = more breathing room for Python = safer against data loss
- But it uses more RAM

The million samples you measured is most likely the default size the driver chose
based on the rate you requested. This is something you will tune a lot in WP3
when preventing data loss.

---

# STEP 10 — Python reads the number

When you call `task.read()` in Python, it copies samples out of the host buffer.
The driver has already converted the raw 16-bit step numbers back into volts.

You see `0.49998...` — and the journey is complete. 🎉

---

# The whole chain on one line

```
Chip (0.5 V)
  → AI+ / AI- input pins        (differential — removes noise by subtraction)
  → Sample-and-Hold             (SIMULTANEOUS — one ADC per channel, zero skew)
  → 16-bit ADC                  (successive approximation; 30.5 µV/step on ±1 V)
  → Sample clock                (drum from 100 MHz; 14.29 MS/s max, 20 kS/s min)
  → Onboard FIFO                (small shock absorber: 4,096/ch + 8,191 shared)
  → DMA engine                  (the delivery truck; 8 channels; no CPU needed)
  → PXIe bus                    (the road: x1, 250 MB/s — THE bottleneck)
  → Host buffer in RAM          (big box: ~1,000,000 samples ≈ 1 second)
  → Python task.read()          (back to volts: 0.49998)
```

---

# Where data can be lost (the core of the project)

There are exactly **two** places data can be lost, with different causes:

| Stage | Buffer | Headroom | Overflows when... |
|-------|--------|----------|-------------------|
| Card → bus | Onboard FIFO | ~0.29 ms/channel | the bus cannot drain it fast enough (rate too high) |
| Bus → app | Host buffer (RAM) | ~1 second | Python/Windows cannot read it fast enough |

- A **FIFO overflow** is a *hardware / bus* limit.
- A **host buffer overflow** is a *software / operating system* limit.

The error we triggered earlier (**-200279**) was the second kind — Python could
not empty the big box fast enough. NI's bandwidth warning is about the first kind.

---

# Voltage and current limits (safety)

It is important to separate three different things:

### 1. Normal measurement range (Input Range)
```
±1 V   |   ±2 V   |   ±5 V   |   ±10 V
```
The most you can measure accurately is ±10 V (on the largest range). There is
**no minimum voltage** — it can measure very small voltages, down to about one
step (30.5 µV). Anything beyond ±10 V will not be read correctly.

### 2. Maximum safe voltage (Maximum Working Voltage)
```
±11 V for all ranges (Measurement Category I)
```
Above ±11 V, accuracy on the other channels starts to degrade (but the card is
still safe).

### 3. Damage voltage (Overvoltage Protection)
| State | Safe limit |
|-------|------------|
| Device ON | ±36 V |
| Device OFF | ±15 V |

Note: when the card is **off**, its protection is weaker (±15 V only). Do not
connect a high voltage while it is off.

### 4. Current
The card's input is **voltage**, not current, so it draws an extremely tiny
current from the chip:
```
Input bias current: ±10 pA  (a fraction of a trillionth of an amp)
```
This means the card barely affects the chip — which is good. The maximum current
during a dangerous overvoltage condition is:
```
Input current during overvoltage: ±10 mA max per AI pin
```

---

# Key specifications summary (for citation)

| Specification | Value |
|---|---|
| Analog input channels | 8 differential |
| ADC resolution | 16 bits |
| Sampling type | Simultaneous (one ADC per channel) |
| Max sample rate (internal clock) | 14.29 MS/s per channel |
| Max sample rate (external clock) | 15 MS/s per channel |
| Minimum sample rate | 20 kS/s |
| Input ranges | ±1 V, ±2 V, ±5 V, ±10 V |
| Resolution on ±1 V range | ~30.5 µV per step |
| Absolute accuracy at full scale (±1 V) | ~219 µV |
| Onboard FIFO | 4,096 samples/channel + 8,191 shared (~12,287 for one channel) |
| Data transfer | DMA (scatter-gather), 8 DMA channels |
| Bus connection | PXI Express Gen 1 x1 (~250 MB/s) — the bottleneck |
| Timing accuracy | 50 ppm of sample rate |
| Timing resolution | 10 ns |
| Master clock (timebase) | 100 MHz |
| Input impedance | >100 GΩ |
| Input bias current | ±10 pA |
| CMRR (DC to 60 Hz) | 70 dB |
| Max working voltage | ±11 V |
| Overvoltage protection (on / off) | ±36 V / ±15 V |
| Warm-up time | 15 minutes |
| Calibration interval | 2 years |

*All values from the official NI PXIe-6386 Specifications and the NI
Supplementary Information document (links at the top of this file). The internal
voltage reference value is proprietary and not published by NI.*
