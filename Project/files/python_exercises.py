"""
============================================================================
Python Practice Exercises for PXI Data Acquisition Project
============================================================================
Author: Samir Elsherbiny
Course: Bachelor Project - PXI DAQ System Interface
University of Freiburg / Hahn-Schickard

Work through these exercises IN ORDER. Each one builds skills you'll
directly use in your project. Run each exercise, understand the output,
then try the "YOUR TURN" challenges.

Requirements: pip install numpy matplotlib
============================================================================
"""

# ============================================================================
# LEVEL 1: PYTHON BASICS
# ============================================================================

# --- Exercise 1.1: Variables and Data Types ---
# In DAQ, you constantly work with numbers (voltages, sampling rates, etc.)

print("=" * 60)
print("EXERCISE 1.1: Variables and Data Types")
print("=" * 60)

# These are the specs of your PXI system
num_ai_cards = 2           # integer
channels_per_card = 8      # integer
max_sample_rate = 14e6     # float (14 MS/s = 14,000,000)
system_name = "PXI-1042Q"  # string
is_connected = True        # boolean

print(f"System: {system_name}")
print(f"Total AI channels: {num_ai_cards * channels_per_card}")
print(f"Max sample rate: {max_sample_rate / 1e6} MS/s")
print(f"Connected: {is_connected}")

# YOUR TURN: Add variables for analog output channels (2) and digital I/O
# lines (8), then print the total number of all channels.
# Write your code below:
# ...


# --- Exercise 1.2: Lists ---
# You'll store channel names, voltage readings, and sample data in lists

print("\n" + "=" * 60)
print("EXERCISE 1.2: Lists")
print("=" * 60)

# Channel names on a PXI card
channels = ["ai0", "ai1", "ai2", "ai3", "ai4", "ai5", "ai6", "ai7"]
print(f"All channels: {channels}")
print(f"First channel: {channels[0]}")
print(f"Last channel: {channels[-1]}")
print(f"Channels 0-3: {channels[:4]}")
print(f"Number of channels: {len(channels)}")

# Simulated voltage readings
voltages = [0.52, -1.23, 3.45, 0.01, -0.89, 2.11, -3.33, 1.67]
print(f"\nVoltage readings: {voltages}")
print(f"Max voltage: {max(voltages):.2f} V")
print(f"Min voltage: {min(voltages):.2f} V")

# YOUR TURN: Create a list of 5 sampling rates (e.g., 1000, 10000, 100000,
# 1000000, 14000000). Print each one formatted as "X kS/s" or "X MS/s".
# Write your code below:
# ...


# --- Exercise 1.3: Dictionaries ---
# Perfect for storing configuration parameters

print("\n" + "=" * 60)
print("EXERCISE 1.3: Dictionaries")
print("=" * 60)

# DAQ configuration as a dictionary
daq_config = {
    "device": "Dev1",
    "channels": ["ai0", "ai1"],
    "sample_rate": 1000.0,
    "num_samples": 100,
    "voltage_range": (-10.0, 10.0),
    "mode": "finite"
}

print(f"Device: {daq_config['device']}")
print(f"Sample rate: {daq_config['sample_rate']} Hz")
print(f"Channels: {daq_config['channels']}")

# Accessing and modifying
daq_config["sample_rate"] = 5000.0
print(f"Updated sample rate: {daq_config['sample_rate']} Hz")

# Loop through all settings
print("\nFull configuration:")
for key, value in daq_config.items():
    print(f"  {key}: {value}")

# YOUR TURN: Create a dictionary for a waveform generator config with keys:
# "waveform_type" (sine), "frequency" (1000), "amplitude" (2.5),
# "offset" (0.0), "channel" ("ao0"). Print all settings.
# Write your code below:
# ...


# --- Exercise 1.4: Loops and Conditionals ---
# Used everywhere: processing samples, checking thresholds, etc.

print("\n" + "=" * 60)
print("EXERCISE 1.4: Loops and Conditionals")
print("=" * 60)

