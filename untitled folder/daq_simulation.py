import threading
import queue
import time

"""
In the PXI the Reader collect the row data from PXI such as voltages,
will send the data to the queue that works as a data collector
or a place holder for the data. After the Processor will,
take the data from the queue. We do this because the Processor is
slower that the Reader and can not catch the all data directly
from the Reader which is much faster than the Processor that process
the data and print it live.
""" 
queue_1 = queue.Queue(maxsize=20)
queue_2 = queue.Queue()
stop_event = threading.Event() # this will stop the threads at the end or when i need this
lost_samples = 0 # to count how many samples are lost because of Buffer overflow
                 # Buffer Overflow occurs when the queue is full and the reader tries to add new data
total_read = 0
total_processed = 0  

def reader():
    global lost_samples, total_read
    i = 0 # will use as number of each sample the reader reads from PXI
    while not stop_event.is_set():
        if queue_1.full():
            lost_samples += 1
            print(f"Overflow - sample {i} is lost. Total lost Sample are {lost_samples}")
        else:
            queue_1.put(f"sample {i}") # put the road data in the queue
            total_read += 1
            print(f"Reader sample {i} road")
        i += 1
        time.sleep(0.5) # pause 0.5 sec after each sample


def processor():
    global total_processed
    while not stop_event.is_set() or not queue_1.empty():
        try:
            data = queue_1.get(timeout=0.5) # get the stored data from the first queue
            total_processed += 1
            print(f"Processer will work on this {data}") # draw data 
            queue_2.put(data) # After drawing the data put it in the second queue
            time.sleep(1)
        except:
            pass


def saver():
    file = open("data.txt", "w")
    while not stop_event.is_set() or not queue_1.empty() or not queue_2.empty():
        try:
            data = queue_2.get(timeout=0.5) # get the data from the second queue
            file.write(data + "\n")
            # flush means: write the data directly in the file.
            file.flush() # to prvent python Buffering(collects data in RAM first then afetr awhile it writs it)
        except:
            pass
    file.close()
    print(f"Saver: i have closed the file")


thread_reader = threading.Thread(target=reader)
thread_processor = threading.Thread(target=processor)
tread_saver = threading.Thread(target=saver)

thread_reader.start()
thread_processor.start()
tread_saver.start()

input("Please Press Enter to stop threading...\n")
stop_event.set()

print("Waits for queue_1 to empty its elements...")
while not queue_1.empty():
    time.sleep(0.1)
print("queue 1 emptys its content!")

print("Waits for queue_2 to empty its elements...")
while not queue_2.empty():
    time.sleep(0.1)
print("queue 2 emptys its content!")

thread_reader.join() # gurentees that all threads are done before the prog ends.
thread_processor.join()
tread_saver.join()

print(f"The programm is done. Total number of Lost Samples are {lost_samples}")


total_attempted = total_read + lost_samples
print(f"Tatal tries:  {total_attempted}")
print(f"Check: {total_attempted} = {total_read} + {lost_samples} → {total_read + lost_samples == total_attempted}")