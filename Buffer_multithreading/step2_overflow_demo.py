"""
SCRIPT 2: Serial Data Stream — Seeing Buffer Overflow Happen
==============================================================
This simulates your PXI card streaming data continuously.
We save simulated data to a file, then try to read and process
it in real-time — showing exactly where overflow happens.

Run this: python step2_overflow_demo.py
"""
import numpy as np
import time
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


print("=" * 60)
print("PART 1: Creating a Simulated Dataset")
print("=" * 60)

# --- Create a simulated signal and save it to a file ---
# This represents data that the PXI card would produce

sample_rate = 100000   # 100 kHz (100,000 samples per second)
duration = 5           # 5 seconds of data
total_samples = sample_rate * duration  # = 500,000 samples

print(f"Generating {total_samples:,} samples at {sample_rate/1000:.0f} kHz...")
print(f"Duration: {duration} seconds")

t = np.linspace(0, duration, total_samples, endpoint=False)

# Create a realistic signal: sine + noise
signal = (2.0 * np.sin(2 * np.pi * 50 * t) +       # 50 Hz main signal
          0.5 * np.sin(2 * np.pi * 200 * t) +       # 200 Hz harmonic
          np.random.normal(0, 0.2, total_samples))    # noise

# Save to file (simulating recorded PXI data)
np.save("simulated_pxi_data.npy", signal)
print(f"Saved to: simulated_pxi_data.npy ({signal.nbytes / 1024:.0f} KB)")
print()

input("Press Enter to simulate reading this data with a buffer...\n")


# ===================================================================
# PART 2: The SLOW way — read, process, plot ONE AT A TIME
# ===================================================================

print("=" * 60)
print("PART 2: Single-Thread Processing (THE PROBLEM)")
print("=" * 60)
print("""
This simulates what happens when your program does everything
in a single thread:

  1. Read a chunk from hardware (buffer)
  2. Process the data (convert voltage to current, calculate RMS)
  3. Update the plot
  4. Go back to step 1

The problem: steps 2 and 3 take time. While your program is
busy processing and plotting, the buffer keeps filling up!
""")

input("Press Enter to run the simulation...\n")

# Load the data (simulating hardware producing data)
all_data = np.load("simulated_pxi_data.npy")

# Buffer settings
buffer_max_size = 10000    # Buffer can hold 10,000 samples
chunk_size = 5000          # Hardware delivers 5,000 samples at a time
read_interval = chunk_size / sample_rate  # Time between chunks

# Simulation
buffer_fill = 0
total_read = 0
total_lost = 0
data_pointer = 0  # Where we are in the file

processing_times = []
buffer_levels = []
lost_events = []

print(f"Buffer size: {buffer_max_size:,} samples")
print(f"Chunk size: {chunk_size:,} samples")
print(f"Chunk arrives every: {read_interval*1000:.1f} ms")
print(f"{'—' * 60}")
print()

step = 0
while data_pointer < len(all_data):
    step += 1
    
    # --- HARDWARE SIDE: new data arrives ---
    new_samples = min(chunk_size, len(all_data) - data_pointer)
    space_left = buffer_max_size - buffer_fill
    
    if new_samples > space_left:
        lost = new_samples - space_left
        total_lost += lost
        buffer_fill = buffer_max_size
        lost_events.append((step, lost))
    else:
        lost = 0
        buffer_fill += new_samples
    
    # --- SOFTWARE SIDE: read from buffer ---
    chunk = all_data[data_pointer:data_pointer + new_samples]
    data_pointer += new_samples
    
    # --- SOFTWARE SIDE: process the data (takes time!) ---
    process_start = time.time()
    
    rms = np.sqrt(np.mean(chunk**2))       # Calculate RMS
    peak = np.max(np.abs(chunk))            # Find peak
    mean = np.mean(chunk)                   # Calculate mean
    
    # Simulate slow plotting (this is what causes overflow!)
    # In real code, matplotlib is VERY slow for real-time updates
    time.sleep(0.02)  # Simulates 20ms of plotting time
    
    process_time = time.time() - process_start
    processing_times.append(process_time)
    
    # Now empty the buffer (we've read the data)
    buffer_fill = max(0, buffer_fill - new_samples)
    buffer_levels.append(buffer_fill)
    
    # Print status
    bar_len = 30
    fill_pct = (buffer_fill / buffer_max_size) * 100
    filled = int(fill_pct / (100 / bar_len))
    bar = "█" * filled + "░" * (bar_len - filled)
    
    overflow_marker = " ⚠️  OVERFLOW!" if lost > 0 else ""
    
    if step <= 20 or step % 10 == 0 or lost > 0:
        print(f"  Chunk {step:3d}: [{bar}] {fill_pct:5.1f}% | "
              f"Process: {process_time*1000:5.1f}ms | "
              f"RMS: {rms:.3f}V{overflow_marker}")
    
    total_read += new_samples

print(f"\n{'—' * 60}")
print(f"RESULTS:")
print(f"  Total samples generated: {len(all_data):,}")
print(f"  Total samples read:      {total_read:,}")
print(f"  Total samples LOST:      {total_lost:,}")
if total_lost > 0:
    print(f"  Data loss rate:          {total_lost/len(all_data)*100:.2f}%")
    print(f"  Overflow events:         {len(lost_events)}")
else:
    print(f"  Data loss rate:          0% ✓")
print(f"  Avg processing time:    {np.mean(processing_times)*1000:.1f} ms")
print(f"  Max processing time:    {np.max(processing_times)*1000:.1f} ms")

# Save a plot of buffer levels over time
fig, axes = plt.subplots(2, 1, figsize=(12, 6))

# Top: the signal
axes[0].plot(t[:50000], all_data[:50000], linewidth=0.3, color='#028090')
axes[0].set_ylabel("Voltage (V)")
axes[0].set_title("Signal Data (first 0.5 seconds)")
axes[0].grid(True, alpha=0.3)

# Bottom: buffer level over time
axes[1].plot(buffer_levels, linewidth=1, color='#E07C24')
axes[1].axhline(y=buffer_max_size, color='red', linestyle='--',
                linewidth=1, label='Buffer MAX')
axes[1].set_xlabel("Chunk number")
axes[1].set_ylabel("Buffer fill (samples)")
axes[1].set_title("Buffer Level Over Time (higher = closer to overflow)")
axes[1].legend()
axes[1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig("plot_buffer_overflow.png", dpi=150)
plt.close()
print(f"\nSaved plot: plot_buffer_overflow.png")

print("""
╔══════════════════════════════════════════════════════════════╗
║  WHAT HAPPENED:                                              ║
║                                                              ║
║  Our program tried to do everything sequentially:            ║
║    Read → Process → Plot → Read → Process → Plot → ...      ║
║                                                              ║
║  But "Process" and "Plot" take time (20+ ms each).           ║
║  During that time, the hardware keeps sending data.          ║
║  The buffer fills up → OVERFLOW → DATA LOST.                 ║
║                                                              ║
║  SOLUTION: Use separate threads!                             ║
║    Thread 1: Read data as fast as possible                   ║
║    Thread 2: Process and plot (can be slower)                ║
║    A Queue connects them safely.                             ║
║                                                              ║
║  → Run step3_threading_fix.py to see the solution!           ║
╚══════════════════════════════════════════════════════════════╝
""")
