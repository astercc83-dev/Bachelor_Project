import nidaqmx
from nidaqmx.constants import AcquisitionType
from nidaqmx.stream_readers import AnalogUnscaledReader
import numpy as np
import time
import os

# ===== SETTINGS: change these between runs =====
CHANNELS = "PXI1Slot3/ai0"       # later: "PXI1Slot3/ai0:1" for 2 channels
NUM_CHANNELS = 1                 # must match CHANNELS
RATE = 45000                     # later: 14_000_000
DURATION_S = 60                  # later: 300, 600, 1200
OUT_FILE = "rec_raw.bin"
CHUNK = 500_000                  # max samples per channel per read
HOST_BUFFER = 10_000_000         # host buffer size in samples per channel
# ===============================================

chunk_array = np.empty((NUM_CHANNELS, CHUNK), dtype=np.int16)

total_read = 0
loops = 0
max_waiting = 0
overflow = False
error_msg = ""

out = open(OUT_FILE, "wb")

with nidaqmx.Task() as task:
    task.ai_channels.add_ai_voltage_chan(CHANNELS)
    task.timing.cfg_samp_clk_timing(rate=RATE, sample_mode=AcquisitionType.CONTINUOUS)
    task.in_stream.input_buf_size = HOST_BUFFER

    actual_buffer = task.in_stream.input_buf_size
    reader = AnalogUnscaledReader(task.in_stream)

    print("Channels:      ", NUM_CHANNELS)
    print("Rate:          ", RATE, "S/s per channel")
    print("Duration:      ", DURATION_S, "s")
    print("Host buffer:   ", actual_buffer, "samples per channel")
    print("Running...")

    task.start()
    t_start = time.time()

    try:
        while (time.time() - t_start) < DURATION_S:
            waiting = task.in_stream.avail_samp_per_chan

            if waiting > max_waiting:
                max_waiting = waiting

            if waiting > 0:
                to_read = min(waiting, CHUNK)
                reader.read_int16(chunk_array[:, :to_read],
                                  number_of_samples_per_channel=to_read)
                chunk_array[:, :to_read].tofile(out)
                total_read += to_read
                loops += 1

    except nidaqmx.errors.DaqError as e:
        overflow = True
        error_msg = str(e).split("\n")[0]

    elapsed = time.time() - t_start
    task.stop()

out.close()

# ===== RESULTS =====
expected = int(RATE * elapsed)
difference = expected - total_read
loss_percent = (difference / expected * 100) if expected > 0 else 0
file_size = os.path.getsize(OUT_FILE)
expected_bytes = total_read * NUM_CHANNELS * 2

print("")
print("===== RESULT =====")
print("Channels:          ", NUM_CHANNELS)
print("Rate:              ", RATE, "S/s per channel")
print("Elapsed time:      ", round(elapsed, 3), "s")
print("Expected samples:  ", expected, "per channel")
print("Read samples:      ", total_read, "per channel")
print("Difference:        ", difference)
print("Loss percent:      ", round(loss_percent, 4), "%")
print("Read loops:        ", loops)
print("Max waiting seen:  ", max_waiting, "of", actual_buffer)
print("Buffer peak usage: ", round(max_waiting / actual_buffer * 100, 2), "%")
print("File size:         ", file_size, "bytes")
print("Expected bytes:    ", expected_bytes)
print("Overflow:          ", overflow)
if overflow:
    print("Error:             ", error_msg)
print("==================")