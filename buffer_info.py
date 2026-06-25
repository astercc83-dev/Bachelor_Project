""" Experiment 
1: Inspect the hardware buffers (answer his question "what is the capacity?").
This answers exactly: "which memory in the hardware, and what is its capacity."""

# import nidaqmx
# from nidaqmx.constants import AcquisitionType

# with nidaqmx.Task() as task:
#     task.ai_channels.add_ai_voltage_chan("PXI1Slot3/ai0")
#     task.timing.cfg_samp_clk_timing(
#         rate=14_000_000,
#         sample_mode=AcquisitionType.CONTINUOUS
#     )
#     # Onboard FIFO size (on the card itself)
#     print(f"Onboard buffer (FIFO) size: {task.in_stream.input_onbrd_buf_size} samples")
#     # Host buffer size (in RAM, managed by driver)
#     print(f"Host buffer size: {task.in_stream.input_buf_size} samples")



""" Experiment 2: Deliberately cause a real buffer overflow
Make the reader artificially slow (like your slow processor in the simulation): 
At 10 MS/s the driver buffer fills in a fraction of a second while 
you sleep → overflow detected.
This is the deliverable: "here appears buffer overflow."""


import nidaqmx
import time
from nidaqmx.constants import AcquisitionType

with nidaqmx.Task() as task:
    task.ai_channels.add_ai_voltage_chan("PXI1Slot3/ai0")
    task.timing.cfg_samp_clk_timing(
        rate=1_000_0000, # 10 MS/s — very fast producer
        sample_mode=AcquisitionType.CONTINUOUS
    )
    task.start()
    read_count = 0
    try:
        while True:
            available = task.in_stream.avail_samp_per_chan
            percent_full = (available / 1_000_000) * 100
            data = task.read(number_of_samples_per_channel=1000)
            read_count += 1
            print(f'Read # {read_count:3d} |')

            time.sleep(0.5)               # ← simulate slow consumer!
    except nidaqmx.errors.DaqError as e:
        print("BUFFER OVERFLOW DETECTED!")
        print(f"Error code: {e.error_code}")   # expect -200279


""" Experiment 3: Measure how much margin you have
Instead of sleeping, monitor how many samples are waiting in the host buffer: """

#available = task.in_stream.avail_samp_per_chan

""" Print this every loop. If it keeps growing, 
your read loop is too slow and overflow is coming. 
If it stays near zero, you are keeping up. 
This is your early-warning system — much smarter than waiting for the crash. """
