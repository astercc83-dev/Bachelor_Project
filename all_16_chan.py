import nidaqmx
from nidaqmx.constants import AcquisitionType
from nidaqmx.stream_readers import AnalogUnscaledReader
import numpy as np
import time
import os

# ===== SETTINGS =====
CHANNELS = "PXI1Slot3/ai0:7, PXI1Slot4/ai0:7"
NUM_CHANNELS = 16
RATE = 14_000_000
DURATION_S = 60
WRITE_TO_DISK = True
OUT_FILE = "rec_raw_16ch.bin"
CHUNK = 500_000
# ====================

flat = np.empty(NUM_CHANNELS * CHUNK, dtype=np.int16)

total_read = 0
loops = 0
max_waiting = 0
overflow = False
overflow_time = -1
error_msg = ""
acquired = remaining = -1

out = open(OUT_FILE, "wb") if WRITE_TO_DISK else None

with nidaqmx.Task() as task:
    task.ai_channels.add_ai_voltage_chan(CHANNELS)
    task.timing.cfg_samp_clk_timing(rate=RATE, sample_mode=AcquisitionType.CONTINUOUS)

    actual_rate = task.timing.samp_clk_rate
    buffer_size = task.in_stream.input_buf_size
    reader = AnalogUnscaledReader(task.in_stream)

    print("Channels:     ", NUM_CHANNELS)
    print("Actual rate:  ", actual_rate, "S/s per channel")
    print("Host buffer:  ", buffer_size, "samples per channel")
    print("Write to disk:", WRITE_TO_DISK)
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
                block = flat[:NUM_CHANNELS * to_read].reshape(NUM_CHANNELS, to_read)
                reader.read_int16(block, number_of_samples_per_channel=to_read)
                if WRITE_TO_DISK:
                    block.T.tofile(out)
                total_read += to_read
                loops += 1

                if loops <= 20 or loops % 500 == 0:
                    print(loops, round(time.time() - t_start, 2), "s | waiting:", waiting, "| read:", to_read)

    except nidaqmx.errors.DaqError as e:
        overflow = True
        overflow_time = round(time.time() - t_start, 2)
        error_msg = str(e).split("\n")[0]

    elapsed = time.time() - t_start
    task.stop()

    try:
        acquired = task.in_stream.total_samp_per_chan_acquired
        remaining = task.in_stream.avail_samp_per_chan
    except nidaqmx.errors.DaqError:
        pass

if out:
    out.close()

# ===== RESULTS =====
expected = int(actual_rate * elapsed)
data_mb = total_read * NUM_CHANNELS * 2 / 1e6

print("")
print("===== RESULT =====")
print("Elapsed time:      ", round(elapsed, 3), "s")
print("Expected samples:  ", expected, "per channel")
print("Read samples:      ", total_read, "per channel")
print("HW acquired:       ", acquired)
print("Read + remaining:  ", total_read + remaining)
print("Exact match:       ", acquired == total_read + remaining)
print("Read loops:        ", loops)
print("Max waiting seen:  ", max_waiting, "of", buffer_size)
print("Buffer peak usage: ", round(max_waiting / buffer_size * 100, 2), "%")
print("Data rate:         ", round(data_mb / elapsed, 1), "MB/s total")
if WRITE_TO_DISK:
    print("File size:         ", os.path.getsize(OUT_FILE), "bytes")
    print("Expected bytes:    ", total_read * NUM_CHANNELS * 2)
print("Overflow:          ", overflow)
if overflow:
    print("Overflow at:       ", overflow_time, "s")
    print("Error:             ", error_msg)
print("==================")