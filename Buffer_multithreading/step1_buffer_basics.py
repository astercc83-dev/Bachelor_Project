"""
SCRIPT 1: What is a Buffer? Why does it Overflow?
===================================================
Before we write any code, let's understand the concept.

Run this: python step1_buffer_basics.py
"""
import time

print("=" * 60)
print("PART 1: What is a Buffer?")
print("=" * 60)
print("""
A BUFFER is temporary storage (like a bucket).

Your PXI card has a hardware buffer:
  - The card constantly digitizes analog signals
  - It stores samples in the buffer (a chunk of memory)
  - Your Python program reads from this buffer
  - After reading, the buffer space is freed for new data

Example with numbers:
  - Buffer size: 10,000 samples
  - Sample rate: 1,000,000 samples/sec (1 MS/s)
  - Time to fill buffer: 10,000 / 1,000,000 = 0.01 sec = 10 ms

  → Your program has only 10 ms to read the buffer
    before it fills up again!
""")

input("Press Enter to see a buffer simulation...\n")


# ===================================================================
# PART 2: Simple Buffer Simulation
# ===================================================================

print("=" * 60)
print("PART 2: Simple Buffer Simulation")
print("=" * 60)
print()

class SimpleBuffer:
    """
    Simulates a hardware buffer (like the one on your PXI card).
    """
    def __init__(self, max_size):
        self.max_size = max_size    # How many samples it can hold
        self.current_fill = 0        # How many samples are in it now
        self.total_lost = 0          # Samples lost due to overflow
        self.total_received = 0      # Total samples that arrived
    
    def add_samples(self, count):
        """Hardware adds new samples (this happens automatically)."""
        self.total_received += count
        space_available = self.max_size - self.current_fill
        
        if count <= space_available:
            # Enough space — all samples fit
            self.current_fill += count
            return 0  # no data lost
        else:
            # NOT enough space — some samples are LOST forever!
            lost = count - space_available
            self.current_fill = self.max_size  # buffer is now full
            self.total_lost += lost
            return lost  # return how many were lost
    
    def read_samples(self, count):
        """Your program reads samples (empties part of the buffer)."""
        actually_read = min(count, self.current_fill)
        self.current_fill -= actually_read
        return actually_read
    
    def get_fill_percentage(self):
        return (self.current_fill / self.max_size) * 100


# --- Demo: Buffer WITHOUT overflow ---
print("Demo 1: Buffer that gets emptied fast enough (NO overflow)")
print("-" * 60)

buf = SimpleBuffer(max_size=1000)

for step in range(5):
    # Hardware adds 200 samples
    lost = buf.add_samples(200)
    print(f"  Step {step+1}: +200 samples → "
          f"Buffer: {buf.current_fill}/{buf.max_size} "
          f"({buf.get_fill_percentage():.0f}%) "
          f"Lost: {lost}")
    
    # Program reads 200 samples (keeps up!)
    read = buf.read_samples(200)
    print(f"          Read {read} samples → "
          f"Buffer: {buf.current_fill}/{buf.max_size} "
          f"({buf.get_fill_percentage():.0f}%)")
    print()

print(f"  Total lost: {buf.total_lost} samples ✓ No data loss!\n")

input("Press Enter to see what happens when we're too slow...\n")


# --- Demo: Buffer WITH overflow ---
print("Demo 2: Buffer that gets emptied TOO SLOWLY (OVERFLOW!)")
print("-" * 60)

buf2 = SimpleBuffer(max_size=1000)

for step in range(8):
    # Hardware adds 200 samples every step
    lost = buf2.add_samples(200)
    
    status = ""
    if lost > 0:
        status = f" ⚠️  OVERFLOW! Lost {lost} samples!"
    
    bar_filled = int(buf2.get_fill_percentage() / 5)
    bar = "█" * bar_filled + "░" * (20 - bar_filled)
    
    print(f"  Step {step+1}: +200 → [{bar}] "
          f"{buf2.current_fill}/{buf2.max_size}{status}")
    
    # Program only reads 100 samples (too slow! reads half of what comes in)
    if step % 2 == 0:  # and sometimes doesn't read at all
        read = buf2.read_samples(100)
        print(f"          Read {read} → [{('█' * int(buf2.get_fill_percentage()/5)).ljust(20, '░')}] "
              f"{buf2.current_fill}/{buf2.max_size}")
    else:
        print(f"          (busy plotting, no time to read!)")
    print()

print(f"  Total received: {buf2.total_received}")
print(f"  Total LOST: {buf2.total_lost} samples ✗ DATA LOSS!")
print(f"  Loss rate: {buf2.total_lost/buf2.total_received*100:.1f}%")

print("""
╔══════════════════════════════════════════════════════════════╗
║  KEY TAKEAWAY:                                               ║
║                                                              ║
║  Buffer overflow happens when your program is SLOWER          ║
║  than the hardware.                                          ║
║                                                              ║
║  The hardware doesn't wait — it keeps sending data.          ║
║  If your buffer is full, new data OVERWRITES old data.       ║
║  That data is gone forever.                                  ║
║                                                              ║
║  This is exactly what happens on your PXI system when        ║
║  Python is busy plotting and can't read fast enough.         ║
║                                                              ║
║  Next script → we simulate this with real timing!            ║
╚══════════════════════════════════════════════════════════════╝
""")
