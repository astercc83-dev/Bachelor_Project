"""
SCRIPT 3: Simulated PXI System (mimics nidaqmx API)
=====================================================
This class works EXACTLY like the real nidaqmx API.
When you get hardware access, you just swap this for nidaqmx.Task()

Run this: python 3_simulated_pxi.py
"""
import numpy as np
import matplotlib.pyplot as plt


# ===================================================================
# STEP 1: Understanding the SimulatedPXISystem class
# ===================================================================
# This is a Python CLASS - it groups related functions together.
# The real nidaqmx.Task() is also a class.
# Our class mimics its behavior so you learn the pattern.

class SimulatedPXISystem:
    """
    Mimics the nidaqmx.Task() API.
    
    Real nidaqmx code:
        with nidaqmx.Task() as task:
            task.ai_channels.add_ai_voltage_chan("Dev1/ai0")
            task.timing.cfg_samp_clk_timing(1000)
            data = task.read(100)
    
    Our simulated code:
        with SimulatedPXISystem() as pxi:
            pxi.add_ai_channel("SimDev1/ai0")
            pxi.configure_timing(1000, 100)
            data = pxi.read()
    """
    
    def __init__(self, device_name="SimDev1"):
        """Called when you create the object: pxi = SimulatedPXISystem()"""
        self.device_name = device_name
        self.channels = []
        self.sample_rate = 1000.0
        self.num_samples = 100
        self.is_configured = False
        print(f"[{self.device_name}] Device opened")
    
    def add_ai_channel(self, channel_name, min_val=-10.0, max_val=10.0):
        """
        Add an analog input channel.
        Real equivalent: task.ai_channels.add_ai_voltage_chan("Dev1/ai0")
        """
        self.channels.append({
            "name": channel_name,
            "min": min_val,
            "max": max_val,
        })
        print(f"[{self.device_name}] Added channel: {channel_name} "
              f"(range: {min_val} to {max_val} V)")
    
    def add_ao_channel(self, channel_name, min_val=-5.0, max_val=5.0):
        """
        Add an analog output channel.
        Real equivalent: task.ao_channels.add_ao_voltage_chan("Dev1/ao0")
        """
        self.channels.append({
            "name": channel_name,
            "min": min_val,
            "max": max_val,
        })
        print(f"[{self.device_name}] Added output channel: {channel_name}")
    
    def configure_timing(self, sample_rate, num_samples):
        """
        Set the sample clock timing.
        Real equivalent: task.timing.cfg_samp_clk_timing(rate, samps_per_chan=N)
        """
        self.sample_rate = sample_rate
        self.num_samples = num_samples
        self.is_configured = True
        duration_ms = (num_samples / sample_rate) * 1000
        print(f"[{self.device_name}] Timing: {sample_rate} Hz, "
              f"{num_samples} samples ({duration_ms:.1f} ms)")
    
    def read(self):
        """
        Read data from all configured channels.
        Real equivalent: data = task.read(number_of_samples)
        
        Returns: dict of {channel_name: numpy_array}
        """
        if not self.is_configured:
            raise RuntimeError("Call configure_timing() first!")
        
        if len(self.channels) == 0:
            raise RuntimeError("No channels added! Call add_ai_channel() first!")
        
        # Generate time array
        t = np.linspace(0, self.num_samples / self.sample_rate,
                        self.num_samples, endpoint=False)
        
        # Generate simulated signals (different freq per channel)
        data = {}
        for i, ch in enumerate(self.channels):
            freq = 100 * (i + 1)  # 100 Hz, 200 Hz, 300 Hz, etc.
            amplitude = (ch["max"] - ch["min"]) / 8  # use 1/4 of range
            signal = amplitude * np.sin(2 * np.pi * freq * t)
            noise = np.random.normal(0, amplitude * 0.02, self.num_samples)
            data[ch["name"]] = signal + noise
        
        print(f"[{self.device_name}] Read {self.num_samples} samples "
              f"from {len(self.channels)} channels")
        return data, t
    
    def write(self, waveform_data):
        """
        Write data to analog output.
        Real equivalent: task.write(data)
        """
        print(f"[{self.device_name}] Wrote {len(waveform_data)} samples to output")
    
    def close(self):
        """Close the device and free resources."""
        print(f"[{self.device_name}] Device closed\n")
    
    def __enter__(self):
        """Support for 'with' statement - called at start"""
        return self
    
    def __exit__(self, *args):
        """Support for 'with' statement - called at end (auto-cleanup)"""
        self.close()