# Simulate checking voltage readings against a threshold
voltages = [0.52, -1.23, 3.45, 0.01, -0.89, 2.11, -3.33, 1.67]
threshold = 2.0

print(f"Threshold: ±{threshold} V")
for i, v in enumerate(voltages):
    if abs(v) > threshold:
        print(f"  WARNING: Channel ai{i} = {v:.2f} V (exceeds threshold!)")
    else:
        print(f"  OK: Channel ai{i} = {v:.2f} V")

# Counting samples above threshold
count = sum(1 for v in voltages if abs(v) > threshold)
print(f"\n{count} out of {len(voltages)} channels exceed threshold")

# YOUR TURN: Write a loop that simulates checking if a buffer is full.
# Start with buffer_size = 0, max_buffer = 1000. In each iteration,
# add 150 samples. Print the buffer fill percentage. When the buffer
# exceeds max_buffer, print "BUFFER OVERFLOW!" and break.
# Write your code below:
# ...


# --- Exercise 1.5: Functions ---
# You'll write MANY functions in your project

print("\n" + "=" * 60)
print("EXERCISE 1.5: Functions")
print("=" * 60)

def voltage_to_current(voltage, gain):
    """Convert voltage reading to current based on amplifier gain."""
    return voltage / gain

def format_sample_rate(rate_hz):
    """Format a sampling rate in Hz to a readable string."""
    if rate_hz >= 1e6:
        return f"{rate_hz / 1e6:.1f} MS/s"
    elif rate_hz >= 1e3:
        return f"{rate_hz / 1e3:.1f} kS/s"
    else:
        return f"{rate_hz:.0f} S/s"

def calculate_acquisition_time(num_samples, sample_rate):
    """Calculate how long an acquisition will take."""
    time_sec = num_samples / sample_rate
    if time_sec < 1:
        return f"{time_sec * 1000:.1f} ms"
    else:
        return f"{time_sec:.2f} s"

# Using the functions
voltage = 2.5
gain = 1000
current = voltage_to_current(voltage, gain)
print(f"Voltage: {voltage} V -> Current: {current * 1e3:.2f} mA (gain={gain})")

for rate in [500, 10000, 1000000, 14000000]:
    print(f"  {rate} Hz = {format_sample_rate(rate)}")

print(f"\nAcquisition time: {calculate_acquisition_time(10000, 1000000)}")
print(f"Acquisition time: {calculate_acquisition_time(1000000, 14000000)}")

# YOUR TURN: Write a function called "channel_name_generator" that takes
# a device name (e.g., "Dev1") and number of channels (e.g., 8), and
# returns a list like ["Dev1/ai0", "Dev1/ai1", ..., "Dev1/ai7"].
# Test it with "Dev1" and 8 channels, then with "Dev2" and 4 channels.
# Write your code below:
# ...


# --- Exercise 1.6: The 'with' Statement (Context Managers) ---
# The nidaqmx API uses this pattern for EVERY task

print("\n" + "=" * 60)
print("EXERCISE 1.6: The 'with' Statement")
print("=" * 60)

# Writing data to a file (you'll save measurements this way)
data = [0.52, -1.23, 3.45, 0.01, -0.89]

with open("test_data.csv", "w") as f:
    f.write("sample_index,voltage\n")
    for i, v in enumerate(data):
        f.write(f"{i},{v:.4f}\n")
print("Data written to test_data.csv")

# Reading it back
with open("test_data.csv", "r") as f:
    content = f.read()
print(f"File content:\n{content}")

# This is EXACTLY how nidaqmx works:
# with nidaqmx.Task() as task:
#     task.ai_channels.add_ai_voltage_chan("Dev1/ai0")
#     data = task.read()
# Task is automatically cleaned up after the 'with' block

# YOUR TURN: Write a function "save_measurements" that takes a filename,
# a list of channel names, and a list of voltage readings. Save them
# to a CSV file with headers. Then read and print the file.
# Write your code below:
# ...


