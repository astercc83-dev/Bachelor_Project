import nidaqmx
from nidaqmx.constants import AcquisitionType
from nidaqmx.stream_readers import AnalogUnscaledReader 
from nidaqmx.stream_readers import AnalogSingleChannelReader

import numpy as np 
import os
import time 



rate_to_test = [10_000_000, 14_000_000]
samples_per_read_to_test = [10_000, 1_000_000, 10_000_000, 14_000_000]
max_loops = 200

# total_samples = samples_per_read * loops

# Old Method: write the data afeter conversion (float64 written as txt)
# results = open("experiment_results.txt", "a")
# results.write("\n=== New experiment run === \n")
# results.write("rate | samples/read | mode | overflow | at_loop | expected_ms | measured_ms\n")

def run_experiment(rate):
    overflow = False
    overflow_loop = -1
    loop_times = []
    buffer = np.empty(
    125*10**6,
    dtype=np.float64
)
    
    
    with nidaqmx.Task() as task:
        print("task_started")
        reader = AnalogSingleChannelReader(task.in_stream)
        task.ai_channels.add_ai_voltage_chan("PXI1Slot3/ai0")
        task.timing.cfg_samp_clk_timing(rate=rate, sample_mode=AcquisitionType.CONTINUOUS)
        #task.in_stream.input_buf_size = 4*10**6 *15

        # # prepare raw reader + buffer if needed
        # reader = AnalogUnscaledReader(task.in_stream)
        # raw_buffer = np.empty((1, samples_per_read), dtype=np.int16)

        # # open output file depending on mode
        # if mode == "write_text":
        #     out = open("rec_text.txt", "w")
        # elif mode == "write_raw":
        #     out = open("rec_raw.bin", "wb")

        task.start()
        start = 0
        data_collected = 0
        while True:
            
            loop_start = time.time()
            
            if True:
                data_in_buffer = task.in_stream.avail_samp_per_chan
                print(data_in_buffer)
                new_data = task.read(number_of_samples_per_channel=data_in_buffer)
                
                

                end = start + len(new_data)

                buffer[start:end] = new_data

                data_collected += len(new_data)

                start = end

            if data_collected >= (14* 10**6) * 10:
                print("done for 60 sec")
                loop = time.time() - loop_start
                print(loop)
                break

                    
                # elif mode == "write_text":
                #     data_in_buffer = task.in_stream.avail_samp_per_chan
                #     data = task.read(number_of_samples_per_channel=data_in_buffer)
                #     data_colleteced = data_colleteced + data_in_buffer
                #     for value in data:
                #         out.write(str(value) + "\n")
                
                # elif mode == "write_raw":
                #     reader.read_int16(raw_buffer, number_of_samples_per_channel=samples_per_read)
                #     raw_buffer.tofile(out)
            # nidaqmx.errors.DaqReadError:
            #     overflow = True
            #     #print(data)
            #     print("over")
            #     #overflow_loop = i
            #     break
            #loop_times.append(time.time() - loop_start)

        task.stop()
run_experiment(14*10**6)
#         if mode in ("write_text", "write_raw"):
#             out.close()

#     expected_ms = (samples_per_read /  rate) * 1000
#     measured_ms = (sum(loop_times) / len(loop_times)) * 1000 if loop_times else 0

#     line = (f"{str(rate)} | {str(samples_per_read)} | {mode} | {str(overflow)} | {str(overflow_loop)} | {str(round(expected_ms, 2))} | {str(round(measured_ms, 2))} \n")
#     results.write(line)
#     print(line.strip())

# for rate in rate_to_test:
#     for spr in samples_per_read_to_test:
#         for mode in ["read_only", "write_text", "write_raw"]:
#             run_experiment(rate, spr, mode)
# results.close()
# print("\nDone. Check expermint_results.txt")



# # The new Methode: is to write a raw data(int16 written as binary) (size 2 bytes)
# raw_file = open("recorded_raw.bin", "wb")

# with nidaqmx.Task() as task:
#     task.ai_channels.add_ai_voltage_chan("PXI1Slot3/ai0")
#     task.timing.cfg_samp_clk_timing(rate=rate, sample_mode=AcquisitionType.CONTINUOUS)
#     reader = AnalogUnscaledReader(task.in_stream)
#     buffer = np.empty((1, samples_per_read), dtype=np.int16)

#     task.start()

#     for i in range(loops):
#         reader.read_int16(buffer, number_of_samples_per_channel=samples_per_read)
#         buffer.tofile(raw_file)
    
#     task.stop()

# raw_file.close()

# data = np.fromfile("recorded_raw.bin", dtype=np.int16)

# # For +- 10 V -(20V)- range (default). 16 bit
# step_size = 20 / (2**16)
# volts = data * step_size

# print("First 100 sampls in volts:", volts[:100])
# # print("Number of samples:", len(data))
# # print("First 20 samples:", data[:500])

# # compare the actual file sizes
# text_size = os.path.getsize("recorded_text.txt")
# raw_size = os.path.getsize("recorded_raw.bin")

# print("*" * 50 + "\n")
# print(f"Total samples recorded: {total_samples}")
# print(f"Text file size: {text_size} bytes = {round(text_size/total_samples, 2)} bytes/sample")
# print(f"Raw file size: {raw_size} bytes = {round(raw_size/total_samples, 2)} bytes/sample")
# print(f"Text is {round(text_size/raw_size, 1)} times bigger than raw")
# print("*" * 50 + "\n")
