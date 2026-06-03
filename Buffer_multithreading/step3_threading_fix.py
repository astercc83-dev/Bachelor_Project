"""
SCRIPT 3: Fixing Buffer Overflow with Multithreading
======================================================
The problem: doing read + process + plot in one thread is too slow.
The solution: separate them into different threads!

Run this: python step3_threading_fix.py
"""
import numpy as np
import threading
import queue
import time
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


print("=" * 60)
print("THE SOLUTION: Multithreading")
print("=" * 60)
print("""
Instead of doing everything in one thread:

  SINGLE THREAD (slow, causes overflow):
  ┌─────────────────────────────────────────────┐
  │ Read → Process → Plot → Read → Process → ...│
  │ (everything waits for everything else)       │
  └─────────────────────────────────────────────┘

We split into separate threads:

  THREAD 1 — Reader (fast, never stops):
  ┌─────────────────────────────────────┐
  │ Read → Read → Read → Read → ...    │  ← just reads, puts in queue
  └──────────────┬──────────────────────┘
                 │ Queue (thread-safe buffer)
  ┌──────────────▼──────────────────────┐
  │ Process → Plot → Process → Plot    │  ← takes from queue, processes
  └─────────────────────────────────────┘
  THREAD 2 — Processor (can be slower)

Thread 1 NEVER waits for Thread 2.
Thread 1 just keeps reading and putting data in the queue.
Thread 2 takes data from the queue whenever it's ready.
""")

input("Press Enter to run the threaded simulation...\n")


# ===================================================================
# Load the simulated data
# ===================================================================

all_data = np.load("simulated_pxi_data.npy")
sample_rate = 100000
total_samples = len(all_data)

print(f"Loaded {total_samples:,} samples at {sample_rate/1000:.0f} kHz")
print()


# ===================================================================
# METHOD 1: Single Thread (the problem — for comparison)
# ===================================================================

print("=" * 60)
print("METHOD 1: Single Thread (baseline — expect overflow)")
print("=" * 60)

def run_single_thread(data, chunk_size=5000):
    """Process everything in one thread — the slow way."""
    buffer_max = 10000
    buffer_fill = 0
    total_lost = 0
    results = []
    pointer = 0
    
    start_time = time.time()
    
    while pointer < len(data):
        # New data arrives
        new_samples = min(chunk_size, len(data) - pointer)
        space_left = buffer_max - buffer_fill
        
        if new_samples > space_left:
            total_lost += (new_samples - space_left)
            buffer_fill = buffer_max
        else:
            buffer_fill += new_samples
        
        # Read chunk
        chunk = data[pointer:pointer + new_samples]
        pointer += new_samples
        
        # Process (takes time)
        rms = np.sqrt(np.mean(chunk**2))
        results.append(rms)
        
        # Simulate slow plotting
        time.sleep(0.015)
        
        buffer_fill = max(0, buffer_fill - new_samples)
    
    elapsed = time.time() - start_time
    return total_lost, elapsed, results

lost_single, time_single, results_single = run_single_thread(all_data)
print(f"  Time: {time_single:.2f} seconds")
print(f"  Samples lost: {lost_single:,}")
print(f"  Data loss: {lost_single/total_samples*100:.2f}%")
print()

input("Press Enter to run the THREADED version...\n")


# ===================================================================
# METHOD 2: Multi-Threaded (the solution)
# ===================================================================

print("=" * 60)
print("METHOD 2: Multi-Threaded (the fix)")
print("=" * 60)

