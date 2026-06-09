import nidaqmx # bring the all nidaqmx liberary
import nidaqmx.system # to identify the device and the installed driver
import time
from nidaqmx.constants import AcquisitionType
#import multiprocessing
#import threading


"""a class in the nidaqmx-> to represent the PXI-sys. 
local(): mean this device (local device -PXI- itself)
"""
system = nidaqmx.system.System.local() # goto pxi and collect its infos
print(f"Driver: {system.driver_version}") # to get the driver version

""" In the project system.devices = [PXI1Slot2,  PXI1Slot3,  PXI1Slot4]
   Dev1 = AI Card (8 channels)
   Dev2 = AI Card (8 channels)
   Dev3 = AO + Digital Card """
for device in system.devices: # device: Dev1 then Dev2 then Dev3 
    print(f"Device: {device.name}") # print each dev name -> Device: Dev1

    """ device.ai_physical_chans: a list with all analog input channels 
    in the current card (device). the list compehession here means:
    take each channel and give just the name of each one -> 
    Channels: ['PXI1Slot3/ai0', 'PXI1Slot3/ai1', ..., 'PXI1Slot3/ai7'] """
    print(f"Channels: {[ch.name for ch in device.ai_physical_chans]}")



""" nidaqmx.Task: Make a new task (task like an work order you give it to PXI)
to do something... .  "with ... as task" this part do two thing:
1. Opens the and prepared it. 
2. Closes it automatically even when error happens """
with nidaqmx.Task() as task:
    task.ai_channels.add_ai_voltage_chan("PXI1Slot3/ai0")
    value = task.read() # read the voltage form the added channel before
    print(f"Voltage: {value:.4f} V")


""" We will use a for loop with those sampling rates to see how
Python copes with each rate, and at which rate Python will
fail to catch up with the data. """
sampling_rates = [1000, 10000, 1000000, 5000000, 14000000]

for rate in sampling_rates:
    try: # try to make the following task
        with nidaqmx.Task() as task:
            task.ai_channels.add_ai_voltage_chan("PXI1Slot3/ai0")
            """ We read a 1000 sample with a speed of `rate` in 
            second -> for 1 MS/s it will take 1000000/1000 = 1ms""" 
            task.timing.cfg_samp_clk_timing(
                rate = rate,
                sample_mode=AcquisitionType.FINITE,
                samps_per_chan=1000
            )
            start = time.time() # the current time now(time before reading)
            data = task.read(1000) # read 1000 Sample from the pxi
            elapsed = time.time() - start # time now - time before reading

            print(f"Rate: {rate/1e6: .1f} MS/s"
                  f"1000 Samples road in {elapsed*1000: .1f} ms")

    except Exception as e: # if you fail do the following order instead of error showing
        print(f"Rate: {rate/1e6: .1f} MS/s fails: {e}")