"""
SCRIPT 4: Threading vs Multiprocessing — Which is Better?
==========================================================
Your supervisor asked: which approach is more efficient?
This script compares both and explains when to use which.

Run this: python step4_threading_vs_multiprocessing.py
"""
import numpy as np
import threading
import multiprocessing
import queue
import time


print("=" * 60)
print("Threading vs Multiprocessing — What's the Difference?")
print("=" * 60)
print("""
THREADING:
  - Multiple threads share the SAME memory
  - Only ONE thread runs Python code at a time (due to the GIL)
  - Great for I/O tasks (reading from hardware, waiting for data)
  - Low overhead (fast to create, easy to share data)

  Thread 1 ──┐
  Thread 2 ──┤── Same memory space (same process)
  Thread 3 ──┘

MULTIPROCESSING:
  - Each process has its OWN separate memory
  - TRUE parallel execution on multiple CPU cores
  - Great for heavy calculations (math on large arrays)
  - Higher overhead (slow to create, must copy data between processes)

  Process 1 ── [own memory]  ── CPU Core 1
  Process 2 ── [own memory]  ── CPU Core 2
  Process 3 ── [own memory]  ── CPU Core 3
""")

input("Press Enter to run the comparison tests...\n")


# ===================================================================
# TEST 1: I/O-Bound Task (Reading Data)
# ===================================================================

print("=" * 60)
print("TEST 1: I/O-Bound Task (simulating hardware read)")
print("=" * 60)
print("This simulates reading data from the PXI card.\n")

def io_task(task_id, duration=0.05):
    """Simulates waiting for hardware (I/O-bound)."""
    time.sleep(duration)  # Simulates waiting for DAQ hardware
    return task_id

num_tasks = 20

# Sequential
start = time.time()
for i in range(num_tasks):
    io_task(i)
sequential_time = time.time() - start
print(f"  Sequential:      {sequential_time:.3f} s")

# Threading
start = time.time()
threads = []
for i in range(num_tasks):
    t = threading.Thread(target=io_task, args=(i,))
    threads.append(t)
    t.start()
for t in threads:
    t.join()
threading_time = time.time() - start
print(f"  Threading:       {threading_time:.3f} s "
      f"({sequential_time/threading_time:.1f}x faster)")

# Multiprocessing
start = time.time()
processes = []
for i in range(num_tasks):
    p = multiprocessing.Process(target=io_task, args=(i,))
    processes.append(p)
    p.start()
for p in processes:
    p.join()
multiprocessing_time = time.time() - start
print(f"  Multiprocessing: {multiprocessing_time:.3f} s "
      f"({sequential_time/multiprocessing_time:.1f}x faster)")

print(f"\n  Winner for I/O tasks: ", end="")
if threading_time < multiprocessing_time:
    print("THREADING ✓ (lower overhead for I/O)")
else:
    print("MULTIPROCESSING ✓")
print()

input("Press Enter for Test 2...\n")


# ===================================================================
# TEST 2: CPU-Bound Task (Processing Data)
# ===================================================================

print("=" * 60)
print("TEST 2: CPU-Bound Task (heavy math on data)")
print("=" * 60)
print("This simulates processing acquired data (FFT, RMS, filtering).\n")

def cpu_task(data):
    """Simulates heavy data processing (CPU-bound)."""
    # Calculate RMS
    rms = np.sqrt(np.mean(data**2))
    # Simple filtering (moving average)
    filtered = np.convolve(data, np.ones(10)/10, mode='valid')
    # Find peaks
    peaks = np.where(np.diff(np.sign(np.diff(data))) < 0)[0]
    return rms, len(peaks)

# Create test datasets
datasets = [np.random.randn(100000) for _ in range(10)]

# Sequential
start = time.time()
for d in datasets:
    cpu_task(d)
sequential_time = time.time() - start
print(f"  Sequential:      {sequential_time:.3f} s")

# Threading
start = time.time()
threads = []
for d in datasets:
    t = threading.Thread(target=cpu_task, args=(d,))
    threads.append(t)
    t.start()
for t in threads:
    t.join()
threading_time = time.time() - start
print(f"  Threading:       {threading_time:.3f} s "
      f"({sequential_time/threading_time:.1f}x faster)")

# Multiprocessing
start = time.time()
processes = []
for d in datasets:
    p = multiprocessing.Process(target=cpu_task, args=(d,))
    processes.append(p)
    p.start()
for p in processes:
    p.join()
multiprocessing_time = time.time() - start
print(f"  Multiprocessing: {multiprocessing_time:.3f} s "
      f"({sequential_time/multiprocessing_time:.1f}x faster)")

print(f"\n  Winner for CPU tasks: ", end="")
if multiprocessing_time < threading_time:
    print("MULTIPROCESSING ✓ (bypasses GIL for true parallelism)")
else:
    print("THREADING ✓ (overhead of multiprocessing outweighed benefit)")


# ===================================================================
# CONCLUSION FOR YOUR PXI PROJECT
# ===================================================================

print(f"""

{'=' * 60}
CONCLUSION: What Should You Use in Your PXI Project?
{'=' * 60}

Your project has 3 main tasks running at the same time:

  ┌──────────────────────────────────────────────────────┐
  │ Task 1: READ data from PXI hardware  →  I/O-bound   │
  │         (waiting for hardware to deliver data)       │
  │                                                      │
  │ Task 2: PLOT data in real-time       →  I/O-bound   │
  │         (sending pixels to screen)                   │
  │                                                      │
  │ Task 3: SAVE data to disk            →  I/O-bound   │
  │         (writing to hard drive)                      │
  └──────────────────────────────────────────────────────┘

  All three are I/O-bound! → THREADING is the better choice.

  Why not multiprocessing?
  ┌──────────────────────────────────────────────────────┐
  │ Problem 1: Each process has its OWN memory.          │
  │   → You can't share the hardware connection.         │
  │   → You'd have to disconnect and reconnect the PXI  │
  │     device, which causes a gap in data acquisition.  │
  │                                                      │
  │ Problem 2: Higher overhead.                          │
  │   → Creating processes is slower than threads.       │
  │   → Copying data between processes takes time.       │
  │                                                      │
  │ Problem 3: Ahmad's thesis confirmed this.            │
  │   → He tried multiprocessing but switched to         │
  │     threading because reconnecting the device        │
  │     caused voltage gaps that damaged the sensor.     │
  └──────────────────────────────────────────────────────┘

  RECOMMENDED ARCHITECTURE for your project:

  ┌─────────────────┐
  │  READER THREAD   │ ← reads from PXI, puts in queue
  │  (highest speed) │
  └────────┬─────────┘
           │
     ┌─────▼──────┐
     │   QUEUE 1   │ ← thread-safe buffer (shock absorber)
     └─────┬───────┘
           │
     ┌─────▼───────────────┐
     │  PROCESSOR THREAD    │ ← takes from queue
     │  - plot in real-time │
     │  - calculate RMS     │
     │  - detect events     │
     └─────┬───────────────┘
           │
     ┌─────▼──────┐
     │   QUEUE 2   │ ← another queue for saving
     └─────┬───────┘
           │
     ┌─────▼───────────┐
     │  SAVER THREAD    │ ← writes data to disk
     │  (can be slower) │
     └─────────────────┘

  This is exactly what Ahmad Ahmad used in his thesis,
  and it's the standard pattern for real-time DAQ systems.
""")
