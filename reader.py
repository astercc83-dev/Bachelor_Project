import nidaqmx  # To read from the PXI harware
from nidaqmx.constants import AcquisitionType
from nidaqmx import constants
import numpy as np # To create and handel the data arrays
from multiprocessing import shared_memory # To create the shared buffer between processes

""" We need at first to define our constants. such as;
CHANNEL: the physical channel we read from.
SAMPLE_RATE: We define a 1 MS/s, we know from our benchmark that 
the PXI supports this --We can change it later--.
BUFFER_SIZE: how many samples in each buffer. 1000 Sample at 
1 MS/s = 1 ms of data per buffer. """

CHANNEL = "PXI1Slot3/ai0"
SAMPLE_RATE = 1_000_000
BUFFER_SIZE = constants.READ_ALL_AVAILABLE


""" Creating the Shared Memory:(Shared Memory) is a special area in 
RAM that all Processes can see and access at the same time """

# how many bytes one sample takes = np.float64().itemsize = 8 bytes
# BUFFER_SIZE * 8 bytes = total bytes needed for 1000 Samples = 8000 bytes
buffer_size_bytes = BUFFER_SIZE * np.float64().itemsize 

shm = shared_memory.SharedMemory(
    name="pxi_buffer", # a name so other processes can find this memory
    create=True, # creare it fresh (not connect to existing one)
    size=buffer_size_bytes # how big the memory area is
)

# Creates a numpy array that lives inside the shared memory
# for example: shm = reserve a space in RAM (8000 bytes)
# buffer = put a numpy array inside that space
buffer = np.ndarray( 
    shape=(BUFFER_SIZE,),
    dtype=np.float64, # each sample is a 64-bit float number
    buffer=shm.buf # connect the array to the shared memory area
)


""" Writing the Reader function: that reads the data from 
PXI and write it in the shared memory """

def read_from_pxi(): # A function that contains all reading logic.
    with nidaqmx.Task() as task: # make a new task as follows:
        task.ai_channels.add_ai_voltage_chan(CHANNEL) # read the voltage of channel 'CHANNEL'
        task.timing.cfg_samp_clk_timing( 
            rate=SAMPLE_RATE, # read at speed of SAMPLE_RATE(1 MS/s)
            sample_mode=nidaqmx.constants.AcquisitionType.CONTINUOUS # continuous means read forever until we say Stop
        )
        task.start() # Tell the PXI Card: start collecting Samples now.
        print("Reader started...")

        while True: # Read forever in a loop.
            data = task.read( # Read BUFFER_SIZE(1000 samples) from the pxi
                number_of_samples_per_channel=BUFFER_SIZE
            )
            # Write the BUFFER_SIZE(1000 samples) into the Shared Memory.
            # the [:] means copy into the existing array not create a new one this 
            # very important without [:] the shared memory connections breaks. 
            buffer[:] = data
            print(f"Read {BUFFER_SIZE} samples, first value: {buffer[0]:.4f} V")


""" Adding a cleanup and then we run the reader function """

 # only run this code if I run this file directly.
 # This important later when we import this file from main.py file.
if __name__ == "__main__" :
    try: # try to run the reader. 
        read_from_pxi()
    except KeyboardInterrupt: # If the user presses Ctrl+C to stop the prog, don't crash just stop cleanly.
        print("Reader stopped by user.")
    finally: # This runs always whether the program stopped normally or crashed.
        shm.close() # Disconnect from the shared memory.

        # Delete the Shared Memory from RAM completely. Very IMPORTANT: because if we forgot
        # this, the memory stays reserved even after the program closes!
        shm.unlink() 
        print("Shared memory cleaned up.")