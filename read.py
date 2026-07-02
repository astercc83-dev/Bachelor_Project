import nidaqmx
import numpy as np
import matplotlib.pyplot as plt
""" the AcquisitionType from const is important 
as it give us an access to the number of samples that we will take 
is that a FINITE number or CONTINUOS taking of samples numbers"""
from nidaqmx.constants import AcquisitionType # To have an access to the timer
import time

rate = 14_000_000
sample_per_read = 1_000_000
max_loops = 500
write_to_file = True # True= raed and write to file. False = read only

result_file = open("overflow_result.txt", "a")

# Optional: record the actual samples (un-comment to use)
# data_file = open("recorded_data.txt", "a")

overflow_happens = False
overflow_loop = -1

with nidaqmx.Task() as task:
    task.ai_channels.add_ai_voltage_chan("PXI1Slot3/ai0")
    task.timing.cfg_samp_clk_timing(rate=rate, sample_mode=AcquisitionType.CONTINUOUS)

    # increasing the buffer size 
    #task.in_stream.input_buf_size = 1_000_000
    buffer_size = task.in_stream.input_buf_size

    task.start()

    for i in range(max_loops):
        start_time = time.time()
        try:
            data = task.read(number_of_samples_per_channel=sample_per_read)
            waiting = task.in_stream.avail_samp_per_chan

            if write_to_file:
                # Write a summary line per read (lightweight)
                result_file.write(f"loop {str(i)} ok, read {str(len(data))} samples, Waiting_samples_in_buffer={waiting} sampels\n")

                # Optional: record the actual samples (un-comment to use)
                # for value in data:
                #    data_file.write(str(value) + "\n")
            
        except nidaqmx.errors.DaqReadError as error:
            overflow_happens = True
            overflow_loop = i
            print("OVERFLOW at Loop", i)
            break
    loop_time = time.time() - start_time
    task.stop()

# Write the experiment result summary
summary = ("RESULT | rate=" + str(rate) +
           " | samples_per_read=" + str(sample_per_read) +
           " | buffer_size=" + str(buffer_size) +
           " | write_to_file=" + str(write_to_file) +
           " | overflow=" + str(overflow_happens) +
           " | at_loop=" + str(overflow_loop) + 
           " | time_taken_after_all_loops=" + str(round(loop_time * 1000, 3))+ "ms" + "\n")

result_file.write(summary)
result_file.close()

# data_file.close() # un-comment if recording actual samples

print(summary)








# # Interactive Mode: this say to matplotlib, i will draw 
# # a live plot so don't stop the prog.
# plt.ion()



# figure, axis = plt.subplots()

# # line with temporary data all are at start 0(thousand 0), 
# # we will update this line each iteration. 
# line, = axis.plot(range(10000), [0] * 10000)

# # Keep the y-Axis limit between 0 and 0.02 and not upadate any value
# axis.set_ylim(0, 0.05)

# plt.title("Live Plot")
# plt.xlabel("Sample number")
# plt.ylabel("Voltage (V)")


# # with nidaqmx.Task() as task:
# #     task.ai_channels.add_ai_voltage_chan("PXI1Slot3/ai0")
# #     task.timing.cfg_samp_clk_timing(rate=20_000, sample_mode=AcquisitionType.FINITE, samps_per_chan=1000)
# #     """ This 100 samples will be road from the host buffer (RAM), 
# #     after the DMA brought it from FIFO to RAM """
# #     data = task.read(number_of_samples_per_channel=1000)
# #     #print(data)

# with nidaqmx.Task() as task:
#     task.ai_channels.add_ai_voltage_chan("PXI1Slot3/ai0")
#     task.timing.cfg_samp_clk_timing(rate=rate, sample_mode=AcquisitionType.CONTINUOUS)

#     # increasing the buffer size 
#     #task.in_stream.input_buf_size = 1_000_000
#     buffer_size = task.in_stream.input_buf_size
#     print(f"Host buffer (samples): {buffer_size}")

#     task.start()

#     for i in range(200):
#         loop_start = time.time()
#         data = task.read(number_of_samples_per_channel=10000)

#         # # (Clear Figure): in every iteration clear the old plot. 
#         # plt.clf()
#         # # draw or plot the data after each itration
#         # plt.plot(data)
#         # # The title will change each iteration to see the num of current read
#         # plt.title("Live Plot - Read number " + str(i))

#         # Update the line before was (thousand 0) now with each 
#         # data values in each iteration
#         line.set_ydata(data)
#         plt.pause(0.01)
#         loop_time = time.time() - loop_start
#         waiting = task.in_stream.avail_samp_per_chan
#         print(f"Loop {i} - loop time: {round(loop_time, 4)} S - waiting in buffer: {waiting}")
#         # This line is very important it give the matplotlib
#         # a chance to draw and show the plot on the screen
#         # and pause for 10 ms so we can see the plot
        
#     task.stop()

# # Close the interactive mode 
# plt.ioff()
# # show the plot on the screen
# plt.show()

# # Static Plot
# # plt.plot(data)
# # plt.title("Real Data from Card")
# # plt.xlabel("Sample number")
# # plt.ylabel("Voltage (V)")

# # plt.show()