import nidaqmx
from nidaqmx.constants import AcquisitionType
from nidaqmx.stream_readers import AnalogUnscaledReader
import numpy as np
import time
import os

# ===== SETTINGS =====
CHANNELS = "PXI1Slot3/ai0"
NUM_CHANNELS = 1
RATE = 14_000_000
DURATION_S = 60
WRITE_TO_DISK = True
OUT_FILE = "rec_raw.bin"
CHUNK = 500_000
# ====================

flat = np.empty(NUM_CHANNELS * CHUNK, dtype=np.int16)
total_read = loops = max_waiting = 0
error_code, error_msg, hidden_code = 0, "", 0
acquired = remaining = -1

out = open(OUT_FILE, "wb") if WRITE_TO_DISK else None

with nidaqmx.Task() as task:
    task.ai_channels.add_ai_voltage_chan(CHANNELS)
    task.timing.cfg_samp_clk_timing(rate=RATE, sample_mode=AcquisitionType.CONTINUOUS)
    actual_rate = task.timing.samp_clk_rate
    buffer_size = task.in_stream.input_buf_size
    reader = AnalogUnscaledReader(task.in_stream)
    print("Channels:", NUM_CHANNELS, "| Actual rate:", actual_rate, "| Buffer:", buffer_size, "| Write:", WRITE_TO_DISK)

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
    except nidaqmx.errors.DaqError as e:
        error_code = e.error_code
        error_msg = str(e).split("\n")[0]

    # force one read to reveal an error the loop never saw
    try:
        probe = flat[:NUM_CHANNELS].reshape(NUM_CHANNELS, 1)
        reader.read_int16(probe, number_of_samples_per_channel=1, timeout=2.0)
    except nidaqmx.errors.DaqError as e:
        hidden_code = e.error_code
        print("Hidden error:", e.error_code, str(e).split("\n")[0])

    elapsed = time.time() - t_start
    task.stop()                                    # stop FIRST, then count
    try:
        acquired = task.in_stream.total_samp_per_chan_acquired
        remaining = task.in_stream.avail_samp_per_chan
    except nidaqmx.errors.DaqError as e:
        print("Count query error:", e.error_code)

if out:
    out.close()

file_size = os.path.getsize(OUT_FILE) if WRITE_TO_DISK else 0
peak_ms = max_waiting / actual_rate * 1000

print("Elapsed:", round(elapsed, 3), "s | Read:", total_read, "| Loops:", loops)
print("HW acquired:", acquired, "| Read+remaining:", total_read + remaining,
      "| Match:", acquired == total_read + remaining)
print("Peak waiting:", max_waiting, "(", round(peak_ms, 1), "ms ) | File:", file_size,
      "| Expected bytes:", total_read * NUM_CHANNELS * 2)
print("Loop error:", error_code, error_msg)

with open("results.csv", "a") as f:
    f.write(f"{time.strftime('%Y-%m-%d %H:%M')},{NUM_CHANNELS},{actual_rate},{DURATION_S},"
            f"{WRITE_TO_DISK},{round(elapsed,3)},{total_read},{acquired},{remaining},"
            f"{loops},{max_waiting},{file_size},{error_code},{hidden_code}\n")