# ============================================================================
# LEVEL 2: NUMPY (Essential for DAQ data processing)
# ============================================================================

print("\n" + "=" * 60)
print("EXERCISE 2.1: NumPy Arrays")
print("=" * 60)

import numpy as np

# Creating arrays (much faster than lists for large data)
samples = np.array([0.52, -1.23, 3.45, 0.01, -0.89, 2.11, -3.33, 1.67])
print(f"Samples: {samples}")
print(f"Mean: {np.mean(samples):.4f} V")
print(f"Std Dev: {np.std(samples):.4f} V")
print(f"RMS: {np.sqrt(np.mean(samples**2)):.4f} V")

# Generating time arrays (you'll do this constantly)
sample_rate = 1000  # Hz
duration = 0.01     # seconds (10 ms)
num_points = int(sample_rate * duration)
t = np.linspace(0, duration, num_points, endpoint=False)
print(f"\nTime array: {num_points} points from 0 to {duration*1000} ms")
print(f"First 5 time values: {t[:5]}")
print(f"Time step: {t[1] - t[0]:.6f} s = {(t[1]-t[0])*1e6:.1f} µs")

# YOUR TURN: Create a time array for 1 second of data at 14 MS/s.
# How many points does it have? What is the time step in nanoseconds?
# Write your code below:
# ...


# --- Exercise 2.2: Generating Waveforms ---
# Your project requires generating sine, square, and ramp signals

print("\n" + "=" * 60)
print("EXERCISE 2.2: Generating Waveforms")
print("=" * 60)

sample_rate = 10000  # 10 kHz
duration = 0.01      # 10 ms
t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)

# Sine wave
freq = 500  # Hz
amplitude = 2.5  # Volts
sine_wave = amplitude * np.sin(2 * np.pi * freq * t)

# Square wave (using sign of sine)
square_wave = amplitude * np.sign(np.sin(2 * np.pi * freq * t))

# Ramp (sawtooth) wave
ramp_wave = amplitude * (2 * (t * freq % 1) - 1)

# Triangle wave
triangle_wave = amplitude * (2 * np.abs(2 * (t * freq % 1) - 1) - 1)

print(f"Generated 4 waveforms: {len(t)} points each")
print(f"  Frequency: {freq} Hz")
print(f"  Amplitude: {amplitude} V")
print(f"  Duration: {duration*1000} ms")

print(f"\nSine wave - min: {sine_wave.min():.2f}, max: {sine_wave.max():.2f}")
print(f"Square wave - min: {square_wave.min():.2f}, max: {square_wave.max():.2f}")
print(f"Ramp wave - min: {ramp_wave.min():.2f}, max: {ramp_wave.max():.2f}")

# YOUR TURN: Write a function "generate_waveform(waveform_type, freq,
# amplitude, sample_rate, duration)" that returns (time_array, waveform).
# waveform_type should be "sine", "square", "ramp", or "triangle".
# Test it with different parameters.
# Write your code below:
# ...


# --- Exercise 2.3: Array Operations (Data Processing) ---

print("\n" + "=" * 60)
print("EXERCISE 2.3: Array Operations")
print("=" * 60)

# Simulating noisy DAQ data
np.random.seed(42)
clean_signal = 2.0 * np.sin(2 * np.pi * 100 * t)
noise = np.random.normal(0, 0.3, len(t))
noisy_signal = clean_signal + noise

print(f"Clean signal RMS: {np.sqrt(np.mean(clean_signal**2)):.4f} V")
print(f"Noisy signal RMS: {np.sqrt(np.mean(noisy_signal**2)):.4f} V")
print(f"Noise RMS: {np.sqrt(np.mean(noise**2)):.4f} V")

# Simple moving average filter (you might use this for smoothing)
def moving_average(data, window_size):
    """Apply a simple moving average filter."""
    return np.convolve(data, np.ones(window_size)/window_size, mode='valid')