def run_multi_threaded(data, chunk_size=5000):
    """
    Two threads working together:
    - Reader thread:    reads data as fast as possible → puts in queue
    - Processor thread: takes from queue → processes (can be slower)
    """
    data_queue = queue.Queue(maxsize=50)  # Queue holds up to 50 chunks
    stop_event = threading.Event()
    
    # Shared statistics
    stats = {
        "total_lost": 0,
        "chunks_read": 0,
        "chunks_processed": 0,
        "results": [],
        "queue_sizes": [],
    }
    
    def reader_thread():
        """
        THREAD 1: Reads data as fast as possible.
        Only job: read from hardware, put in queue.
        Does NOT process, does NOT plot. Just reads.
        """
        pointer = 0
        buffer_max = 10000
        buffer_fill = 0
        
        while pointer < len(data):
            new_samples = min(chunk_size, len(data) - pointer)
            chunk = data[pointer:pointer + new_samples]
            pointer += new_samples
            
            # Put data in queue
            try:
                data_queue.put(chunk, timeout=0.5)
                stats["chunks_read"] += 1
                stats["queue_sizes"].append(data_queue.qsize())
            except queue.Full:
                # Queue is full — processor is too slow
                stats["total_lost"] += new_samples
            
            # Small sleep to simulate hardware read timing
            time.sleep(chunk_size / sample_rate)
        
        stop_event.set()  # Signal: no more data coming
    
    def processor_thread():
        """
        THREAD 2: Processes data from the queue.
        Can be slower — the queue absorbs the speed difference.
        """
        while not stop_event.is_set() or not data_queue.empty():
            try:
                chunk = data_queue.get(timeout=0.1)
                
                # Process (takes time — but that's okay now!)
                rms = np.sqrt(np.mean(chunk**2))
                stats["results"].append(rms)
                stats["chunks_processed"] += 1
                
                # Simulate slow plotting
                time.sleep(0.015)
                
            except queue.Empty:
                continue
    
    # Create and start both threads
    start_time = time.time()
    
    t1 = threading.Thread(target=reader_thread, name="Reader")
    t2 = threading.Thread(target=processor_thread, name="Processor")
    
    t1.start()
    t2.start()
    
    # Wait for both to finish
    t1.join()
    t2.join()
    
    elapsed = time.time() - start_time
    return stats["total_lost"], elapsed, stats["results"], stats["queue_sizes"]

lost_threaded, time_threaded, results_threaded, queue_sizes = run_multi_threaded(all_data)
print(f"  Time: {time_threaded:.2f} seconds")
print(f"  Samples lost: {lost_threaded:,}")
print(f"  Data loss: {lost_threaded/total_samples*100:.2f}%")
print()


# ===================================================================
# COMPARISON
# ===================================================================

print("=" * 60)
print("COMPARISON: Single Thread vs Multi-Threaded")
print("=" * 60)

print(f"""
  ┌────────────────────┬──────────────┬──────────────┐
  │                    │ Single Thread│ Multi-Thread  │
  ├────────────────────┼──────────────┼──────────────┤
  │ Time               │ {time_single:>9.2f} s  │ {time_threaded:>9.2f} s  │
  │ Samples lost       │ {lost_single:>9,}    │ {lost_threaded:>9,}    │
  │ Data loss %        │ {lost_single/total_samples*100:>9.2f}%   │ {lost_threaded/total_samples*100:>9.2f}%   │
  └────────────────────┴──────────────┴──────────────┘
""")

# Plot the queue size over time
if queue_sizes:
    fig, axes = plt.subplots(2, 1, figsize=(12, 6))
    
    # Top: Queue fill level over time
    axes[0].plot(queue_sizes, linewidth=0.8, color='#028090')
    axes[0].set_ylabel("Queue size (chunks)")
    axes[0].set_title("Queue Level Over Time (threading)")
    axes[0].grid(True, alpha=0.3)
    axes[0].axhline(y=50, color='red', linestyle='--', label='Queue MAX (50)')
    axes[0].legend()
    
    # Bottom: RMS values from both methods
    axes[1].plot(results_single[:100], label='Single thread', alpha=0.7, color='#E07C24')
    axes[1].plot(results_threaded[:100], label='Multi-threaded', alpha=0.7, color='#028090')
    axes[1].set_ylabel("RMS Voltage (V)")
    axes[1].set_xlabel("Chunk number")
    axes[1].set_title("RMS Values — First 100 Chunks")
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig("plot_threading_comparison.png", dpi=150)
    plt.close()
    print("Saved: plot_threading_comparison.png")

print("""
╔══════════════════════════════════════════════════════════════╗
║  WHY THREADING WORKS:                                        ║
║                                                              ║
║  The Reader thread is FAST — it only reads data and puts     ║
║  it in the queue. It never waits for processing or plotting. ║
║                                                              ║
║  The Queue acts as a shock absorber between the fast          ║
║  reader and the slower processor.                            ║
║                                                              ║
║  The Processor can take its time — plotting, calculating,    ║
║  saving — because the queue holds the data safely.           ║
║                                                              ║
║  → Run step4_threading_vs_multiprocessing.py to see          ║
║    which approach is better for your PXI project!            ║
╚══════════════════════════════════════════════════════════════╝
""")
