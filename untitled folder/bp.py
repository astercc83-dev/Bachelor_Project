import nidaqmx.system
import numpy as np 

#print(dir(nidaqmx))
#print(dir(nidaqmx.system))

""" Discover your hardware """
system = nidaqmx.system.System.local()
print(f"Driver version: {system.driver_version}")
for device in system.devices:
    print(f"Device: {device.name}")
    print(f"  AI channels: {[ch.name for ch in device.ai_physical_chans]}")
    print(f"  AO channels: {[ch.name for ch in device.ao_physical_chans]}")
    print(f"  DI lines: {[ch.name for ch in device.di_lines]}")
    print(f"  DO lines: {[ch.name for ch in device.do_lines]}")

""" Read a single analog voltage """
with nidaqmx.Task() as task:
    task.ai_channels.add_ai_voltage_chan("Dev1/ai0", min_val=-10.0, max_val=10.0)
    value = task.read()
    print(f"Voltage: {value:.4f} V")


""" Read multiple channels """
with nidaqmx.Task() as task:
    task.ai_channels.add_ai_voltage_chan("Dev1/ai0:3")  # channels 0-3
    values = task.read()
    for i, v in enumerate(values):
        print(f"Channel {i}: {v:.4f} V")

""" Hardware-timed acquisition """
from nidaqmx.constants import AcquisitionType, READ_ALL_AVAILABLE

with nidaqmx.Task() as task:
    task.ai_channels.add_ai_voltage_chan("Dev1/ai0")
    task.timing.cfg_samp_clk_timing(
        rate=1000.0,  # 1000 samples per second
        sample_mode=AcquisitionType.FINITE,
        samps_per_chan=100  # collect 100 samples
    )
    data = task.read(READ_ALL_AVAILABLE)
    print(f"Collected {len(data)} samples")
    print(f"First 5: {data[:5]}")


"""" Generate an analog output (sine wave) """
samples = 1000
freq = 10  # Hz
t = np.linspace(0, 1, samples, endpoint=False)
sine_wave = np.sin(2 * np.pi * freq * t)

with nidaqmx.Task() as task:
    task.ao_channels.add_ao_voltage_chan("Dev1/ao0", min_val=-5.0, max_val=5.0)
    task.timing.cfg_samp_clk_timing(
        rate=1000.0,
        sample_mode=AcquisitionType.FINITE,
        samps_per_chan=samples
    )
    task.write(sine_wave, auto_start=True)
    task.wait_until_done()
    print("Sine wave generated!")