filtered = moving_average(noisy_signal, 5)
print(f"Filtered signal length: {len(filtered)} (lost {len(noisy_signal) - len(filtered)} points)")

# Multi-channel data (2D arrays)
# In DAQ, you often get data as [channels x samples] or [samples x channels]
num_channels = 4
num_samples = 100
multi_channel_data = np.random.randn(num_channels, num_samples) * 2.5

print(f"\nMulti-channel data shape: {multi_channel_data.shape}")
print(f"Channel 0 mean: {multi_channel_data[0].mean():.4f} V")
print(f"Channel 1 mean: {multi_channel_data[1].mean():.4f} V")
print(f"All channel means: {multi_channel_data.mean(axis=1)}")

# YOUR TURN: Generate a 16-channel dataset (simulating your 16 AI channels)
# where each channel has a sine wave at a different frequency
# (100 Hz, 200 Hz, 300 Hz, ... 1600 Hz). Calculate the peak-to-peak
# voltage for each channel.
# Write your code below:
# ...


# ============================================================================
# LEVEL 3: MATPLOTLIB (You need this for real-time visualization)
# ============================================================================

print("\n" + "=" * 60)
print("EXERCISE 3.1: Basic Plotting")
print("=" * 60)

import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for saving files
import matplotlib.pyplot as plt

# Generate test signals
sample_rate = 10000
duration = 0.02  # 20 ms
t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
signal = 2.5 * np.sin(2 * np.pi * 200 * t) + 0.5 * np.sin(2 * np.pi * 600 * t)

# Basic plot
fig, ax = plt.subplots(figsize=(10, 4))
ax.plot(t * 1000, signal, color='#028090', linewidth=0.8)
ax.set_xlabel("Time (ms)")
ax.set_ylabel("Voltage (V)")
ax.set_title("Analog Input Signal")
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig("plot_basic_signal.png", dpi=150)
plt.close()
print("Saved: plot_basic_signal.png")


# --- Exercise 3.2: Multi-channel Plot ---

print("\n" + "=" * 60)
print("EXERCISE 3.2: Multi-Channel Plot")
print("=" * 60)

fig, axes = plt.subplots(4, 1, figsize=(10, 8), sharex=True)
frequencies = [100, 250, 500, 1000]
colors = ['#028090', '#E07C24', '#6D2E46', '#2C5F2D']

for i, (ax, freq, color) in enumerate(zip(axes, frequencies, colors)):
    signal = 2.0 * np.sin(2 * np.pi * freq * t)
    noise = np.random.normal(0, 0.2, len(t))
    ax.plot(t * 1000, signal + noise, color=color, linewidth=0.5, label=f"ai{i}")
    ax.set_ylabel(f"ai{i} (V)")
    ax.legend(loc='upper right')
    ax.grid(True, alpha=0.3)
    ax.set_ylim(-3, 3)

axes[-1].set_xlabel("Time (ms)")
axes[0].set_title("Multi-Channel DAQ Acquisition")
plt.tight_layout()
plt.savefig("plot_multichannel.png", dpi=150)
plt.close()
print("Saved: plot_multichannel.png")


# --- Exercise 3.3: Waveform Comparison Plot ---

print("\n" + "=" * 60)
print("EXERCISE 3.3: Waveform Comparison")
print("=" * 60)

freq = 200
amplitude = 3.0
sine = amplitude * np.sin(2 * np.pi * freq * t)
square = amplitude * np.sign(np.sin(2 * np.pi * freq * t))
ramp = amplitude * (2 * (t * freq % 1) - 1)
triangle = amplitude * (2 * np.abs(2 * (t * freq % 1) - 1) - 1)

fig, axes = plt.subplots(2, 2, figsize=(12, 6))
waveforms = [("Sine", sine), ("Square", square), ("Ramp", ramp), ("Triangle", triangle)]

