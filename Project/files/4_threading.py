"""
SCRIPT 4: Threading — Producer-Consumer Pattern
=================================================
This is THE most important pattern for your project.
In WP3, you need to:
  - Thread 1 (Producer): Read data from the PXI hardware
  - Thread 2 (Consumer): Plot the data in real-time

Without threading, reading blocks plotting, and you lose data.
This script teaches you exactly how it works.

Run this: python 4_threading.py
"""
import threading
import queue
import time
import numpy as np
import matplotlib.pyplot as plt


# ===================================================================
# STEP 1: Understanding the Problem
# ===================================================================

print("=" * 60)
print("WHY DO WE NEED THREADING?")
print("=" * 60)
print("""
Without threading (BAD):
  while running:
      data = read_from_hardware()   # takes 100ms
      plot_data(data)               # takes 50ms
      save_data(data)               # takes 30ms
      # Total: 180ms per loop = data loss at high sample rates!

With threading (GOOD):
  Thread 1: read_from_hardware() → puts data in queue
  Thread 2: gets data from queue → plots it
  Thread 3: gets data from queue → saves it
  # All run simultaneously! No data loss.
""")

input("Press Enter to continue to the demo...\n")


# ===================================================================
# STEP 2: Simple Threading Example
# ===================================================================

print("=" * 60)
print("STEP 2: Simple Threading Example")
print("=" * 60)

def count_up(name, count):
    """A simple function that counts and prints."""
    for i in range(count):
        print(f"  [{name}] Count: {i+1}")
        time.sleep(0.3)

# Without threading: runs one after another (sequential)
print("\nWithout threading (sequential):")
start = time.time()
count_up("Task A", 3)
count_up("Task B", 3)
sequential_time = time.time() - start
print(f"Total time: {sequential_time:.1f} seconds\n")

# With threading: runs at the same time (parallel)
print("With threading (parallel):")
start = time.time()

thread_a = threading.Thread(target=count_up, args=("Task A", 3))
thread_b = threading.Thread(target=count_up, args=("Task B", 3))

thread_a.start()   # Start thread A
thread_b.start()   # Start thread B (runs at same time!)

thread_a.join()     # Wait for A to finish
thread_b.join()     # Wait for B to finish

threaded_time = time.time() - start
print(f"Total time: {threaded_time:.1f} seconds")
print(f"Speedup: {sequential_time/threaded_time:.1f}x faster!\n")

input("Press Enter to continue to the DAQ simulation...\n")


# ===================================================================
# STEP 3: The Queue — How threads communicate
# ===================================================================

print("=" * 60)
print("STEP 3: Understanding Queues")
print("=" * 60)
print("""
A Queue is a thread-safe FIFO (First-In, First-Out) buffer.
Producer puts data IN → Queue → Consumer takes data OUT

Think of it like a conveyor belt in a factory:
  Worker 1 puts items on the belt (producer)
  Worker 2 takes items off the belt (consumer)
  They work at their own speed without blocking each other!
""")

# Simple queue demo
q = queue.Queue()

# Put items in
q.put("sample_1")
q.put("sample_2")
q.put("sample_3")
print(f"Queue size after 3 puts: {q.qsize()}")

# Get items out (FIFO order)
item1 = q.get()
item2 = q.get()
print(f"Got: {item1}, {item2}")
print(f"Queue size after 2 gets: {q.qsize()}\n")

input("Press Enter to continue to the full DAQ simulation...\n")


# ===================================================================
# STEP 4: Full DAQ Simulation with Threading
# ===================================================================

print("=" * 60)
print("STEP 4: Full DAQ Producer-Consumer Simulation")
print("=" * 60)

# Shared resources
data_queue = queue.Queue()      # Thread-safe buffer
stop_event = threading.Event()  # Signal to stop all threads
all_data = []                   # Collected data for final plot


def daq_reader(data_q, stop, sample_rate=1000, chunk_size=100):
    """
    PRODUCER thread: Simulates reading from PXI hardware.
    
    In real code, this would be:
        data = task.read(chunk_size)
    
    Runs in a loop, putting chunks of data into the queue.
    """
    sample_count = 0
    chunk_number = 0
    
    while not stop.is_set():
        # Simulate the time it takes to fill a buffer
        time.sleep(chunk_size / sample_rate)
        
        # Generate simulated DAQ data
        t_start = sample_count / sample_rate
        t = np.linspace(t_start, t_start + chunk_size / sample_rate,
                        chunk_size, endpoint=False)
        
        # Simulate a 100 Hz sine wave with noise
        signal = 2.0 * np.sin(2 * np.pi * 100 * t) + \
                 np.random.normal(0, 0.1, chunk_size)
        
        # Put data into queue
        data_q.put({
            "time": t,
            "signal": signal,
            "chunk": chunk_number
        })
        
        sample_count += chunk_size
        chunk_number += 1
    
    print(f"\n  [READER] Stopped. Produced {chunk_number} chunks "
          f"({sample_count} total samples)")


