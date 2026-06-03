"""
Generating Waveforms with NumPy
==========================================
This is what will be done in WP2 when generating test signals
for the analog output of the PXI system.

Run this: python 1_waveforms.py
"""
import numpy as np
import matplotlib.pyplot as plt

# --- STEP 1: Create a time array ---
# Think of this as the x-axis of your plot
# sample_rate = how many points per second (like your PXI card)
# duration = how long to record

sample_rate = 10000   # 10,000 samples per second (10 kHz)
duration = 0.02       # 0.02 seconds = 20 milliseconds
num_points = int(sample_rate * duration)  # = 200 points

# np.linspace creates evenly spaced numbers
# from 0 to 0.02, with 200 points
t = np.linspace(0, duration, num_points, endpoint=False)

print(f"Sample rate: {sample_rate} Hz")
print(f"Duration: {duration * 1000} ms")
print(f"Number of points: {num_points}")
print(f"Time step between samples: {(t[1]-t[0])*1e6:.1f} microseconds")
print(f"First 5 time values: {t[:5]}")
print()

# --- STEP 2: Generate a SINE wave ---
# Formula: amplitude * sin(2 * pi * frequency * time)
# This is the most basic signal in DAQ

freq = 200        # 200 Hz
amplitude = 2.5   # 2.5 Volts peak

sine_wave = amplitude * np.sin(2 * np.pi * freq * t)

print(f"Sine wave: {freq} Hz, {amplitude} V amplitude")
print(f"  Min value: {sine_wave.min():.2f} V")
print(f"  Max value: {sine_wave.max():.2f} V")
print(f"  First 5 values: {np.round(sine_wave[:5], 3)}")
print()

# --- STEP 3: Generate a SQUARE wave ---
# Just take the sign of the sine wave: +1 or -1
# np.sign() returns +1 for positive, -1 for negative

square_wave = amplitude * np.sign(np.sin(2 * np.pi * freq * t))

print(f"Square wave: {freq} Hz, {amplitude} V amplitude")
print(f"  Min value: {square_wave.min():.2f} V")
print(f"  Max value: {square_wave.max():.2f} V")
print(f"  Unique values: {np.unique(square_wave)}")
print()

# --- STEP 4: Generate a RAMP (sawtooth) wave ---
# Goes from -amplitude to +amplitude, then drops back
# Uses modulo (%) to create repeating pattern

ramp_wave = amplitude * (2 * (t * freq % 1) - 1)

print(f"Ramp wave: {freq} Hz, {amplitude} V amplitude")
print(f"  Min value: {ramp_wave.min():.2f} V")
print(f"  Max value: {ramp_wave.max():.2f} V")
print()

# --- STEP 5: Generate a TRIANGLE wave ---
# Like ramp but goes up AND down smoothly

triangle_wave = amplitude * (2 * np.abs(2 * (t * freq % 1) - 1) - 1)

print(f"Triangle wave: {freq} Hz, {amplitude} V amplitude")
print(f"  Min value: {triangle_wave.min():.2f} V")
print(f"  Max value: {triangle_wave.max():.2f} V")
print()

# --- STEP 6: Plot all 4 waveforms ---
# This opens a window on your screen!

fig, axes = plt.subplots(2, 2, figsize=(12, 7))

# Convert time to milliseconds for readability
t_ms = t * 1000

waveforms = [
    ("Sine Wave", sine_wave, "tab:blue"),
    ("Square Wave", square_wave, "tab:orange"),
    ("Ramp Wave", ramp_wave, "tab:green"),
    ("Triangle Wave", triangle_wave, "tab:red"),
]

for ax, (name, wave, color) in zip(axes.flat, waveforms):
    ax.plot(t_ms, wave, color=color, linewidth=1.5)
    ax.set_title(name, fontsize=13, fontweight='bold')
    ax.set_xlabel("Time (ms)")
    ax.set_ylabel("Voltage (V)")
    ax.set_ylim(-3.5, 3.5)
    ax.grid(True, alpha=0.3)
    ax.axhline(y=0, color='black', linewidth=0.5)

fig.suptitle(f"Waveform Generation — {freq} Hz, {amplitude} V amplitude",
             fontsize=15, fontweight='bold')
plt.tight_layout()
plt.show()  # <-- This opens the plot window!

print("\n--- DONE! Close the plot window to continue ---")
print("\nIn your PXI project, you'll send these arrays to the")
print("analog output card using: task.write(sine_wave)")