for ax, (name, wave) in zip(axes.flat, waveforms):
    ax.plot(t * 1000, wave, color='#1E2761', linewidth=1)
    ax.set_title(name)
    ax.set_xlabel("Time (ms)")
    ax.set_ylabel("Voltage (V)")
    ax.grid(True, alpha=0.3)
    ax.set_ylim(-4, 4)

plt.suptitle(f"Waveform Types - {freq} Hz, {amplitude} V", fontsize=14)
plt.tight_layout()
plt.savefig("plot_waveforms.png", dpi=150)
plt.close()
print("Saved: plot_waveforms.png")

# YOUR TURN: Create a plot that shows a "before and after" filtering:
# top subplot = noisy signal, bottom subplot = filtered signal.
# Add labels, title, and grid.
# Write your code below:
# ...


# ============================================================================
# LEVEL 4: THREADING & QUEUES (Critical for real-time acquisition)
# ============================================================================

print("\n" + "=" * 60)
print("EXERCISE 4.1: Threading Basics")
print("=" * 60)

import threading
import time
import queue

# Simulating a DAQ producer-consumer pattern
# Producer = reads data from hardware
# Consumer = processes/displays the data

data_queue = queue.Queue()
stop_event = threading.Event()

def simulated_daq_reader(q, stop, sample_rate=1000, chunk_size=100):
    """Simulates reading data from a DAQ device."""
    sample_count = 0
    while not stop.is_set():
        # Simulate hardware read delay
        time.sleep(chunk_size / sample_rate)
        
        # Generate fake data (replace with real DAQ read later)
        t_start = sample_count / sample_rate
        t = np.linspace(t_start, t_start + chunk_size/sample_rate,
                        chunk_size, endpoint=False)
        data = 2.0 * np.sin(2 * np.pi * 50 * t) + np.random.normal(0, 0.1, chunk_size)
        
        q.put(data)
        sample_count += chunk_size

def simulated_data_processor(q, stop, results):
    """Simulates processing/displaying data."""
    total_samples = 0
    while not stop.is_set() or not q.empty():
        try:
            data = q.get(timeout=0.1)
            # Process the data
            rms = np.sqrt(np.mean(data**2))
            peak = np.max(np.abs(data))
            total_samples += len(data)
            results.append({"samples": total_samples, "rms": rms, "peak": peak})
        except queue.Empty:
            continue

# Run the simulation for 1 second
results = []
reader = threading.Thread(target=simulated_daq_reader,
                          args=(data_queue, stop_event, 1000, 100))
processor = threading.Thread(target=simulated_data_processor,
                             args=(data_queue, stop_event, results))

print("Starting simulated DAQ acquisition (1 second)...")
reader.start()
processor.start()

time.sleep(1.0)  # Run for 1 second
stop_event.set()  # Signal threads to stop

reader.join()
processor.join()

print(f"Acquisition complete!")
print(f"Total samples processed: {results[-1]['samples'] if results else 0}")
print(f"Last RMS: {results[-1]['rms']:.4f} V")
print(f"Queue items remaining: {data_queue.qsize()}")

# YOUR TURN: Modify the simulation to use 3 threads:
# 1. DAQ reader (producer)
# 2. Real-time plotter (consumer 1) - just prints RMS every 500ms
# 3. Data saver (consumer 2) - collects all data into a list
# Hint: Use the same queue, both consumers read from it.
# Actually, you'll need TWO queues - one for each consumer.
# Write your code below:
# ...


# ============================================================================
# LEVEL 5: PUTTING IT ALL TOGETHER
# ============================================================================

print("\n" + "=" * 60)
print("EXERCISE 5.1: Simulated DAQ System")
print("=" * 60)