def data_processor(data_q, stop, collected_data):
    """
    CONSUMER thread: Processes data from the queue.
    
    In real code, this would update a live plot.
    Here we calculate statistics and collect data.
    """
    chunks_processed = 0
    
    while not stop.is_set() or not data_q.empty():
        try:
            # Try to get data from queue (wait up to 0.1 seconds)
            chunk = data_q.get(timeout=0.1)
            
            # Calculate statistics
            rms = np.sqrt(np.mean(chunk["signal"]**2))
            peak = np.max(np.abs(chunk["signal"]))
            
            # Store for later plotting
            collected_data.append(chunk)
            chunks_processed += 1
            
            # Print status every 5 chunks
            if chunks_processed % 5 == 0:
                print(f"  [PROCESSOR] Chunk #{chunk['chunk']:3d} | "
                      f"RMS: {rms:.3f} V | Peak: {peak:.3f} V | "
                      f"Queue size: {data_q.qsize()}")
        
        except queue.Empty:
            # No data available, just continue waiting
            continue
    
    print(f"  [PROCESSOR] Stopped. Processed {chunks_processed} chunks")


# --- Run the simulation ---
print("\nStarting 3-second DAQ acquisition simulation...")
print("(Reader thread produces data, Processor thread consumes it)\n")

# Create threads
reader_thread = threading.Thread(
    target=daq_reader,
    args=(data_queue, stop_event, 1000, 100),
    name="DAQ-Reader"
)
processor_thread = threading.Thread(
    target=data_processor,
    args=(data_queue, stop_event, all_data),
    name="Data-Processor"
)

# Start both threads
reader_thread.start()
processor_thread.start()

# Let them run for 3 seconds
print("  [MAIN] Acquisition running for 3 seconds...\n")
time.sleep(3.0)

# Signal threads to stop
print("\n  [MAIN] Stopping acquisition...")
stop_event.set()

# Wait for both threads to finish
reader_thread.join()
processor_thread.join()

print(f"\n  [MAIN] Done! Queue remaining: {data_queue.qsize()}")
print(f"  [MAIN] Total chunks collected: {len(all_data)}")

input("\nPress Enter to see the collected data plot...\n")


# ===================================================================
# STEP 5: Plot all the collected data
# ===================================================================

print("=" * 60)
print("STEP 5: Plotting Collected Data")
print("=" * 60)

if all_data:
    # Combine all chunks into one continuous signal
    full_time = np.concatenate([chunk["time"] for chunk in all_data])
    full_signal = np.concatenate([chunk["signal"] for chunk in all_data])
    
    print(f"Total data points: {len(full_signal)}")
    print(f"Total duration: {full_time[-1]:.2f} seconds")
    print(f"Overall RMS: {np.sqrt(np.mean(full_signal**2)):.4f} V")
    
    # Plot
    fig, axes = plt.subplots(2, 1, figsize=(12, 7))
    
    # Top: full signal
    axes[0].plot(full_time, full_signal, linewidth=0.3, color='#028090')
    axes[0].set_xlabel("Time (s)")
    axes[0].set_ylabel("Voltage (V)")
    axes[0].set_title("Full Acquisition (all chunks combined)", fontweight='bold')
    axes[0].grid(True, alpha=0.3)
    
    # Bottom: zoomed in (first 50ms)
    mask = full_time < 0.05
    axes[1].plot(full_time[mask] * 1000, full_signal[mask],
                 linewidth=1, color='#E07C24')
    axes[1].set_xlabel("Time (ms)")
    axes[1].set_ylabel("Voltage (V)")
    axes[1].set_title("Zoomed View (first 50 ms)", fontweight='bold')
    axes[1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.show()

print("""
╔══════════════════════════════════════════════════════════════╗
║  WHAT YOU LEARNED:                                           ║
║                                                              ║
║  1. threading.Thread() creates a new thread                  ║
║  2. queue.Queue() lets threads share data safely             ║
║  3. threading.Event() signals threads to stop                ║
║  4. The producer-consumer pattern prevents data loss         ║
║                                                              ║
║  In YOUR project (WP3), you will:                            ║
║  - Replace daq_reader() with real nidaqmx task.read()        ║
║  - Replace data_processor() with pyqtgraph live plotting     ║
║  - Add a 3rd thread for saving data to disk                  ║
╚══════════════════════════════════════════════════════════════╝
""")