# ===================================================================
# STEP 2: Using the SimulatedPXISystem
# ===================================================================

print("=" * 60)
print("EXAMPLE 1: Basic 4-channel acquisition")
print("=" * 60)

# The 'with' statement ensures the device is properly closed
# even if an error occurs. This is EXACTLY how nidaqmx works.

with SimulatedPXISystem("SimDev1") as pxi:
    # Add 4 analog input channels
    pxi.add_ai_channel("SimDev1/ai0")
    pxi.add_ai_channel("SimDev1/ai1")
    pxi.add_ai_channel("SimDev1/ai2")
    pxi.add_ai_channel("SimDev1/ai3")
    
    # Configure: 10 kHz sample rate, 1000 samples
    pxi.configure_timing(sample_rate=10000, num_samples=1000)
    
    # Read data
    data, t = pxi.read()
    
    # Print statistics
    print("\nResults:")
    for ch_name, samples in data.items():
        rms = np.sqrt(np.mean(samples**2))
        peak = np.max(np.abs(samples))
        print(f"  {ch_name}: RMS={rms:.4f} V, Peak={peak:.4f} V")

# Device is automatically closed here!


# ===================================================================
# STEP 3: Plot the acquired data
# ===================================================================

print("=" * 60)
print("EXAMPLE 2: Acquire and plot")
print("=" * 60)

with SimulatedPXISystem("SimDev1") as pxi:
    pxi.add_ai_channel("SimDev1/ai0", min_val=-5.0, max_val=5.0)
    pxi.add_ai_channel("SimDev1/ai1", min_val=-5.0, max_val=5.0)
    pxi.configure_timing(sample_rate=5000, num_samples=500)
    
    data, t = pxi.read()
    
    # Plot
    fig, axes = plt.subplots(2, 1, figsize=(10, 6), sharex=True)
    t_ms = t * 1000
    
    for i, (ch_name, samples) in enumerate(data.items()):
        axes[i].plot(t_ms, samples, linewidth=0.8)
        axes[i].set_ylabel(f"{ch_name} (V)")
        axes[i].grid(True, alpha=0.3)
        axes[i].set_ylim(-2, 2)
    
    axes[-1].set_xlabel("Time (ms)")
    axes[0].set_title("SimulatedPXISystem — 2-Channel Acquisition")
    plt.tight_layout()
    plt.show()


# ===================================================================
# STEP 4: Show how similar this is to REAL nidaqmx
# ===================================================================

print("=" * 60)
print("COMPARISON: Simulated vs Real nidaqmx")
print("=" * 60)

comparison = """
┌──────────────────────────────────────────────────────────────────┐
│  OUR SIMULATED CODE:              REAL nidaqmx CODE:            │
│  ─────────────────────            ──────────────────             │
│                                                                  │
│  with SimulatedPXISystem()        with nidaqmx.Task()           │
│      as pxi:                          as task:                   │
│                                                                  │
│    pxi.add_ai_channel(              task.ai_channels             │
│      "SimDev1/ai0")                   .add_ai_voltage_chan(      │
│                                       "Dev1/ai0")               │
│                                                                  │
│    pxi.configure_timing(            task.timing                  │
│      10000, 1000)                     .cfg_samp_clk_timing(      │
│                                       10000,                     │
│                                       samps_per_chan=1000)       │
│                                                                  │
│    data = pxi.read()                data = task.read(1000)       │
│                                                                  │
│  # auto-closed                    # auto-closed                  │
└──────────────────────────────────────────────────────────────────┘

When you get hardware access, the PATTERN is identical.
You just change the class name and slightly adjust the method calls!
"""
print(comparison)
