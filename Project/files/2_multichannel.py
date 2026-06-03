"""
SCRIPT 2: Multi-Channel Signal Plotting
=========================================
Your PXI system has 16 analog input channels.
This simulates reading from 4 channels and plotting them.

Run this: python 2_multichannel.py
"""
import numpy as np
import matplotlib.pyplot as plt

# --- STEP 1: Set up acquisition parameters ---
sample_rate = 10000    # 10 kHz
duration = 0.05        # 50 ms
num_samples = int(sample_rate * duration)  # 500 samples

t = np.linspace(0, duration, num_samples, endpoint=False)
t_ms = t * 1000  # convert to milliseconds

print(f"Simulating 4-channel acquisition")
print(f"Sample rate: {sample_rate} Hz")
print(f"Duration: {duration * 1000} ms")
print(f"Samples per channel: {num_samples}")
print()

# --- STEP 2: Simulate 4 channels with different signals ---
# In real life, these come from task.read() on the PXI system
# Here we generate them manually to practice

# Channel 0: 100 Hz sine (like a basic sensor signal)
ch0 = 2.0 * np.sin(2 * np.pi * 100 * t)

# Channel 1: 250 Hz sine with some noise (realistic measurement)
noise = np.random.normal(0, 0.3, num_samples)
ch1 = 1.5 * np.sin(2 * np.pi * 250 * t) + noise

# Channel 2: Square wave at 200 Hz (like a digital-ish signal)
ch2 = 3.0 * np.sign(np.sin(2 * np.pi * 200 * t))

# Channel 3: Sum of two frequencies (complex signal)
ch3 = 1.0 * np.sin(2 * np.pi * 150 * t) + 0.5 * np.sin(2 * np.pi * 400 * t)

# Store in a dictionary (like real DAQ data)
channels = {
    "Dev1/ai0": ch0,
    "Dev1/ai1": ch1,
    "Dev1/ai2": ch2,
    "Dev1/ai3": ch3,
}

# --- STEP 3: Print statistics for each channel ---
print("Channel Statistics:")
print("-" * 55)
for name, data in channels.items():
    mean = np.mean(data)
    rms = np.sqrt(np.mean(data**2))
    peak = np.max(np.abs(data))
    print(f"  {name}: mean={mean:+.4f} V, RMS={rms:.4f} V, peak={peak:.4f} V")
print()

# --- STEP 4: Plot all channels (stacked subplots) ---
# This is exactly how you'll display real-time data in WP3

fig, axes = plt.subplots(4, 1, figsize=(12, 8), sharex=True)

colors = ['#028090', '#E07C24', '#6D2E46', '#2C5F2D']
labels = [
    "100 Hz Sine",
    "250 Hz Sine + Noise",
    "200 Hz Square",
    "150 Hz + 400 Hz Mix",
]

for i, (ax, (name, data)) in enumerate(zip(axes, channels.items())):
    ax.plot(t_ms, data, color=colors[i], linewidth=0.8)
    ax.set_ylabel(f"{name}\n(V)", fontsize=9)
    ax.set_ylim(-4, 4)
    ax.grid(True, alpha=0.3)
    ax.legend([labels[i]], loc='upper right', fontsize=9)
    
    # Add RMS value as text
    rms = np.sqrt(np.mean(data**2))
    ax.text(0.01, 0.95, f"RMS: {rms:.3f} V",
            transform=ax.transAxes, fontsize=9,
            verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

axes[-1].set_xlabel("Time (ms)", fontsize=11)
axes[0].set_title("4-Channel PXI Acquisition (Simulated)", fontsize=14, fontweight='bold')

plt.tight_layout()
plt.show()

print("\n--- DONE! ---")
print("\nIn your project, replace the generated signals with:")
print("  with nidaqmx.Task() as task:")
print('      task.ai_channels.add_ai_voltage_chan("Dev1/ai0:3")')
print("      task.timing.cfg_samp_clk_timing(10000)")
print("      data = task.read(500)  # returns a 2D list")