class SimulatedPXISystem:
    """
    A simulated PXI system that mimics the nidaqmx API pattern.
    Practice with this until you get real hardware access.
    """
    
    def __init__(self, device_name="SimDev1"):
        self.device_name = device_name
        self.channels = []
        self.sample_rate = 1000.0
        self.num_samples = 100
        self.is_configured = False
        print(f"[{self.device_name}] Simulated PXI device created")
    
    def add_ai_channel(self, channel_name, min_val=-10.0, max_val=10.0):
        """Add an analog input channel (like task.ai_channels.add_ai_voltage_chan)"""
        self.channels.append({
            "name": channel_name,
            "min": min_val,
            "max": max_val,
            "type": "analog_input"
        })
        print(f"[{self.device_name}] Added AI channel: {channel_name} "
              f"(range: {min_val} to {max_val} V)")
    
    def configure_timing(self, sample_rate, num_samples):
        """Configure timing (like task.timing.cfg_samp_clk_timing)"""
        self.sample_rate = sample_rate
        self.num_samples = num_samples
        self.is_configured = True
        duration = num_samples / sample_rate
        print(f"[{self.device_name}] Timing configured: "
              f"{sample_rate} Hz, {num_samples} samples ({duration*1000:.1f} ms)")
    
    def read(self):
        """Read data from all channels (like task.read)"""
        if not self.is_configured:
            raise RuntimeError("Timing not configured! Call configure_timing() first.")
        
        t = np.linspace(0, self.num_samples / self.sample_rate,
                        self.num_samples, endpoint=False)
        
        data = {}
        for i, ch in enumerate(self.channels):
            # Generate fake signal: different frequency per channel
            freq = 100 * (i + 1)
            signal = (ch["max"] / 4) * np.sin(2 * np.pi * freq * t)
            noise = np.random.normal(0, 0.05, self.num_samples)
            data[ch["name"]] = signal + noise
        
        print(f"[{self.device_name}] Read {self.num_samples} samples "
              f"from {len(self.channels)} channels")
        return data
    
    def close(self):
        """Close the device"""
        print(f"[{self.device_name}] Device closed")

    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        self.close()


# Using the simulated system (SAME pattern as real nidaqmx!)
print("\n--- Running simulated acquisition ---\n")

with SimulatedPXISystem("SimDev1") as pxi:
    # Add channels
    pxi.add_ai_channel("SimDev1/ai0")
    pxi.add_ai_channel("SimDev1/ai1")
    pxi.add_ai_channel("SimDev1/ai2")
    pxi.add_ai_channel("SimDev1/ai3")
    
    # Configure timing
    pxi.configure_timing(sample_rate=10000, num_samples=1000)
    
    # Read data
    data = pxi.read()
    
    # Process results
    print("\nResults:")
    for ch_name, samples in data.items():
        print(f"  {ch_name}: mean={np.mean(samples):.4f} V, "
              f"RMS={np.sqrt(np.mean(samples**2)):.4f} V, "
              f"peak={np.max(np.abs(samples)):.4f} V")
    
    # Plot
    t = np.linspace(0, 1000/10000, 1000, endpoint=False)
    fig, ax = plt.subplots(figsize=(10, 4))
    for ch_name, samples in data.items():
        ax.plot(t * 1000, samples, linewidth=0.5, label=ch_name)
    ax.set_xlabel("Time (ms)")
    ax.set_ylabel("Voltage (V)")
    ax.set_title("Simulated 4-Channel PXI Acquisition")
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig("plot_simulated_pxi.png", dpi=150)
    plt.close()
    print("\nSaved: plot_simulated_pxi.png")

print("""
╔══════════════════════════════════════════════════════════╗
║  EXERCISES COMPLETE!                                     ║
║                                                          ║
║  Next steps:                                             ║
║  1. Go back and complete all "YOUR TURN" sections        ║
║  2. Modify the SimulatedPXISystem to add analog output   ║
║  3. Add a continuous acquisition mode                    ║
║  4. Try plotting with pyqtgraph instead of matplotlib    ║
║                                                          ║
║  When you get PXI access, replace SimulatedPXISystem     ║
║  with real nidaqmx.Task() calls - the pattern is the     ║
║  same!                                                   ║
╚══════════════════════════════════════════════════════════╝
""")
